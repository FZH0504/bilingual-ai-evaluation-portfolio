"""Validate paired translation-study input without modifying the source workbook."""
from __future__ import annotations

import sys
from typing import Any

import pandas as pd

from common import OUTPUTS, clean_key, load_config, project_path, read_excel, setup_logging

REQUIRED = ["text_id", "condition", "model_name", "model_version_or_access_label",
            "access_date", "prompt_id", "prompt_text", "source_zh", "reference_en",
            "output_en", "generation_id", "notes"]
TEXT_REQUIRED = ["source_zh", "reference_en", "output_en"]


def add_issue(issues: list[dict[str, Any]], severity: str, code: str,
              message: str, row: int | None = None, text_id: str = "") -> None:
    """Append one machine-readable validation issue."""
    issues.append({"severity": severity, "code": code, "excel_row": row,
                   "text_id": text_id, "message": message})


def validate(frame: pd.DataFrame, config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return a minimally trimmed copy and a detailed validation report."""
    issues: list[dict[str, Any]] = []
    missing = [column for column in REQUIRED if column not in frame.columns]
    if missing:
        add_issue(issues, "ERROR", "MISSING_COLUMNS", f"Missing required columns: {missing}")
        return frame, pd.DataFrame(issues)
    clean = frame.copy()
    for column in REQUIRED:
        clean[column] = clean[column].map(lambda value: value.strip() if isinstance(value, str) else value)
    clean["generation_id"] = clean["generation_id"].where(clean["generation_id"].notna(), "run_1")
    for index, row in clean.iterrows():
        excel_row = int(index) + 2
        text_id = clean_key(row["text_id"])
        for column in ["text_id", "condition", *TEXT_REQUIRED]:
            if clean_key(row[column]) == "":
                add_issue(issues, "ERROR", "EMPTY_REQUIRED", f"{column} is empty", excel_row, text_id)
        words = str(row["output_en"]).split() if not pd.isna(row["output_en"]) else []
        if 0 < len(words) < int(config.get("short_output_word_threshold", 20)):
            add_issue(issues, "WARNING", "SHORT_OUTPUT", f"output_en has only {len(words)} whitespace-delimited words", excel_row, text_id)
    key = ["text_id", "condition", "generation_id"]
    duplicates = clean.duplicated(key, keep=False)
    for index in clean.index[duplicates]:
        add_issue(issues, "ERROR", "DUPLICATE_KEY", f"Duplicate key {tuple(clean.loc[index, key])}", int(index) + 2, clean_key(clean.at[index, "text_id"]))
    conditions = [str(config.get("condition_a", "")), str(config.get("condition_b", ""))]
    for text_id, group in clean.groupby("text_id", dropna=False):
        text_key = clean_key(text_id)
        present = set(group["condition"].map(clean_key))
        absent = [condition for condition in conditions if condition and condition not in present]
        if absent:
            add_issue(issues, "ERROR", "INCOMPLETE_PAIR", f"Missing configured conditions: {absent}", None, text_key)
        for column in ["source_zh", "reference_en"]:
            values = group[column].dropna().map(str).unique()
            if len(values) > 1:
                add_issue(issues, "ERROR", "PAIR_TEXT_MISMATCH", f"{column} differs across conditions", None, text_key)
        prompt_map = group.groupby("condition")["prompt_id"].apply(lambda s: set(s.dropna().map(str)))
        if any(len(values) > 1 for values in prompt_map):
            add_issue(issues, "WARNING", "PROMPT_ID_INCONSISTENT", "A condition has multiple prompt_id values", None, text_key)
        for condition, values in prompt_map.items():
            if len(values) == 1 and str(condition) not in next(iter(values)):
                add_issue(issues, "WARNING", "PROMPT_ID_REVIEW", f"prompt_id may not match condition {condition!r}; review manually", None, text_key)
    report = pd.DataFrame(issues, columns=["severity", "code", "excel_row", "text_id", "message"])
    return clean, report


def main() -> int:
    """Run validation and stop downstream work when pairing is unsafe."""
    logger = setup_logging("validation", "validation.log")
    config = load_config()
    try:
        frame = read_excel(project_path(config["input_file"]), str(config.get("input_sheet", "data")))
        clean, report = validate(frame, config)
        OUTPUTS.mkdir(parents=True, exist_ok=True)
        clean.to_excel(OUTPUTS / "validated_data.xlsx", index=False, sheet_name="data")
        report.to_excel(OUTPUTS / "validation_report.xlsx", index=False, sheet_name="issues")
        errors = int((report.get("severity", pd.Series(dtype=str)) == "ERROR").sum())
        warnings = int((report.get("severity", pd.Series(dtype=str)) == "WARNING").sum())
        logger.info("Validation completed: %d error(s), %d warning(s)", errors, warnings)
        if errors:
            logger.error("Serious validation errors found. Inspect outputs/validation_report.xlsx; do not run scoring yet.")
            return 2
        return 0
    except Exception as exc:
        logger.exception("Validation failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
