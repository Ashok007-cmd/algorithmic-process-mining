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


def validate_input_path(
    path: Path,
    max_size_bytes: int = MAX_FILE_SIZE_BYTES,
    allowed_root: Path | None = None,
) -> Path:
    """Validate that `path` is an existing, readable file within a size limit.

    Returns the resolved path. Raises FileNotFoundError if it doesn't exist,
    or ValueError if it's not a regular file, exceeds `max_size_bytes`, or (when
    `allowed_root` is given) resolves outside that directory.

    `allowed_root` is opt-in and unset by default: this tool's threat model is a
    single local user with the same filesystem permissions as the shell invoking
    it, so there's no privilege boundary to enforce by default (see
    docs/AUDIT_REPORT.md §4.5). Set it if this pipeline is ever driven by paths
    from an untrusted remote caller (e.g. a networked/multi-tenant service).
    """
    resolved = path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not resolved.is_file():
        raise ValueError(f"Not a file: {path}")
    if allowed_root is not None and not resolved.is_relative_to(allowed_root.resolve()):
        raise ValueError(f"Path outside allowed data root: {path}")
    size = resolved.stat().st_size
    if size > max_size_bytes:
        raise ValueError(f"File too large: {size / 1024 / 1024:.1f} MB (max {max_size_bytes / 1024 / 1024:.0f} MB)")
    return resolved
