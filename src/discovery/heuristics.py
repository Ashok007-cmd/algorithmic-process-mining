from __future__ import annotations

from typing import Any

import pandas as pd
import pm4py

from src.utils.cache import cached_discovery
from src.utils.log_utils import get_logger

logger = get_logger(__name__)


@cached_discovery()
def discover_heuristics_net(
    df: pd.DataFrame,
    dependency_threshold: float = 0.5,
    and_threshold: float = 0.65,
) -> Any:
    log = pm4py.format_dataframe(df, case_id="case:concept:name", activity_key="concept:name", timestamp_key="time:timestamp")
    heu_net = pm4py.discover_heuristics_net(
        log,
        dependency_threshold=dependency_threshold,
        and_threshold=and_threshold,
    )
    logger.info("Heuristics miner discovered")
    return heu_net


@cached_discovery()
def discover_heuristics_petri(
    df: pd.DataFrame,
    dependency_threshold: float = 0.5,
    and_threshold: float = 0.65,
) -> tuple[Any, Any, Any]:
    log = pm4py.format_dataframe(df, case_id="case:concept:name", activity_key="concept:name", timestamp_key="time:timestamp")
    net, im, fm = pm4py.discover_petri_net_heuristics(
        log,
        dependency_threshold=dependency_threshold,
        and_threshold=and_threshold,
    )
    logger.info("Heuristics petri net: %d places, %d transitions", len(net.places), len(net.transitions))
    return net, im, fm
