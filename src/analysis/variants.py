from __future__ import annotations

import pandas as pd

from src.utils.log_utils import get_logger

logger = get_logger(__name__)


def compute_variants(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["variant", "count", "pct"])
    seq = (
        df.sort_values("time:timestamp")
        .groupby("case:concept:name")["concept:name"]
        .agg(lambda x: " → ".join(x))
        .reset_index()
        .rename(columns={"concept:name": "variant"})
    )
    variant_counts = seq.groupby("variant").size().reset_index(name="count").sort_values("count", ascending=False)
    variant_counts["pct"] = (variant_counts["count"] / variant_counts["count"].sum() * 100).round(1)
    logger.info("Found %d unique variants", len(variant_counts))
    return variant_counts


def get_happy_path_share(
    df: pd.DataFrame,
    happy_path: list[str],
) -> float:
    seq = df.sort_values("time:timestamp").groupby("case:concept:name")["concept:name"].agg(list)
    matched = sum(1 for s in seq if s == happy_path)
    share = matched / len(seq) if len(seq) > 0 else 0.0
    logger.info("Happy path share: %.1f%% (%d/%d)", share * 100, matched, len(seq))
    return share
