from __future__ import annotations

import pandas as pd

from src.utils.log_utils import get_logger

logger = get_logger(__name__)

REQUIRED_COLUMNS = {"case:concept:name", "concept:name", "time:timestamp"}


def validate_columns(df: pd.DataFrame) -> list[str]:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        msg = f"Missing required columns: {missing}"
        logger.error(msg)
        raise ValueError(msg)
    logger.info("All required columns present")
    return list(REQUIRED_COLUMNS)


def validate_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.copy()
    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"], errors="coerce")
    null_ts = df["time:timestamp"].isna().sum()
    if null_ts > 0:
        logger.warning("Dropping %d rows with unparseable timestamps", null_ts)
        df = df.dropna(subset=["time:timestamp"])
    logger.info("Validated timestamps: %d rows retained (%.1f%%)", len(df), 100 * len(df) / before)
    return df


def validate_no_null_cases(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.copy()
    df = df.dropna(subset=["case:concept:name"])
    dropped = before - len(df)
    if dropped > 0:
        logger.warning("Dropped %d rows with null case IDs", dropped)
    return df


def validate_sort_order(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["case:concept:name", "time:timestamp"]).reset_index(drop=True)
    logger.info("Sorted by case and timestamp")
    return df


def validate_no_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=["case:concept:name", "concept:name", "time:timestamp"])
    dropped = before - len(df)
    if dropped > 0:
        logger.warning("Removed %d duplicate rows", dropped)
    return df


def validate_event_log(df: pd.DataFrame) -> pd.DataFrame:
    validate_columns(df)
    df = validate_timestamps(df)
    df = validate_no_null_cases(df)
    df = validate_sort_order(df)
    df = validate_no_duplicates(df)
    return df
