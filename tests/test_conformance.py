from __future__ import annotations

import pytest

from src.conformance.alignments import check_alignments
from src.conformance.comparison import compare_methods, compare_to_normative, load_normative_model
from src.conformance.token_replay import check_token_replay
from src.discovery.inductive import discover_inductive


class TestTokenReplay:
    def test_token_replay_on_self(self, o2c_df):
        net, im, fm = discover_inductive(o2c_df)
        result = check_token_replay(o2c_df, net, im, fm)
        assert result["fitness"] >= 0.8
        assert "total_cases" in result

    def test_token_replay_returns_correct_types(self, o2c_df):
        net, im, fm = discover_inductive(o2c_df)
        result = check_token_replay(o2c_df, net, im, fm)
        assert isinstance(result["fitness"], float)
        assert isinstance(result["fitted_cases"], int)
        assert isinstance(result["non_fitted_cases"], int)


class TestAlignments:
    def test_alignments_on_self(self, o2c_df):
        net, im, fm = discover_inductive(o2c_df)
        result = check_alignments(o2c_df, net, im, fm)
        assert result["fitness"] >= 0.8

    def test_alignments_caps_to_max_alignments(self, o2c_df):
        net, im, fm = discover_inductive(o2c_df)
        total_cases = o2c_df["case:concept:name"].nunique()
        result = check_alignments(o2c_df, net, im, fm, max_alignments=2)
        assert result["total_cases"] == 2
        assert result["total_cases"] < total_cases


class TestComparison:
    def test_compare_methods(self, o2c_df):
        net, im, fm = discover_inductive(o2c_df)
        result = compare_methods(o2c_df, net, im, fm)
        assert "token_replay" in result
        assert "alignments" in result
        assert "delta_fitness" in result


class TestNormativeComparison:
    def test_load_normative_model(self):
        net, im, fm = load_normative_model("data/normative/o2c_sop.pnml")
        assert len(net.transitions) > 0

    def test_load_normative_model_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_normative_model(tmp_path / "missing.pnml")

    def test_compare_to_normative(self, o2c_df):
        result = compare_to_normative(o2c_df, "data/normative/o2c_sop.pnml")
        assert "token_replay" in result
        assert "alignments" in result
        assert result["normative_model"] == "data/normative/o2c_sop.pnml"
        # o2c_df is the clean happy-path log, so it should conform well.
        assert result["token_replay"]["fitness"] >= 0.9
