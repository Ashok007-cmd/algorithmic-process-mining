from __future__ import annotations

import pandas as pd

from src.data.transformer import convert_timestamps_to_utc, transform_event_log


class TestConvertTimestamps:
    def test_no_timestamp_column(self):
        df = pd.DataFrame({"a": [1]})
        result = convert_timestamps_to_utc(df)
        assert "a" in result.columns
        assert "time:timestamp" not in result.columns

    def test_naive_to_utc(self):
        df = pd.DataFrame({"case:concept:name": ["A"], "concept:name": ["x"], "time:timestamp": ["2024-01-01 12:00:00"]})
        result = convert_timestamps_to_utc(df)
        assert result["time:timestamp"].iloc[0] == pd.Timestamp("2024-01-01 12:00:00")

    def test_tz_aware_converts(self):
        df = pd.DataFrame({"case:concept:name": ["A"], "concept:name": ["x"], "time:timestamp": ["2024-01-01 12:00:00+05:00"]})
        result = convert_timestamps_to_utc(df)
        assert result["time:timestamp"].iloc[0] == pd.Timestamp("2024-01-01 07:00:00")


class TestTransformEventLog:
    def test_transform_with_datetime(self, o2c_df):
        result = transform_event_log(o2c_df)
        assert "time:timestamp" in result.columns
        assert pd.api.types.is_datetime64_any_dtype(result["time:timestamp"])
