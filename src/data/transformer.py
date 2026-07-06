from __future__ import annotations

from datetime import UTC

import pandas as pd

from src.utils.log_utils import get_logger

logger = get_logger(__name__)


def rename_columns(
    df: pd.DataFrame,
    mapping: dict[str, str] | None = None,
) -> pd.DataFrame:
    if mapping is None:
        mapping = {
            "case_id": "case:concept:name",
            "activity": "concept:name",
            "timestamp": "time:timestamp",
        }
    rename_map = {k: v for k, v in mapping.items() if k in df.columns}
    df = df.rename(columns=rename_map)
    return df


def cast_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "case:concept:name" in df.columns:
        df["case:concept:name"] = df["case:concept:name"].astype("string")
    if "concept:name" in df.columns:
        df["concept:name"] = df["concept:name"].astype("category")
    return df


def convert_timestamps_to_utc(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "time:timestamp" not in df.columns:
        return df
    if not pd.api.types.is_datetime64_any_dtype(df["time:timestamp"]):
        df["time:timestamp"] = pd.to_datetime(df["time:timestamp"], errors="coerce")
    ts = df["time:timestamp"]
    if ts.dt.tz is None:
        df["time:timestamp"] = ts.dt.tz_localize(UTC).dt.tz_localize(None)
    else:
        df["time:timestamp"] = ts.dt.tz_convert(UTC).dt.tz_localize(None)
    return df


def transform_event_log(
    df: pd.DataFrame,
    column_mapping: dict[str, str] | None = None,
) -> pd.DataFrame:
    df = rename_columns(df, column_mapping)
    df = cast_dtypes(df)
    df = convert_timestamps_to_utc(df)
    df = df.sort_values(["case:concept:name", "time:timestamp"]).reset_index(drop=True)
    logger.info("Transform complete: %d rows, %d cases", len(df), df["case:concept:name"].nunique())
    return df
