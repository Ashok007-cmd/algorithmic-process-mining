from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import pytest

import src.viz.charts as charts


class TestCharts:
    @pytest.fixture
    def cycle_data(self):
        return pd.DataFrame({"cycle_time_hours": [1.0, 2.0, 3.0]})

    @pytest.fixture
    def activity_data(self):
        return pd.DataFrame({"concept:name": ["a", "b", "a", "c"]})

    @pytest.fixture
    def variant_data(self):
        return pd.DataFrame({"variant": ["a → b", "a → c"], "count": [5, 3], "pct": [62.5, 37.5]})

    @pytest.fixture
    def throughput_data(self):
        return pd.DataFrame({"concept:name": ["a", "b"], "mean_hours": [1.0, 2.0], "std_hours": [0.1, 0.2]})

    def test_cycle_time_distribution(self, cycle_data):
        fig = charts.plot_cycle_time_distribution(cycle_data)
        assert isinstance(fig, go.Figure)

    def test_activity_frequency(self, activity_data):
        fig = charts.plot_activity_frequency(activity_data)
        assert isinstance(fig, go.Figure)

    def test_throughput_times(self, throughput_data):
        fig = charts.plot_throughput_times(throughput_data)
        assert isinstance(fig, go.Figure)

    def test_variant_distribution(self, variant_data):
        fig = charts.plot_variant_distribution(variant_data)
        assert isinstance(fig, go.Figure)

    def test_fitness_comparison(self):
        fig = charts.plot_fitness_comparison({"tr": {"fitness": 0.9}, "al": {"fitness": 0.95}})
        assert isinstance(fig, go.Figure)

    def test_empty_data(self):
        empty = pd.DataFrame()
        assert isinstance(charts.plot_cycle_time_distribution(empty), go.Figure)
        assert isinstance(charts.plot_activity_frequency(empty), go.Figure)
        assert isinstance(charts.plot_throughput_times(empty), go.Figure)

    def test_empty_variant(self):
        empty = pd.DataFrame(columns=["variant", "count", "pct"])
        assert isinstance(charts.plot_variant_distribution(empty), go.Figure)

    def test_empty_comparison(self):
        assert isinstance(charts.plot_fitness_comparison({}), go.Figure)
