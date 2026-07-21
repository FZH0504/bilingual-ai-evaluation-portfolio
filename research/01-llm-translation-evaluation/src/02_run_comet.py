"""Score whole texts or manually aligned segments with official COMET."""
from __future__ import annotations

import importlib.metadata
import platform
import random
import sys
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from common import OUTPUTS, ROOT, load_config, project_path, read_excel, setup_logging


def environment(torch: Any, model_id: str) -> dict[str, Any]:
    """Collect auditable runtime metadata."""
    gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else ""
    try:
        comet_version = importlib.metadata.version("unbabel-comet")
    except importlib.metadata.PackageNotFoundError:
        comet_version = "unknown"
    return {"python_version": platform.python_version(), "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda or "", "gpu_name": gpu,
            "unbabel_comet_version": comet_version, "comet_model_id": model_id,
            "scoring_timestamp_utc": datetime.now(timezone.utc).isoformat()}


def usable_token_limit(model: Any) -> int:
    """Infer a conservative encoder token limit from the loaded checkpoint."""
    encoder_limit = getattr(getattr(model, "encoder", None), "max_positions", None)
    if callable(encoder_limit):
        encoder_limit = encoder_limit()
    if encoder_limit is not None:
        return int(encoder_limit)
    tokenizer = getattr(model, "tokenizer", None) or getattr(getattr(model, "encoder", None), "tokenizer", None)
    if tokenizer is None:
        raise RuntimeError("Loaded COMET model does not expose a tokenizer")
    tokenizer_limit = int(getattr(tokenizer, "model_max_length", 512))
    if tokenizer_limit > 100_000:
        tokenizer_limit = 512
    return tokenizer_limit


def token_length(model: Any, sample: dict[str, str]) -> int:
    """Measure the longest component; COMET encodes src/mt/ref separately."""
    tokenizer = getattr(model, "tokenizer", None) or getattr(getattr(model, "encoder", None), "tokenizer", None)
    if tokenizer is None:
        raise RuntimeError("Loaded COMET model does not expose a tokenizer")
    return max(len(tokenizer.encode(sample[key], add_special_tokens=True)) for key in ("src", "mt", "ref"))


def predict_with_fallback(model: Any, samples: list[dict[str, str]], config: dict[str, Any],
                          torch: Any, logger: Any) -> tuple[list[float], str, int]:
    """Predict with decreasing GPU batches and optional CPU fallback."""
    prefer = str(config.get("preferred_device", "auto")).lower()
    use_gpu = torch.cuda.is_available() and prefer != "cpu"
    batches = [int(config.get("initial_batch_size", 8)), *map(int, config.get("fallback_batch_sizes", [4, 2, 1]))]
    batches = list(dict.fromkeys(size for size in batches if size > 0))
    if use_gpu:
        for batch in batches:
            try:
                logger.info("COMET GPU attempt with batch_size=%d", batch)
                result = model.predict(samples, batch_size=batch, gpus=1, progress_bar=True)
                return [float(x) for x in result.scores], "cuda", batch
            except torch.cuda.OutOfMemoryError:
                logger.warning("CUDA out of memory at batch_size=%d", batch)
                torch.cuda.empty_cache()
            except RuntimeError as exc:
                if "out of memory" not in str(exc).lower():
                    raise
                logger.warning("CUDA OOM-like RuntimeError at batch_size=%d", batch)
                torch.cuda.empty_cache()
    if use_gpu and not bool(config.get("fallback_to_cpu", True)):
        raise RuntimeError("All GPU batch sizes failed and fallback_to_cpu=false")
    logger.warning("Using CPU; COMET scoring can be substantially slower.")
    batch = batches[-1]
    result = model.predict(samples, batch_size=batch, gpus=0, progress_bar=True)
    return [float(x) for x in result.scores], "cpu", batch


def load_units(frame: pd.DataFrame, input_path: Any, segment_sheet: str) -> tuple[pd.DataFrame, bool]:
    """Use aligned segments when a nonempty sheet exists, otherwise whole texts."""
    try:
        segments = pd.read_excel(input_path, sheet_name=segment_sheet)
        required = {"text_id", "condition", "segment_id", "source_segment", "reference_segment", "output_segment"}
        if not segments.empty and required.issubset(segments.columns):
            return segments, True
    except (ValueError, FileNotFoundError):
        pass
    whole = frame[["text_id", "condition", "source_zh", "reference_en", "output_en"]].copy()
    whole["segment_id"] = "whole_text"
    return whole.rename(columns={"source_zh": "source_segment", "reference_en": "reference_segment", "output_en": "output_segment"}), False


def main() -> int:
    """Load COMET, guard long texts, score, aggregate, and write audit metadata."""
    logger = setup_logging("comet", "comet.log")
    try:
        import torch
        from comet import download_model, load_from_checkpoint
        config = load_config()
        random.seed(int(config.get("random_seed", 0))); np.random.seed(int(config.get("random_seed", 0))); torch.manual_seed(int(config.get("random_seed", 0)))
        validated = read_excel(OUTPUTS / "validated_data.xlsx", "data")
        input_path = project_path(config["input_file"])
        units, segmented = load_units(validated, input_path, str(config.get("aligned_segments_sheet", "aligned_segments")))
        model_id = str(config["comet_model"])
        logger.info("Downloading/loading official COMET model %s", model_id)
        model = load_from_checkpoint(download_model(model_id))
        limit = usable_token_limit(model)
        samples, accepted_indices, reviews = [], [], []
        for index, row in units.iterrows():
            sample = {"src": str(row["source_segment"]), "mt": str(row["output_segment"]), "ref": str(row["reference_segment"])}
            length = token_length(model, sample)
            if length > limit:
                reviews.append({**row.to_dict(), "max_component_tokens": length, "reliable_limit": limit, "review_status": "needs_alignment"})
                logger.warning("Skipping text_id=%s condition=%s: %d tokens exceeds limit %d", row["text_id"], row["condition"], length, limit)
            else:
                samples.append(sample); accepted_indices.append(index)
        OUTPUTS.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(reviews).to_excel(OUTPUTS / "long_text_review.xlsx", index=False)
        if not samples:
            raise RuntimeError("No scorable records remain; inspect outputs/long_text_review.xlsx")
        scores, device, batch = predict_with_fallback(model, samples, config, torch, logger)
        scored = units.loc[accepted_indices].copy()
        scored["comet_score"] = scores
        scored["device"] = device; scored["batch_size"] = batch
        scored.to_excel(OUTPUTS / "comet_segment_scores.xlsx", index=False)
        grouped = scored.groupby(["text_id", "condition"], as_index=False).agg(comet_score=("comet_score", "mean"), number_of_segments=("segment_id", "count"))
        metadata = validated[["text_id", "condition", "model_name"]].drop_duplicates(["text_id", "condition"])
        text_scores = metadata.merge(grouped, on=["text_id", "condition"], how="left")
        text_scores["comet_model_id"] = model_id
        text_scores["aggregation_method"] = "arithmetic_mean" if segmented else "whole_text"
        text_scores["device"] = device; text_scores["batch_size"] = batch
        text_scores["scoring_status"] = np.where(text_scores["comet_score"].notna(), "scored", "needs_alignment")
        text_scores["error_message"] = np.where(text_scores["comet_score"].notna(), "", "Text/segment exceeded reliable token limit")
        text_scores.to_excel(OUTPUTS / "comet_text_scores.xlsx", index=False)
        pd.DataFrame([environment(torch, model_id)]).to_excel(OUTPUTS / "comet_environment.xlsx", index=False)
        logger.info("Scored %d units into %d text-level records; device=%s batch=%d", len(scored), len(text_scores), device, batch)
        return 0
    except Exception as exc:
        logger.exception("COMET scoring failed (no scores were invented): %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
