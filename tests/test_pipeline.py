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


class TestPipelineCache:
    def test_cache_miss_then_hit(self, tmp_path, o2c_df):
        path = tmp_path / "test.csv"
        o2c_df.to_csv(path, index=False)
        cache_dir = tmp_path / "cache"

        result1 = run_pipeline(path, cache_dir=cache_dir)
        cached_files = list(cache_dir.glob("*.parquet"))
        assert len(cached_files) == 1

        result2 = run_pipeline(path, cache_dir=cache_dir)
        assert list(cache_dir.glob("*.parquet")) == cached_files
        pd.testing.assert_frame_equal(result1, result2)

    def test_cache_invalidated_on_content_change(self, tmp_path, o2c_df, p2p_df):
        path = tmp_path / "test.csv"
        cache_dir = tmp_path / "cache"

        o2c_df.to_csv(path, index=False)
        result1 = run_pipeline(path, cache_dir=cache_dir)

        p2p_df.to_csv(path, index=False)
        result2 = run_pipeline(path, cache_dir=cache_dir)

        assert len(result1) != len(result2) or not result1.equals(result2)
        assert len(list(cache_dir.glob("*.parquet"))) == 2

    def test_cache_keys_differ_by_anonymize(self, tmp_path, o2c_df):
        path = tmp_path / "test.csv"
        o2c_df.to_csv(path, index=False)
        cache_dir = tmp_path / "cache"

        run_pipeline(path, cache_dir=cache_dir, anonymize=False)
        run_pipeline(path, cache_dir=cache_dir, anonymize=True, salt="s")
        assert len(list(cache_dir.glob("*.parquet"))) == 2
