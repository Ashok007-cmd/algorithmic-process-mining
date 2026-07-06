from __future__ import annotations

import json

import pytest

from src.cli import build_parser, cmd_conformance, cmd_discover, cmd_generate, cmd_run


class TestCmdGenerate:
    def test_generate_csv(self, tmp_path):
        output = tmp_path / "log.csv"
        args = build_parser().parse_args(["generate", "--process", "o2c", "--cases", "5", "--output", str(output)])
        cmd_generate(args)
        assert output.exists()

    def test_generate_unsupported_extension_falls_back_to_csv_and_logs_actual_path(self, tmp_path, caplog):
        output = tmp_path / "log.xyz"
        args = build_parser().parse_args(["generate", "--process", "o2c", "--cases", "3", "--output", str(output)])
        with caplog.at_level("INFO"):
            cmd_generate(args)
        actual_path = output.with_suffix(".csv")
        assert actual_path.exists()
        assert not output.exists()
        assert str(actual_path) in caplog.text
        assert str(output) not in caplog.text

    def test_generate_failure_exits_nonzero(self, tmp_path):
        args = build_parser().parse_args(
            ["generate", "--process", "o2c", "--cases", "5", "--output", str(tmp_path / "nonexistent_dir" / "log.csv")]
        )
        with pytest.raises(SystemExit) as exc_info:
            cmd_generate(args)
        assert exc_info.value.code == 1


class TestCmdRun:
    def test_run_csv(self, tmp_path, o2c_df):
        raw = tmp_path / "raw.csv"
        o2c_df.to_csv(raw, index=False)
        output = tmp_path / "clean.csv"
        args = build_parser().parse_args(["run", "--input", str(raw), "--output", str(output)])
        cmd_run(args)
        assert output.exists()

    def test_run_neutralizes_csv_formula_injection(self, tmp_path):
        import pandas as pd

        raw = tmp_path / "raw.csv"
        pd.DataFrame(
            {
                "case:concept:name": ["=cmd|'/C calc'!A0", "ORD_2"],
                "concept:name": ['+HYPERLINK("http://evil.example")', "Order Created"],
                "time:timestamp": ["2024-01-01 08:00:00", "2024-01-01 09:00:00"],
            }
        ).to_csv(raw, index=False)
        output = tmp_path / "clean.csv"
        args = build_parser().parse_args(["run", "--input", str(raw), "--output", str(output)])
        cmd_run(args)

        raw_text = output.read_text()
        # A leading single quote tells Excel/LibreOffice/Sheets to render the
        # cell as literal text instead of evaluating it as a formula.
        assert "'=cmd|'/C calc'!A0" in raw_text
        assert "'+HYPERLINK" in raw_text

    def test_run_with_anonymize(self, tmp_path, o2c_df):
        raw = tmp_path / "raw.csv"
        o2c_df.to_csv(raw, index=False)
        output = tmp_path / "clean.csv"
        args = build_parser().parse_args(["run", "--input", str(raw), "--output", str(output), "--anonymize", "--salt", "test"])
        cmd_run(args)
        import pandas as pd

        result = pd.read_csv(output)
        assert not result["case:concept:name"].astype(str).str.startswith("ORD_").any()


class TestCmdDiscover:
    def test_discover_writes_pnml(self, tmp_path, o2c_df):
        raw = tmp_path / "raw.csv"
        o2c_df.to_csv(raw, index=False)
        output = tmp_path / "model.pnml"
        args = build_parser().parse_args(["discover", "--input", str(raw), "--output", str(output)])
        cmd_discover(args)
        assert output.exists()


class TestCmdConformance:
    def test_conformance_against_normative_model(self, tmp_path, o2c_df):
        raw = tmp_path / "raw.csv"
        o2c_df.to_csv(raw, index=False)
        output = tmp_path / "conformance.json"
        args = build_parser().parse_args(
            [
                "conformance",
                "--input",
                str(raw),
                "--model",
                "data/normative/o2c_sop.pnml",
                "--output",
                str(output),
            ]
        )
        cmd_conformance(args)
        result = json.loads(output.read_text())
        assert "token_replay" in result
        assert "alignments" in result
        assert result["normative_model"] == "data/normative/o2c_sop.pnml"

    def test_conformance_falls_back_to_discovery_if_model_missing(self, tmp_path, o2c_df):
        raw = tmp_path / "raw.csv"
        o2c_df.to_csv(raw, index=False)
        output = tmp_path / "conformance.json"
        args = build_parser().parse_args(
            [
                "conformance",
                "--input",
                str(raw),
                "--model",
                str(tmp_path / "missing.pnml"),
                "--output",
                str(output),
            ]
        )
        cmd_conformance(args)
        result = json.loads(output.read_text())
        assert result["normative_model"] is None
