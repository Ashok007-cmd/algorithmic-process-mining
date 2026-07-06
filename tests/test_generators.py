from __future__ import annotations

import pandas as pd
import pytest

from src.data.generators.synthetic import (
    O2C_MODEL,
    P2P_MODEL,
    generate_o2c_log,
    generate_p2p_log,
    get_normative_sequences,
)


class TestGenerators:
    def test_o2c_returns_dataframe(self):
        df = generate_o2c_log(n_cases=5, seed=42)
        assert isinstance(df, pd.DataFrame)

    def test_o2c_has_required_columns(self):
        df = generate_o2c_log(n_cases=5, seed=42)
        assert "case:concept:name" in df.columns
        assert "concept:name" in df.columns
        assert "time:timestamp" in df.columns

    def test_o2c_correct_case_count(self):
        df = generate_o2c_log(n_cases=20, seed=42)
        assert df["case:concept:name"].nunique() == 20

    def test_o2c_happy_path_no_noise(self):
        df = generate_o2c_log(n_cases=1, noise_level=0.0, seed=42)
        trace = df[df["case:concept:name"] == "ORD_00001"]["concept:name"].tolist()
        assert trace == O2C_MODEL.happy_path

    def test_p2p_returns_dataframe(self):
        df = generate_p2p_log(n_cases=3, seed=42)
        assert isinstance(df, pd.DataFrame)

    def test_p2p_correct_case_count(self):
        df = generate_p2p_log(n_cases=15, seed=42)
        assert df["case:concept:name"].nunique() == 15

    def test_p2p_happy_path_no_noise(self):
        df = generate_p2p_log(n_cases=1, noise_level=0.0, seed=42)
        trace = df[df["case:concept:name"] == "PRO_00001"]["concept:name"].tolist()
        assert trace == P2P_MODEL.happy_path

    def test_noise_produces_deviations(self):
        df_clean = generate_o2c_log(n_cases=50, noise_level=0.0, seed=42)
        df_noisy = generate_o2c_log(n_cases=50, noise_level=1.0, seed=42)
        clean_variants = df_clean.groupby("case:concept:name")["concept:name"].agg(tuple).nunique()
        noisy_variants = df_noisy.groupby("case:concept:name")["concept:name"].agg(tuple).nunique()
        assert noisy_variants >= clean_variants

    def test_seeded_reproducibility(self):
        df1 = generate_o2c_log(n_cases=10, noise_level=0.5, seed=99)
        df2 = generate_o2c_log(n_cases=10, noise_level=0.5, seed=99)
        assert df1.equals(df2)

    def test_normative_sequences_o2c(self):
        seqs = get_normative_sequences("o2c")
        assert seqs[0] == O2C_MODEL.happy_path

    def test_normative_sequences_p2p(self):
        seqs = get_normative_sequences("p2p")
        assert seqs[0] == P2P_MODEL.happy_path

    def test_invalid_model_name(self):
        with pytest.raises(ValueError):
            get_normative_sequences("invalid")

    def test_timestamps_are_in_order(self):
        df = generate_o2c_log(n_cases=3, seed=42)
        for case_id, group in df.groupby("case:concept:name"):
            times = pd.to_datetime(group["time:timestamp"])
            assert times.is_monotonic_increasing
