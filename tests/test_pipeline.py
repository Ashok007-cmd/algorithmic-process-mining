from __future__ import annotations

import pandas as pd

from src.data.pipeline import run_pipeline


class TestPipeline:
    def test_pipeline_with_csv(self, tmp_path, o2c_df):
        path = tmp_path / "test.csv"
        o2c_df.to_csv(path, index=False)
        result = run_pipeline(path)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(o2c_df)

    def test_pipeline_anonymize(self, tmp_path, o2c_df):
        path = tmp_path / "test.csv"
        o2c_df.to_csv(path, index=False)
        result = run_pipeline(path, anonymize=True)
        assert isinstance(result, pd.DataFrame)
        assert not result["case:concept:name"].str.startswith("ORD_").any()
