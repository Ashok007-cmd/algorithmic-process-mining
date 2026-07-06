from __future__ import annotations

from typing import Any

import pandas as pd
import pm4py

from src.utils.cache import cached_discovery
from src.utils.log_utils import get_logger

logger = get_logger(__name__)


@cached_discovery()
def discover_dfg(df: pd.DataFrame) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    log = pm4py.format_dataframe(df, case_id="case:concept:name", activity_key="concept:name", timestamp_key="time:timestamp")
    dfg, sa, ea = pm4py.discover_dfg(log)
    logger.info("DFG: %d edges, %d start activities, %d end activities", len(dfg), len(sa), len(ea))
    return dfg, sa, ea


@cached_discovery()
def discover_dfg_petri(
    df: pd.DataFrame,
) -> tuple[Any, Any, Any]:
    log = pm4py.format_dataframe(df, case_id="case:concept:name", activity_key="concept:name", timestamp_key="time:timestamp")
    net, im, fm = pm4py.discover_petri_net_ilp(log)
    logger.info("DFG petri net: %d places, %d transitions", len(net.places), len(net.transitions))
    return net, im, fm
