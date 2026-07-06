from __future__ import annotations

from pathlib import Path

import pandas as pd

MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB

# Leading characters that spreadsheet applications (Excel, LibreOffice, Google
# Sheets) interpret as the start of a formula when a CSV cell is opened.
_CSV_FORMULA_TRIGGERS = ("=", "+", "-", "@", "\t", "\r")


def sanitize_for_csv_injection(df: pd.DataFrame) -> pd.DataFrame:
    """Neutralize spreadsheet formula injection (CWE-1236) before writing CSV.

    Event log values (activity names, resource names, free-text attributes)
    often originate from external systems and can't be trusted not to start
    with a formula trigger character. Any such string cell is prefixed with a
    single quote so it's rendered as literal text, not executed as a formula,
    when the exported CSV is opened in a spreadsheet application.
    """
    df = df.copy()
    for col in df.select_dtypes(include=["object", "string", "category"]).columns:
        df[col] = (
            df[col].astype("object").map(lambda v: f"'{v}" if isinstance(v, str) and v.startswith(_CSV_FORMULA_TRIGGERS) else v)
        )
    return df


def validate_input_path(path: Path, max_size_bytes: int = MAX_FILE_SIZE_BYTES) -> Path:
    """Validate that `path` is an existing, readable file within a size limit.

    Returns the resolved path. Raises FileNotFoundError if it doesn't exist,
    or ValueError if it's not a regular file or exceeds `max_size_bytes`.
    """
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not resolved.is_file():
        raise ValueError(f"Not a file: {path}")
    size = resolved.stat().st_size
    if size > max_size_bytes:
        raise ValueError(f"File too large: {size / 1024 / 1024:.1f} MB (max {max_size_bytes / 1024 / 1024:.0f} MB)")
    return resolved
