from __future__ import annotations

import pytest

from src.utils.io_utils import validate_input_path


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
