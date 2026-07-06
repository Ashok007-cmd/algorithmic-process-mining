from __future__ import annotations

import pandas as pd

from src.utils.log_utils import get_logger

logger = get_logger(__name__)


def compute_cycle_time(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["start", "end", "cycle_time_hours"])
    df = df.copy()
    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"])
    case_times = (
        df.groupby("case:concept:name")["time:timestamp"].agg(["min", "max"]).rename(columns={"min": "start", "max": "end"})
    )
    case_times["cycle_time_hours"] = (case_times["end"] - case_times["start"]).dt.total_seconds() / 3600
    logger.info(
        "Cycle time: mean=%.2fh, median=%.2fh",
        case_times["cycle_time_hours"].mean(),
        case_times["cycle_time_hours"].median(),
    )
    return case_times


def compute_throughput_times(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["mean_hours", "median_hours", "std_hours", "count"])
    df = df.copy()
    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"])
    df = df.sort_values(["case:concept:name", "time:timestamp"])
    df["prev_timestamp"] = df.groupby("case:concept:name")["time:timestamp"].shift(1)
    df["throughput_hours"] = (df["time:timestamp"] - df["prev_timestamp"]).dt.total_seconds() / 3600
    act_times = df.groupby("concept:name")["throughput_hours"].agg(["mean", "median", "std", "count"])
    act_times.columns = ["mean_hours", "median_hours", "std_hours", "count"]
    logger.info("Throughput times computed for %d activities", len(act_times))
    return act_times


def compute_case_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["n_events", "n_unique_activities", "start", "end", "cycle_time_hours"])
    df = df.copy()
    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"])
    summary = df.groupby("case:concept:name").agg(
        n_events=("concept:name", "count"),
        n_unique_activities=("concept:name", "nunique"),
        start=("time:timestamp", "min"),
        end=("time:timestamp", "max"),
    )
    summary["cycle_time_hours"] = (summary["end"] - summary["start"]).dt.total_seconds() / 3600
    return summary
