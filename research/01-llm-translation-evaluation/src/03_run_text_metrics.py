"""Compute transparent local metrics and import external official tool results."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import textstat

from common import OUTPUTS, ROOT, load_config, project_path, read_excel, setup_logging

EXTERNAL_REQUIRED = ["text_id", "condition", "tool_name", "tool_version_or_access_date",
                     "syntactic_simplicity", "word_concreteness", "referential_cohesion",
                     "deep_cohesion", "l2_readability"]


def ratio(left: set[str], right: set[str]) -> float:
    """Return overlap over the smaller nonempty set, or NaN when undefined."""
    denominator = min(len(left), len(right))
    return len(left & right) / denominator if denominator else np.nan


def incidence(text: str, phrases: list[str], words: int) -> float:
    """Count case-insensitive connective phrase matches per 1,000 words."""
    count = sum(len(re.findall(r"(?<!\w)" + re.escape(item) + r"(?!\w)", text, re.I)) for item in phrases)
    return count * 1000 / words if words else np.nan


def local_metrics(text: str, nlp: Any, connectives: dict[str, list[str]], embedder: Any = None) -> dict[str, float]:
    """Calculate reproducible operational measures for one English text."""
    doc = nlp(text)
    tokens = [token for token in doc if not token.is_space and not token.is_punct]
    word_tokens = [token for token in tokens if token.is_alpha]
    sentences = [sentence for sentence in doc.sents if sentence.text.strip()]
    words = len(word_tokens); sentence_count = len(sentences)
    content_sets, noun_sets = [], []
    for sentence in sentences:
        content_sets.append({t.lemma_.lower() for t in sentence if t.is_alpha and not t.is_stop and t.pos_ in {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}})
        noun_sets.append({t.lemma_.lower() for t in sentence if t.is_alpha and t.pos_ in {"NOUN", "PROPN"}})
    content_overlap = [ratio(a, b) for a, b in zip(content_sets, content_sets[1:])]
    noun_overlap = [ratio(a, b) for a, b in zip(noun_sets, noun_sets[1:])]
    result = {
        "flesch_reading_ease": float(textstat.flesch_reading_ease(text)),
        "fkgl": float(textstat.flesch_kincaid_grade(text)),
        "word_count": float(words), "sentence_count": float(sentence_count),
        "average_sentence_length": words / sentence_count if sentence_count else np.nan,
        "average_syllables_per_word": textstat.syllable_count(text) / words if words else np.nan,
        "type_token_ratio": len({t.text.lower() for t in word_tokens}) / words if words else np.nan,
        "adjacent_content_word_overlap": float(np.nanmean(content_overlap)) if content_overlap and not np.all(np.isnan(content_overlap)) else np.nan,
        "adjacent_noun_overlap": float(np.nanmean(noun_overlap)) if noun_overlap and not np.all(np.isnan(noun_overlap)) else np.nan,
    }
    for category, phrases in connectives.items():
        result[f"connective_{category}_incidence"] = incidence(text, phrases, words)
    result["connective_total_incidence"] = sum(result[f"connective_{c}_incidence"] for c in connectives)
    if embedder is not None and len(sentences) > 1:
        embeddings = embedder.encode([s.text for s in sentences], normalize_embeddings=True)
        result["semantic_cohesion"] = float(np.mean(np.sum(embeddings[:-1] * embeddings[1:], axis=1)))
    else:
        result["semantic_cohesion"] = np.nan
    return result


def import_external(path: Path, keys: pd.DataFrame, logger: Any) -> pd.DataFrame:
    """Validate and merge external metrics without replacing local proxies."""
    if not path.exists():
        logger.info("No external metrics workbook found; external fields remain NaN.")
        return keys.copy()
    try:
        external = pd.read_excel(path, sheet_name="external_metrics")
    except ValueError:
        external = pd.read_excel(path)
    missing = [column for column in EXTERNAL_REQUIRED if column not in external.columns]
    if missing:
        raise ValueError(f"External metrics missing columns: {missing}")
    if external.duplicated(["text_id", "condition"]).any():
        raise ValueError("external_metrics has duplicate text_id + condition keys")
    return keys.merge(external, on=["text_id", "condition"], how="left")


def main() -> int:
    """Run local output/reference metrics, deviations, and external import."""
    logger = setup_logging("text_metrics", "text_metrics.log")
    try:
        import spacy
        config = load_config()
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError as exc:
            raise RuntimeError("spaCy model missing. Run: python -m spacy download en_core_web_sm") from exc
        embedder = None
        if bool(config.get("compute_sentence_transformer_similarity", False)):
            try:
                from sentence_transformers import SentenceTransformer
                embedder = SentenceTransformer(str(config.get("sentence_transformer_model")))
            except ImportError:
                logger.warning("sentence-transformers is not installed; semantic cohesion is skipped.")
        with (ROOT / "connectives.json").open(encoding="utf-8") as handle:
            connectives = json.load(handle)
        frame = read_excel(OUTPUTS / "validated_data.xlsx", "data")
        rows = []
        for _, row in frame.iterrows():
            output = local_metrics(str(row["output_en"]), nlp, connectives, embedder)
            reference = local_metrics(str(row["reference_en"]), nlp, connectives, embedder)
            record: dict[str, Any] = {"text_id": row["text_id"], "condition": row["condition"]}
            for name, value in output.items(): record[f"{name}_output"] = value
            for name, value in reference.items(): record[f"{name}_reference"] = value
            for name in output:
                record[f"{name}_difference"] = output[name] - reference[name]
                record[f"{name}_absolute_deviation"] = abs(output[name] - reference[name])
            rows.append(record)
        local = pd.DataFrame(rows); local["metric_source"] = "local"
        external = import_external(project_path(config["external_metrics_file"]), local[["text_id", "condition"]], logger)
        external_columns = [c for c in EXTERNAL_REQUIRED if c not in {"text_id", "condition"}]
        combined = local.merge(external[["text_id", "condition", *external_columns]], on=["text_id", "condition"], how="left")
        for name in ["syntactic_simplicity", "word_concreteness", "referential_cohesion", "deep_cohesion", "l2_readability"]:
            reference_column = f"{name}_reference"
            if reference_column in external.columns:
                reference_values = external[["text_id", "condition", reference_column]]
                combined = combined.merge(reference_values, on=["text_id", "condition"], how="left")
                combined[f"{name}_difference"] = combined[name] - combined[reference_column]
                combined[f"{name}_absolute_deviation"] = combined[f"{name}_difference"].abs()
        combined["external_metric_source"] = np.where(combined["tool_name"].notna(), "external", np.nan)
        OUTPUTS.mkdir(parents=True, exist_ok=True)
        combined.to_excel(OUTPUTS / "text_metrics.xlsx", index=False)
        logger.info("Computed transparent local metrics for %d records", len(combined))
        return 0
    except Exception as exc:
        logger.exception("Text metrics failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
