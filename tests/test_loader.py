from __future__ import annotations

from pathlib import Path

import pandas as pd
import pm4py
import pytest

from src.data.loader import load_csv, load_event_log, load_parquet, load_xes


class TestLoader:
    def test_load_csv(self, tmp_path, o2c_df):
        path = tmp_path / "test.csv"
        o2c_df.to_csv(path, index=False)
        result = load_csv(path)
        assert len(result) == len(o2c_df)

    def test_load_csv_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_csv(Path("/nonexistent/file.csv"))

    def test_load_csv_not_a_file(self, tmp_path):
        with pytest.raises(ValueError, match="Not a file"):
            load_csv(tmp_path)

    def test_load_sample_o2c_fixture(self, sample_o2c_df):
        assert "case:concept:name" in sample_o2c_df.columns
        assert sample_o2c_df["case:concept:name"].nunique() > 0

    def test_load_sample_p2p_fixture(self, sample_p2p_df):
        assert "case:concept:name" in sample_p2p_df.columns
        assert sample_p2p_df["case:concept:name"].nunique() > 0

    def test_load_parquet(self, tmp_path, o2c_df):
        path = tmp_path / "test.parquet"
        o2c_df.to_parquet(path, index=False)
        result = load_parquet(path)
        assert len(result) == len(o2c_df)

    def test_load_event_log_dispatches_by_extension(self, tmp_path, o2c_df):
        csv_path = tmp_path / "test.csv"
        o2c_df.to_csv(csv_path, index=False)
        result = load_event_log(csv_path)
        assert len(result) == len(o2c_df)

        parquet_path = tmp_path / "test.parquet"
        o2c_df.to_parquet(parquet_path, index=False)
        result = load_event_log(parquet_path)
        assert len(result) == len(o2c_df)

    def test_load_event_log_unsupported_format(self, tmp_path):
        path = tmp_path / "test.xyz"
        path.write_text("data")
        with pytest.raises(ValueError, match="Unsupported format"):
            load_event_log(path)

    @pytest.fixture
    def o2c_xes_df(self, o2c_df):
        df = o2c_df.copy()
        df["time:timestamp"] = pd.to_datetime(df["time:timestamp"])
        return df

    def test_load_xes(self, tmp_path, o2c_xes_df):
        path = tmp_path / "test.xes"
        pm4py.write_xes(o2c_xes_df, str(path))
        result = load_xes(path)
        assert len(result) == len(o2c_xes_df)
        assert result["case:concept:name"].nunique() == o2c_xes_df["case:concept:name"].nunique()

    def test_load_xes_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_xes(Path("/nonexistent/file.xes"))

    def test_load_event_log_dispatches_xes(self, tmp_path, o2c_xes_df):
        path = tmp_path / "test.xes"
        pm4py.write_xes(o2c_xes_df, str(path))
        result = load_event_log(path)
        assert len(result) == len(o2c_xes_df)
