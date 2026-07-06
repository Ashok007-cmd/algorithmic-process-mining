from __future__ import annotations

import pandas as pd
import pytest

from src.utils.io_utils import sanitize_for_csv_injection, validate_input_path


class TestValidateInputPath:
    def test_valid_file(self, tmp_path):
        path = tmp_path / "file.csv"
        path.write_text("data")
        assert validate_input_path(path) == path.resolve()

    def test_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            validate_input_path(tmp_path / "missing.csv")

    def test_not_a_file(self, tmp_path):
        with pytest.raises(ValueError, match="Not a file"):
            validate_input_path(tmp_path)

    def test_file_too_large(self, tmp_path):
        path = tmp_path / "big.csv"
        path.write_text("x" * 100)
        with pytest.raises(ValueError, match="File too large"):
            validate_input_path(path, max_size_bytes=10)


class TestSanitizeForCsvInjection:
    @pytest.mark.parametrize(
        "payload",
        [
            "=cmd|'/C calc'!A0",
            '+HYPERLINK("http://evil.example","click")',
            "-2+3",
            "@SUM(1+9)",
            "\ttab-prefixed",
            "\rcr-prefixed",
        ],
    )
    def test_neutralizes_formula_triggers(self, payload):
        df = pd.DataFrame({"concept:name": [payload]})
        result = sanitize_for_csv_injection(df)
        assert result["concept:name"].iloc[0] == f"'{payload}"

    def test_leaves_normal_strings_untouched(self):
        df = pd.DataFrame({"concept:name": ["Order Created", "Ship Order"]})
        result = sanitize_for_csv_injection(df)
        assert list(result["concept:name"]) == ["Order Created", "Ship Order"]

    def test_handles_categorical_columns(self):
        df = pd.DataFrame({"concept:name": pd.Categorical(["=evil()", "Normal"])})
        result = sanitize_for_csv_injection(df)
        assert result["concept:name"].iloc[0] == "'=evil()"
        assert result["concept:name"].iloc[1] == "Normal"

    def test_leaves_non_string_columns_untouched(self):
        df = pd.DataFrame({"count": [1, 2, 3]})
        result = sanitize_for_csv_injection(df)
        assert list(result["count"]) == [1, 2, 3]

    def test_does_not_mutate_input(self):
        df = pd.DataFrame({"concept:name": ["=evil()"]})
        sanitize_for_csv_injection(df)
        assert df["concept:name"].iloc[0] == "=evil()"
