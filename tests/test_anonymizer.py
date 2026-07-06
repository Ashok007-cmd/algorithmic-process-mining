from __future__ import annotations

from src.data.anonymizer import anonymize_event_log


class TestAnonymizer:
    def test_case_ids_changed(self, o2c_df):
        result = anonymize_event_log(o2c_df, salt="test")
        assert not result["case:concept:name"].str.startswith("ORD_").any()

    def test_salt_changes_output(self, o2c_df):
        r1 = anonymize_event_log(o2c_df, salt="a")
        r2 = anonymize_event_log(o2c_df, salt="b")
        assert not r1["case:concept:name"].equals(r2["case:concept:name"])
