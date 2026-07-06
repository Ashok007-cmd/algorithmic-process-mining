from __future__ import annotations

from src.analysis.bottlenecks import find_bottlenecks, find_rework
from src.analysis.kpis import compute_case_summary, compute_cycle_time, compute_throughput_times
from src.analysis.variants import compute_variants, get_happy_path_share


class TestKpis:
    def test_cycle_time(self, o2c_df):
        result = compute_cycle_time(o2c_df)
        assert "cycle_time_hours" in result.columns

    def test_case_summary(self, o2c_df):
        result = compute_case_summary(o2c_df)
        assert len(result) == o2c_df["case:concept:name"].nunique()

    def test_throughput_times(self, o2c_df):
        result = compute_throughput_times(o2c_df)
        assert "mean_hours" in result.columns


class TestBottlenecks:
    def test_find_bottlenecks(self, o2c_df):
        result = find_bottlenecks(o2c_df)
        assert "bottleneck_score" in result.columns

    def test_find_rework(self, o2c_df):
        result = find_rework(o2c_df)
        assert result is not None


class TestVariants:
    def test_compute_variants(self, o2c_df):
        result = compute_variants(o2c_df)
        assert "count" in result.columns
        assert "pct" in result.columns

    def test_happy_path_share(self, o2c_df):
        from src.data.generators.synthetic import O2C_MODEL

        share = get_happy_path_share(o2c_df, O2C_MODEL.happy_path)
        assert 0.0 <= share <= 1.0
