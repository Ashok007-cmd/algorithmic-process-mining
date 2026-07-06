from __future__ import annotations

import pandas as pd
import pytest

from src.analysis.bottlenecks import find_bottlenecks, find_rework
from src.analysis.kpis import compute_case_summary, compute_cycle_time, compute_throughput_times
from src.analysis.variants import compute_variants, get_happy_path_share
from src.conformance.alignments import check_alignments
from src.conformance.comparison import compare_methods
from src.conformance.token_replay import check_token_replay
from src.data.generators.synthetic import O2C_MODEL, generate_o2c_log
from src.data.pipeline import run_pipeline
from src.discovery.inductive import discover_inductive


class TestFullPipeline:
    @pytest.fixture(scope="class")
    def log(self):
        return generate_o2c_log(n_cases=20, noise_level=0.3, seed=42)

    def test_end_to_end(self, log, tmp_path):
        path = tmp_path / "events.csv"
        log.to_csv(path, index=False)
        result = run_pipeline(path)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(log)

    def test_discover_to_conformance(self, log):
        net, im, fm = discover_inductive(log)
        tr = check_token_replay(log, net, im, fm)
        al = check_alignments(log, net, im, fm)
        comparison = compare_methods(log, net, im, fm)
        assert tr["fitness"] > 0
        assert al["fitness"] > 0
        assert comparison["delta_fitness"] > -0.5

    def test_discover_to_analysis(self, log):
        net, im, fm = discover_inductive(log)
        assert net is not None
        cycle = compute_cycle_time(log)
        assert not cycle.empty
        summary = compute_case_summary(log)
        assert not summary.empty
        throughput = compute_throughput_times(log)
        assert not throughput.empty

    def test_analysis_chain(self, log):
        bottlenecks = find_bottlenecks(log)
        assert not bottlenecks.empty
        rework = find_rework(log)
        assert rework is not None
        variants = compute_variants(log)
        assert not variants.empty
        share = get_happy_path_share(log, O2C_MODEL.happy_path)
        assert 0.0 <= share <= 1.0


class TestEmptyDataFrame:
    @pytest.fixture
    def empty(self):
        return pd.DataFrame(columns=["case:concept:name", "concept:name", "time:timestamp"])

    def test_empty_cycle_time(self, empty):
        result = compute_cycle_time(empty)
        assert result.empty

    def test_empty_throughput(self, empty):
        result = compute_throughput_times(empty)
        assert result.empty

    def test_empty_case_summary(self, empty):
        result = compute_case_summary(empty)
        assert result.empty

    def test_empty_bottlenecks(self, empty):
        result = find_bottlenecks(empty)
        assert result.empty

    def test_empty_rework(self, empty):
        result = find_rework(empty)
        assert result.empty

    def test_empty_variants(self, empty):
        result = compute_variants(empty)
        assert result.empty
