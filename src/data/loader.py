from __future__ import annotations

from pathlib import Path

import pandas as pd
import pm4py

from src.utils.io_utils import validate_input_path
from src.utils.log_utils import get_logger

logger = get_logger(__name__)


def load_csv(path: Path, sep: str = ",") -> pd.DataFrame:
    validate_input_path(path)
    logger.info("Loading CSV from %s", path)
    df = pd.read_csv(path, sep=sep)
    logger.info("Loaded %d rows, %d columns", len(df), len(df.columns))
    return df


def load_xes(path: Path) -> pd.DataFrame:
    validate_input_path(path)
    logger.info("Loading XES from %s", path)
    log = pm4py.read_xes(str(path))
    df = pm4py.convert_to_dataframe(log)
    logger.info("Loaded %d rows, %d columns", len(df), len(df.columns))
    return df


def load_parquet(path: Path) -> pd.DataFrame:
    validate_input_path(path)
    logger.info("Loading Parquet from %s", path)
    df = pd.read_parquet(path)
    logger.info("Loaded %d rows, %d columns", len(df), len(df.columns))
    return df


def load_event_log(
    path: Path,
    fmt: str | None = None,
) -> pd.DataFrame:
    if fmt is None:
        fmt = path.suffix.lower().lstrip(".")
    loaders = {
        "csv": load_csv,
        "xes": load_xes,
        "parquet": load_parquet,
    }
    loader = loaders.get(fmt)
    if loader is None:
        raise ValueError(f"Unsupported format: {fmt}. Use csv, xes, or parquet.")
    return loader(path)
