from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data import anonymizer, loader, transformer, validator
from src.utils.log_utils import get_logger

logger = get_logger(__name__)


def run_pipeline(
    path: Path,
    fmt: str | None = None,
    column_mapping: dict[str, str] | None = None,
    anonymize: bool = False,
    salt: str = "",
) -> pd.DataFrame:
    logger.info("Pipeline start: %s", path)
    df = loader.load_event_log(path, fmt)
    df = transformer.transform_event_log(df, column_mapping)
    df = validator.validate_event_log(df)
    if anonymize:
        df = anonymizer.anonymize_event_log(df, salt)
    logger.info("Pipeline complete: %d rows, %d cases", len(df), df["case:concept:name"].nunique())
    return df
