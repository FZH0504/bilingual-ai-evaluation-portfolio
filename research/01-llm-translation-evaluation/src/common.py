"""Shared configuration, paths, logging, and Excel helpers."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
LOGS = ROOT / "logs"
DATA = ROOT / "data"


def load_config() -> dict[str, Any]:
    """Load config.yaml and resolve project-relative paths at call sites."""
    path = ROOT / "config.yaml"
    try:
        with path.open("r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise RuntimeError(f"Cannot read valid YAML from {path}: {exc}") from exc
    return config


def project_path(value: str | Path) -> Path:
    """Resolve a configured path relative to the project root."""
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def setup_logging(name: str, filename: str) -> logging.Logger:
    """Create console and UTF-8 file logging."""
    LOGS.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler = logging.FileHandler(LOGS / filename, encoding="utf-8")
    stream_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def read_excel(path: Path, sheet_name: str) -> pd.DataFrame:
    """Read Excel with a clear error for missing or corrupt workbooks."""
    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {path}")
    try:
        return pd.read_excel(path, sheet_name=sheet_name, dtype=object)
    except Exception as exc:
        raise RuntimeError(f"Cannot read workbook {path}, sheet {sheet_name!r}: {exc}") from exc


def clean_key(value: object) -> str:
    """Convert an Excel identifier to a stable trimmed string."""
    if pd.isna(value):
        return ""
    return str(value).strip()

