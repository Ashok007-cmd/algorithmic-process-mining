from __future__ import annotations

import pandas as pd
import pytest

from src.data.validator import validate_columns, validate_event_log


class TestValidator:
    def test_valid_log_passes(self, o2c_df):
        result = validate_event_log(o2c_df.copy())
        assert isinstance(result, pd.DataFrame)

    def test_missing_column_raises(self):
        df = pd.DataFrame({"a": [1], "b": [2]})
        with pytest.raises(ValueError, match="Missing"):
            validate_columns(df)

    def test_null_timestamps_dropped(self):
        df = pd.DataFrame(
            {
                "case:concept:name": ["A", "A"],
                "concept:name": ["x", "y"],
                "time:timestamp": ["2024-01-01", None],
            }
        )
        result = validate_event_log(df)
        assert len(result) == 1

    def test_null_case_ids_dropped(self):
        df = pd.DataFrame(
            {
                "case:concept:name": [None, "A"],
                "concept:name": ["x", "y"],
                "time:timestamp": ["2024-01-01", "2024-01-02"],
            }
        )
        result = validate_event_log(df)
        assert len(result) == 1

    def test_duplicates_removed(self):
        df = pd.DataFrame(
            {
                "case:concept:name": ["A", "A"],
                "concept:name": ["x", "x"],
                "time:timestamp": ["2024-01-01", "2024-01-01"],
            }
        )
        result = validate_event_log(df)
        assert len(result) == 1
