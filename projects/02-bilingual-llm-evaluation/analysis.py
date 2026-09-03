"""Analysis helpers for the cross-model and temporal bilingual studies.

Research data are intentionally absent. Metric logic is grouped in this paper
module instead of being presented as a separate project for each indicator.
"""
from __future__ import annotations

import importlib.metadata
import math
import platform
import re
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd
import textstat

STUDY_COLUMNS = [
    "text_id",
    "domain",
    "model",
    "prompt",
    "source_zh",
    "reference_en",
    "output_en",
]
SEGMENT_COLUMNS = [
    "text_id",
    "domain",
    "model",
    "prompt",
    "segment_id",
    "source_segment",
    "reference_segment",
    "output_segment",
]
WORD_PATTERN = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")
SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")


def validate_study_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate the fields and keys used in the model/domain/prompt study."""
    missing = [column for column in STUDY_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Study input is missing columns: {missing}")
    result = frame.copy()
    key = ["text_id", "model", "prompt"]
    if result.duplicated(key).any():
        raise ValueError(f"Duplicate study keys found: {key}")
    required_text = ["text_id", "domain", "model", "prompt", "source_zh", "reference_en", "output_en"]
    for column in required_text:
        if result[column].fillna("").astype(str).str.strip().eq("").any():
            raise ValueError(f"{column} cannot be blank")
    return result


def tokenize_words(text: str) -> list[str]:
    return [match.group(0).lower().replace("’", "'") for match in WORD_PATTERN.finditer(text)]


def sentence_count(text: str) -> int:
    if not text.strip():
        return 0
    parts = [part for part in SENTENCE_PATTERN.split(text.strip()) if part.strip()]
    return max(1, len(parts))


def calculate_text_metrics(text: str) -> dict[str, float]:
    """Calculate transparent surface/readability measures for English text."""
    tokens = tokenize_words(text)
    words = len(tokens)
    sentences = sentence_count(text)
    try:
        fre = float(textstat.flesch_reading_ease(text))
        fkgl = float(textstat.flesch_kincaid_grade(text))
    except (TypeError, ValueError, ZeroDivisionError):
        fre = fkgl = math.nan
    return {
        "word_count": float(words),
        "sentence_count": float(sentences),
        "average_sentence_length": words / sentences if sentences else math.nan,
        "type_token_ratio": len(set(tokens)) / words if words else math.nan,
        "flesch_reading_ease": fre,
        "flesch_kincaid_grade": fkgl,
    }


def evaluate_text_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Compute output/reference metrics and their signed differences."""
    validated = validate_study_frame(frame)
    rows: list[dict[str, object]] = []
    for _, row in validated.iterrows():
        output = calculate_text_metrics(str(row["output_en"]))
        reference = calculate_text_metrics(str(row["reference_en"]))
        record: dict[str, object] = {
            key: row[key] for key in ["text_id", "domain", "model", "prompt"]
        }
        for metric, value in output.items():
            record[f"{metric}_output"] = value
            record[f"{metric}_reference"] = reference[metric]
            record[f"{metric}_difference"] = value - reference[metric]
            record[f"{metric}_absolute_deviation"] = abs(value - reference[metric])
        rows.append(record)
    return pd.DataFrame(rows)


def validate_aligned_segments(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in SEGMENT_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Aligned-segment input is missing columns: {missing}")
    result = frame.copy()
    key = ["text_id", "model", "prompt", "segment_id"]
    if result.duplicated(key).any():
        raise ValueError(f"Duplicate aligned-segment keys found: {key}")
    for column in ["source_segment", "reference_segment", "output_segment"]:
        if result[column].fillna("").astype(str).str.strip().eq("").any():
            raise ValueError(f"{column} cannot be blank")
    return result


def aggregate_aligned_comet_segments(scored_segments: pd.DataFrame) -> pd.DataFrame:
    """Use an arithmetic mean over accepted, manually aligned segment scores."""
    required = ["text_id", "domain", "model", "prompt", "segment_id", "comet_score"]
    missing = [column for column in required if column not in scored_segments.columns]
    if missing:
        raise ValueError(f"Scored segments are missing columns: {missing}")
    frame = scored_segments.copy()
    frame["comet_score"] = pd.to_numeric(frame["comet_score"], errors="coerce")
    if frame["comet_score"].isna().any():
        raise ValueError("Every accepted segment must have a numeric COMET score")
    grouped = frame.groupby(["text_id", "domain", "model", "prompt"], as_index=False).agg(
        comet_score=("comet_score", "mean"),
        number_of_segments=("segment_id", "nunique"),
    )
    grouped["aggregation_method"] = "arithmetic_mean_of_manually_aligned_segments"
    return grouped


def _comet_tokenizer(model: Any) -> Any:
    tokenizer = getattr(model, "tokenizer", None) or getattr(getattr(model, "encoder", None), "tokenizer", None)
    if tokenizer is None:
        raise RuntimeError("Loaded COMET model does not expose a tokenizer")
    return tokenizer


def comet_token_limit(model: Any) -> int:
    limit = getattr(getattr(model, "encoder", None), "max_positions", None)
    if callable(limit):
        limit = limit()
    if limit is not None:
        return int(limit)
    tokenizer_limit = int(getattr(_comet_tokenizer(model), "model_max_length", 512))
    return 512 if tokenizer_limit > 100_000 else tokenizer_limit


def score_comet_units(
    aligned_segments: pd.DataFrame,
    model_id: str = "Unbabel/wmt22-comet-da",
    batch_size: int = 4,
    gpus: int = 0,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    """Score pre-aligned units and return scores, over-limit review rows, metadata.

    The function deliberately does not split source/output/reference text
    independently. Records over the model limit are returned for manual
    alignment review.
    """
    from comet import download_model, load_from_checkpoint
    import torch

    frame = validate_aligned_segments(aligned_segments)
    model = load_from_checkpoint(download_model(model_id))
    tokenizer = _comet_tokenizer(model)
    limit = comet_token_limit(model)
    accepted: list[int] = []
    samples: list[dict[str, str]] = []
    review_rows: list[dict[str, object]] = []
    for index, row in frame.iterrows():
        sample = {
            "src": str(row["source_segment"]),
            "mt": str(row["output_segment"]),
            "ref": str(row["reference_segment"]),
        }
        longest = max(len(tokenizer.encode(value, add_special_tokens=True)) for value in sample.values())
        if longest > limit:
            review_rows.append({**row.to_dict(), "max_component_tokens": longest, "token_limit": limit})
            continue
        accepted.append(index)
        samples.append(sample)
    if not samples:
        raise RuntimeError("No aligned segments fit within the COMET token limit")
    prediction = model.predict(samples, batch_size=batch_size, gpus=gpus, progress_bar=True)
    scored = frame.loc[accepted].copy()
    scored["comet_score"] = [float(value) for value in prediction.scores]
    try:
        comet_version = importlib.metadata.version("unbabel-comet")
    except importlib.metadata.PackageNotFoundError:
        comet_version = "unknown"
    metadata = {
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "comet_version": comet_version,
        "comet_model_id": model_id,
        "batch_size": batch_size,
        "gpus": gpus,
        "scoring_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    return scored, pd.DataFrame(review_rows), metadata


def summarize_temporal_metrics(frame: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    """Create descriptive version/domain summaries; no inferential claim is made."""
    required = ["model_version", "domain", *metrics]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Temporal input is missing columns: {missing}")
    result = frame.copy()
    for metric in metrics:
        result[metric] = pd.to_numeric(result[metric], errors="coerce")
    summary = result.groupby(["model_version", "domain"], as_index=False)[metrics].mean()
    summary["interpretation_scope"] = "descriptive_snapshot_only"
    return summary
