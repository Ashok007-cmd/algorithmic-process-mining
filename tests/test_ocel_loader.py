from __future__ import annotations

from pathlib import Path

import pm4py
import pytest

from src.data.ocel.loader import extract_ocel_events, extract_ocel_objects, load_ocel


@pytest.fixture
def sample_ocel_json(tmp_path, o2c_df):
    df = o2c_df.copy()
    df["case:concept:name"] = df["case:concept:name"].astype(str)
    ocel = pm4py.convert_log_to_ocel(df, object_types=["case:concept:name"])
    path = tmp_path / "sample.json"
    pm4py.write_ocel2_json(ocel, str(path))
    return path


class TestLoadOcel:
    def test_load_json(self, sample_ocel_json):
        ocel = load_ocel(sample_ocel_json)
        assert ocel is not None

    def test_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_ocel(Path("/nonexistent/file.json"))

    def test_unsupported_format(self, tmp_path):
        path = tmp_path / "sample.txt"
        path.write_text("data")
        with pytest.raises(ValueError, match="Unsupported OCEL format"):
            load_ocel(path)

    def test_extract_ocel_objects(self, sample_ocel_json, o2c_df):
        ocel = load_ocel(sample_ocel_json)
        objects = extract_ocel_objects(ocel)
        assert set(objects) == set(o2c_df["case:concept:name"].astype(str).unique())

    def test_extract_ocel_events(self, sample_ocel_json):
        ocel = load_ocel(sample_ocel_json)
        events = extract_ocel_events(ocel)
        assert len(events) > 0
