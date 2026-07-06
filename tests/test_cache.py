from __future__ import annotations

import pandas as pd

from src.utils.cache import cached_discovery, dataframe_hash


class TestDataframeHash:
    def test_same_content_same_hash(self):
        df1 = pd.DataFrame({"a": [1, 2, 3]})
        df2 = pd.DataFrame({"a": [1, 2, 3]})
        assert dataframe_hash(df1) == dataframe_hash(df2)

    def test_different_content_different_hash(self):
        df1 = pd.DataFrame({"a": [1, 2, 3]})
        df2 = pd.DataFrame({"a": [1, 2, 4]})
        assert dataframe_hash(df1) != dataframe_hash(df2)


class TestCachedDiscovery:
    def test_cache_hit_returns_same_object(self):
        calls = []

        @cached_discovery()
        def discover(df: pd.DataFrame) -> object:
            calls.append(1)
            return object()

        df = pd.DataFrame({"a": [1, 2, 3]})
        r1 = discover(df)
        r2 = discover(df)
        assert r1 is r2
        assert len(calls) == 1

    def test_cache_miss_on_different_input(self):
        @cached_discovery()
        def discover(df: pd.DataFrame) -> object:
            return object()

        df1 = pd.DataFrame({"a": [1, 2, 3]})
        df2 = pd.DataFrame({"a": [4, 5, 6]})
        assert discover(df1) is not discover(df2)

    def test_cache_miss_on_different_kwargs(self):
        @cached_discovery()
        def discover(df: pd.DataFrame, noise_threshold: float = 0.0) -> object:
            return object()

        df = pd.DataFrame({"a": [1, 2, 3]})
        assert discover(df, noise_threshold=0.0) is not discover(df, noise_threshold=0.5)

    def test_lru_eviction(self):
        calls = []

        @cached_discovery(maxsize=2)
        def discover(df: pd.DataFrame) -> object:
            calls.append(1)
            return object()

        dfs = [pd.DataFrame({"a": [i]}) for i in range(3)]
        for df in dfs:
            discover(df)
        # First df's entry should have been evicted; re-calling recomputes.
        discover(dfs[0])
        assert len(calls) == 4
