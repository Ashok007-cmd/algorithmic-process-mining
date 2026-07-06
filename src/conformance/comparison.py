from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pm4py

from src.conformance import alignments, token_replay
from src.utils.log_utils import get_logger

logger = get_logger(__name__)


def compare_methods(
    df: pd.DataFrame,
    net: Any,
    initial_marking: Any,
    final_marking: Any,
) -> dict[str, Any]:
    logger.info("Comparing conformance methods")
    tr_stats = token_replay.check_token_replay(df, net, initial_marking, final_marking)
    al_stats = alignments.check_alignments(df, net, initial_marking, final_marking)
    comparison = {
        "token_replay": tr_stats,
        "alignments": al_stats,
        "delta_fitness": round(al_stats["fitness"] - tr_stats["fitness"], 4),
    }
    logger.info("Comparison: delta_fitness=%.4f", comparison["delta_fitness"])
    return comparison


def load_normative_model(model_path: Path | str) -> tuple[Any, Any, Any]:
    """Load a normative (to-be / SOP) Petri net from a PNML file."""
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Normative model not found: {path}")
    net, im, fm = pm4py.read_pnml(str(path))
    logger.info("Loaded normative model %s: %d places, %d transitions", path, len(net.places), len(net.transitions))
    return net, im, fm


def compare_to_normative(
    df: pd.DataFrame,
    model_path: Path | str,
) -> dict[str, Any]:
    """As-is vs to-be conformance: compare an event log against a normative
    (to-be / SOP) model loaded from a PNML file, rather than a model freshly
    discovered from the same log.
    """
    net, im, fm = load_normative_model(model_path)
    result = compare_methods(df, net, im, fm)
    result["normative_model"] = str(model_path)
    return result
