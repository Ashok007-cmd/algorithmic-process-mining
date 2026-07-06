import subprocess
import sys
from pathlib import Path


def test_cli_e2e(tmp_path: Path) -> None:
    # Test generation
    output_log = tmp_path / "test_o2c.csv"
    gen_cmd = [sys.executable, "-m", "src.cli", "generate", "--process", "o2c", "--cases", "10", "--output", str(output_log)]
    result = subprocess.run(gen_cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Generate failed: {result.stderr}"
    assert output_log.exists(), "Output log was not created"

    # Test pipeline run
    output_result = tmp_path / "result_o2c.csv"
    run_cmd = [sys.executable, "-m", "src.cli", "run", "--input", str(output_log), "--output", str(output_result)]
    result2 = subprocess.run(run_cmd, capture_output=True, text=True)
    assert result2.returncode == 0, f"Run failed: {result2.stderr}"
    assert output_result.exists(), "Output result was not created"
