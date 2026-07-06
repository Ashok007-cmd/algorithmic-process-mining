from __future__ import annotations

from pathlib import Path
from typing import Any

import pm4py

from src.utils.io_utils import validate_input_path
from src.utils.log_utils import get_logger

logger = get_logger(__name__)


def load_ocel(path: Path) -> Any:
    validate_input_path(path)
    ext = path.suffix.lower()
    if ext == ".json":
        ocel = pm4py.read_ocel2_json(str(path))
    elif ext == ".xml":
        ocel = pm4py.read_ocel2_xml(str(path))
    elif ext == ".sqlite":
        ocel = pm4py.read_ocel2_sqlite(str(path))
    else:
        raise ValueError(f"Unsupported OCEL format: {ext}. Use .json, .xml, or .sqlite.")
    logger.info("Loaded OCEL from %s", path)
    return ocel


def extract_ocel_objects(ocel: Any) -> list[str]:
    return list(ocel.objects["ocel:oid"])


def extract_ocel_events(ocel: Any) -> Any:
    return ocel.events
