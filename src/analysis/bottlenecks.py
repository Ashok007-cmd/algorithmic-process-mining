from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.log_utils import get_logger

logger = get_logger(__name__)


def find_bottlenecks(
    df: pd.DataFrame,
    threshold_percentile: float = 80.0,
) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["mean", "median", "std", "count", "bottleneck_score"])
    df = df.copy()
    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"])
    df = df.sort_values(["case:concept:name", "time:timestamp"])
    df["prev_timestamp"] = df.groupby("case:concept:name")["time:timestamp"].shift(1)
    df["throughput_hours"] = (df["time:timestamp"] - df["prev_timestamp"]).dt.total_seconds() / 3600
    avg_times = (
        df.groupby("concept:name")["throughput_hours"]
        .agg(["mean", "median", "std", "count"])
        .sort_values("mean", ascending=False)
    )
    threshold = np.percentile(avg_times["mean"].dropna(), threshold_percentile)
    bottlenecks = avg_times[avg_times["mean"] >= threshold].copy()
    bottlenecks["bottleneck_score"] = bottlenecks["mean"] / bottlenecks["mean"].max()
    bottlenecks = bottlenecks.sort_values("bottleneck_score", ascending=False)
    logger.info(
        "Found %d bottleneck activities above %.1f%%ile threshold=%.2fh",
        len(bottlenecks),
        threshold_percentile,
        threshold,
    )
    return bottlenecks


def find_rework(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["total_rework", "avg_rework", "cases_with_rework"])
    df = df.sort_values(["case:concept:name", "time:timestamp"])
    df["prev_activity"] = df.groupby("case:concept:name")["concept:name"].shift(1)
    rework = df[df["concept:name"] == df["prev_activity"]]
    rework_counts = rework.groupby(["concept:name", "case:concept:name"]).size().reset_index(name="count")
    summary = (
        rework_counts.groupby("concept:name")["count"]
        .agg(["sum", "mean", "count"])
        .rename(columns={"sum": "total_rework", "mean": "avg_rework", "count": "cases_with_rework"})
    )
    logger.info("Found rework in %d activities", len(summary))
    return summary
