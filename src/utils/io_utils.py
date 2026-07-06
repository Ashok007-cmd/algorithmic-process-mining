from __future__ import annotations

from pathlib import Path

MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB


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
