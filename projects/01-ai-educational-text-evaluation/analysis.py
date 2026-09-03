"""Project-specific analysis for the educational-text adaptation study.

The module groups readability, official Lexile import, content-preservation
validation, and repeated-output stability in one place. It contains no study
texts or saved research data.
"""
from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from collections.abc import Sequence
from itertools import combinations
from pathlib import Path

import pandas as pd
import textstat

WORD_PATTERN = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")
OUTPUT_PATTERN = re.compile(
    r"^(?P<source>.+?)_(?P<system>.+?)_Run(?P<run>\d+)_output$",
    flags=re.IGNORECASE,
)
LEXILE_PATTERN = re.compile(r"^\s*(\d{1,4})\s*L?\s*$", flags=re.IGNORECASE)
DEFAULT_MATTR_WINDOW = 50

CONTENT_COLUMNS = [
    "source_id",
    "output_id",
    "content_point_id",
    "content_point_definition",
    "score",
    "evidence_exact_excerpt",
    "evidence_location",
    "brief_reason",
    "uncertain",
    "confidence",
]


def tokenize_words(text: str) -> list[str]:
    """Return normalized English word tokens."""
    return [match.group(0).lower().replace("’", "'") for match in WORD_PATTERN.finditer(text)]


def parse_output_filename(path: str | Path) -> dict[str, object]:
    """Parse the study convention ``Source_System_RunN_output.txt``."""
    file_path = Path(path)
    match = OUTPUT_PATTERN.match(file_path.stem)
    source = system = ""
    run: int | None = None
    if match:
        source = match.group("source")
        system = match.group("system")
        run = int(match.group("run"))
    chapter_match = re.search(r"(\d+)$", source)
    return {
        "output_id": file_path.name,
        "source": source,
        "chapter": int(chapter_match.group(1)) if chapter_match else None,
        "system": system,
        "run": run,
    }


def calculate_mattr(tokens: Sequence[str], window: int = DEFAULT_MATTR_WINDOW) -> tuple[float, bool]:
    """Return MATTR and whether a full window was available."""
    if window < 2:
        raise ValueError("MATTR window must be at least 2 tokens")
    if not tokens:
        return math.nan, False
    if len(tokens) < window:
        return len(set(tokens)) / len(tokens), False
    values = [
        len(set(tokens[start : start + window])) / window
        for start in range(len(tokens) - window + 1)
    ]
    return sum(values) / len(values), True


def _safe_metric(function: object, text: str) -> float:
    try:
        return float(function(text))  # type: ignore[operator]
    except (TypeError, ValueError, ZeroDivisionError):
        return math.nan


def calculate_text_metrics(text: str, mattr_window: int = DEFAULT_MATTR_WINDOW) -> dict[str, object]:
    """Calculate transparent local measures used in the study.

    Lexile is deliberately absent because it must be imported from an external
    official result rather than estimated here.
    """
    tokens = tokenize_words(text)
    word_count = len(tokens)
    type_count = len(set(tokens))
    sentence_count = int(textstat.sentence_count(text)) if text.strip() else 0
    mattr, full_window = calculate_mattr(tokens, mattr_window)
    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "mean_sentence_length": word_count / sentence_count if sentence_count else math.nan,
        "flesch_kincaid_grade": _safe_metric(textstat.flesch_kincaid_grade, text),
        "dale_chall_readability_score": _safe_metric(textstat.dale_chall_readability_score, text),
        "type_count": type_count,
        "ttr": type_count / word_count if word_count else math.nan,
        "mattr": mattr,
        "mattr_window": mattr_window,
        "mattr_full_window": full_window,
    }


def parse_lexile(value: object) -> float:
    """Parse an externally supplied value such as ``840`` or ``840L``."""
    if pd.isna(value):
        return math.nan
    match = LEXILE_PATTERN.match(str(value))
    if not match:
        raise ValueError(f"Invalid externally supplied Lexile value: {value!r}")
    return float(match.group(1))


def load_official_lexile_results(path: str | Path) -> pd.DataFrame:
    """Load official results without estimating or reverse-engineering Lexile."""
    source = Path(path)
    frame = pd.read_excel(source) if source.suffix.lower() in {".xlsx", ".xls"} else pd.read_csv(source)
    missing = {"output_id", "lexile"} - set(frame.columns)
    if missing:
        raise ValueError(f"Lexile file is missing columns: {sorted(missing)}")
    if frame["output_id"].duplicated().any():
        raise ValueError("Lexile file contains duplicate output_id values")
    result = frame[["output_id", "lexile"]].copy()
    result["lexile"] = result["lexile"].map(parse_lexile)
    result["lexile_source"] = "externally supplied official result"
    return result


def merge_official_lexile_results(metrics: pd.DataFrame, lexile: pd.DataFrame) -> pd.DataFrame:
    if metrics["output_id"].duplicated().any():
        raise ValueError("Metric table contains duplicate output_id values")
    return metrics.merge(lexile, on="output_id", how="left", validate="one_to_one")


def _parse_yes_no(value: object) -> bool:
    normalized = str(value).strip().lower()
    if normalized in {"yes", "true", "1"}:
        return True
    if normalized in {"no", "false", "0"}:
        return False
    raise ValueError(f"uncertain must be yes/no or true/false, received {value!r}")


def validate_content_judgments(frame: pd.DataFrame) -> pd.DataFrame:
    """Require binary coding, positive evidence, and complete point coverage."""
    missing = [column for column in CONTENT_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Content-preservation input is missing columns: {missing}")
    result = frame.copy()
    key = ["source_id", "output_id", "content_point_id"]
    if result.duplicated(key).any():
        raise ValueError("Duplicate content-preservation coding records found")
    result["score"] = pd.to_numeric(result["score"], errors="coerce")
    if result["score"].isna().any() or not result["score"].isin([0, 1]).all():
        raise ValueError("Every content-preservation score must be 0 or 1")
    result["score"] = result["score"].astype(int)
    result["uncertain"] = result["uncertain"].map(_parse_yes_no)
    result["confidence"] = result["confidence"].astype(str).str.strip().str.lower()
    if not result["confidence"].isin({"high", "medium", "low"}).all():
        raise ValueError("confidence must be high, medium, or low")
    evidence = result["evidence_exact_excerpt"].fillna("").astype(str).str.strip()
    if (result["score"].eq(1) & evidence.eq("")).any():
        raise ValueError("A preserved score requires an exact output excerpt")
    expected = {
        source: set(group["content_point_id"])
        for source, group in result.groupby("source_id", sort=False)
    }
    for (source, output), group in result.groupby(["source_id", "output_id"], sort=False):
        missing_points = expected[source] - set(group["content_point_id"])
        if missing_points:
            raise ValueError(f"Incomplete content-point coverage for {output}: {sorted(missing_points)}")
    return result


def summarize_content_preservation(frame: pd.DataFrame) -> pd.DataFrame:
    """Return one auditable content-preservation record per output."""
    validated = validate_content_judgments(frame)
    summary = validated.groupby(["source_id", "output_id"], as_index=False).agg(
        content_points_total=("content_point_id", "nunique"),
        content_points_preserved=("score", "sum"),
        uncertain_count=("uncertain", "sum"),
        low_confidence_count=("confidence", lambda values: int((values == "low").sum())),
    )
    summary["content_preservation_rate"] = (
        summary["content_points_preserved"] / summary["content_points_total"] * 100
    )
    return summary


def normalize_for_hash(text: str) -> str:
    return " ".join(tokenize_words(text))


def normalized_sha256(text: str) -> str:
    return hashlib.sha256(normalize_for_hash(text).encode("utf-8")).hexdigest()


def word_frequency_cosine(left: list[str], right: list[str]) -> float:
    left_counts, right_counts = Counter(left), Counter(right)
    vocabulary = set(left_counts) | set(right_counts)
    if not vocabulary:
        return math.nan
    numerator = sum(left_counts[word] * right_counts[word] for word in vocabulary)
    left_norm = math.sqrt(sum(value * value for value in left_counts.values()))
    right_norm = math.sqrt(sum(value * value for value in right_counts.values()))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else math.nan


def ngram_overlap(left: list[str], right: list[str], size: int) -> tuple[float, float]:
    if size < 1:
        raise ValueError("n-gram size must be positive")
    left_set = {tuple(left[i : i + size]) for i in range(len(left) - size + 1)}
    right_set = {tuple(right[i : i + size]) for i in range(len(right) - size + 1)}
    union = left_set | right_set
    smaller = min(len(left_set), len(right_set))
    return (
        len(left_set & right_set) / len(union) if union else math.nan,
        len(left_set & right_set) / smaller if smaller else math.nan,
    )


def classify_pair(exact: bool, cosine: float, containment_5: float, containment_10: float) -> str:
    if exact:
        return "EXACT_DUPLICATE"
    if cosine >= 0.985 and containment_5 >= 0.90:
        return "NEAR_DUPLICATE"
    if cosine >= 0.95 or containment_10 >= 0.75:
        return "STRONG_OVERLAP_REVIEW"
    return "DISTINCT"


def compare_output_texts(records: list[dict[str, str]]) -> pd.DataFrame:
    """Compare in-memory outputs; records require output_id, source_id, and text."""
    prepared = []
    for record in records:
        tokens = tokenize_words(record["text"])
        prepared.append({**record, "tokens": tokens, "hash": normalized_sha256(record["text"])})
    rows = []
    for left, right in combinations(prepared, 2):
        if left["source_id"] != right["source_id"]:
            continue
        cosine = word_frequency_cosine(left["tokens"], right["tokens"])
        _, containment_5 = ngram_overlap(left["tokens"], right["tokens"], 5)
        _, containment_10 = ngram_overlap(left["tokens"], right["tokens"], 10)
        exact = left["hash"] == right["hash"]
        rows.append(
            {
                "output_id_a": left["output_id"],
                "output_id_b": right["output_id"],
                "exact_normalized_match": exact,
                "word_frequency_cosine": cosine,
                "fivegram_containment": containment_5,
                "tengram_containment": containment_10,
                "review_classification": classify_pair(exact, cosine, containment_5, containment_10),
            }
        )
    return pd.DataFrame(rows)
