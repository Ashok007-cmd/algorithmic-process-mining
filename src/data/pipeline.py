from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from src.data import anonymizer, loader, transformer, validator
from src.utils.log_utils import get_logger

logger = get_logger(__name__)


def _cache_key(
    path: Path,
    fmt: str | None,
    column_mapping: dict[str, str] | None,
    anonymize: bool,
    salt: str,
) -> str:
    """Cheap invalidation key: source path + size + mtime + pipeline params.

    Hashing the full file content would defeat the purpose of caching on
    large logs, so this mirrors the mtime/size-based approach used by
    incremental build tools (make, mypy) instead.
    """
    resolved = path.resolve()
    stat = resolved.stat()
    payload = {
        "path": str(resolved),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "fmt": fmt,
        "column_mapping": column_mapping,
        "anonymize": anonymize,
        "salt_hash": hashlib.sha256(salt.encode()).hexdigest() if anonymize else None,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def run_pipeline(
    path: Path,
    fmt: str | None = None,
    column_mapping: dict[str, str] | None = None,
    anonymize: bool = False,
    salt: str = "",
    cache_dir: Path | None = None,
) -> pd.DataFrame:
    logger.info("Pipeline start: %s", path)

    cache_path = None
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / f"{_cache_key(path, fmt, column_mapping, anonymize, salt)}.parquet"
        if cache_path.exists():
            logger.info("Pipeline cache hit -> %s", cache_path)
            return pd.read_parquet(cache_path)

    df = loader.load_event_log(path, fmt)
    df = transformer.transform_event_log(df, column_mapping)
    df = validator.validate_event_log(df)
    if anonymize:
        df = anonymizer.anonymize_event_log(df, salt)
    logger.info("Pipeline complete: %d rows, %d cases", len(df), df["case:concept:name"].nunique())

    if cache_path is not None:
        df.to_parquet(cache_path, index=False)
        logger.info("Pipeline cache write -> %s", cache_path)

    return df
