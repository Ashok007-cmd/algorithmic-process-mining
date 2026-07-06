from __future__ import annotations

import hashlib
import os

import pandas as pd

from src.utils.log_utils import get_logger

logger = get_logger(__name__)


def hash_case_ids(df: pd.DataFrame, salt: str | None = None) -> pd.DataFrame:
    df = df.copy()
    actual_salt = salt if salt is not None else os.getenv("ANONYMIZER_SALT", "")
    if not actual_salt:
        logger.warning(
            "Anonymizing with an empty salt -- case ID hashes are vulnerable to "
            "dictionary/rainbow-table attacks on predictable IDs. Set ANONYMIZER_SALT "
            "or pass salt= explicitly."
        )
    if "case:concept:name" in df.columns:
        unique_ids = df["case:concept:name"].unique()
        hash_map = {case_id: hashlib.sha256((actual_salt + str(case_id)).encode()).hexdigest()[:16] for case_id in unique_ids}
        df["case:concept:name"] = df["case:concept:name"].map(hash_map)
        logger.info("Hashed %d case IDs", len(hash_map))
    return df


def anonymize_event_log(df: pd.DataFrame, salt: str | None = None) -> pd.DataFrame:
    return hash_case_ids(df, salt)
