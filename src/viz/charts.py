from __future__ import annotations

from typing import Any

import plotly.express as px
import plotly.graph_objects as go
from pandas import DataFrame

_HISTOGRAM_BINS = 30
_LABEL_TRUNCATE = 50
_X_TICK_ANGLE = -45
_DEFAULT_TOP_VARIANTS = 10
_TICK_ANGLE = -45


def plot_cycle_time_distribution(case_times: DataFrame) -> go.Figure:
    if case_times.empty:
        return _empty_figure("Cycle Time Distribution")
    fig = px.histogram(
        case_times,
        x="cycle_time_hours",
        nbins=_HISTOGRAM_BINS,
        title="Cycle Time Distribution",
        labels={"cycle_time_hours": "Cycle Time (hours)"},
    )
    return fig


def plot_activity_frequency(df: DataFrame) -> go.Figure:
    if df.empty:
        return _empty_figure("Activity Frequency")
    counts = df["concept:name"].value_counts().reset_index()
    counts.columns = ["activity", "count"]
    fig = px.bar(
        counts,
        x="activity",
        y="count",
        title="Activity Frequency",
        labels={"activity": "Activity", "count": "Frequency"},
    )
    fig.update_layout(xaxis_tickangle=_TICK_ANGLE)
    return fig


def plot_throughput_times(throughput: DataFrame) -> go.Figure:
    if throughput.empty:
        return _empty_figure("Mean Throughput Time per Activity")
    throughput = throughput.reset_index()
    fig = px.bar(
        throughput,
        x="concept:name",
        y="mean_hours",
        error_y="std_hours",
        title="Mean Throughput Time per Activity",
        labels={"concept:name": "Activity", "mean_hours": "Mean Hours"},
    )
    fig.update_layout(xaxis_tickangle=_TICK_ANGLE)
    return fig


def plot_variant_distribution(variants: DataFrame, top_n: int = _DEFAULT_TOP_VARIANTS) -> go.Figure:
    if variants.empty:
        return _empty_figure(f"Top {top_n} Variants")
    top = variants.head(top_n).copy()
    top["label"] = top["variant"].str[:_LABEL_TRUNCATE]
    fig = px.bar(
        top,
        x="label",
        y="count",
        title=f"Top {top_n} Variants",
        labels={"label": "Variant", "count": "Cases"},
    )
    fig.update_layout(xaxis_tickangle=_TICK_ANGLE)
    return fig


def plot_fitness_comparison(comparison: dict[str, Any]) -> go.Figure:
    if not comparison:
        return _empty_figure("Fitness Comparison")
    methods = list(comparison.keys())
    fitnesses = [comparison[m]["fitness"] for m in methods]
    fig = px.bar(
        x=methods,
        y=fitnesses,
        title="Fitness Comparison",
        labels={"x": "Method", "y": "Fitness"},
        range_y=[0, 1],
    )
    return fig


def _empty_figure(title: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(title=title, annotations=[{"text": "No data available", "showarrow": False, "font": {"size": 16}}])
    return fig
