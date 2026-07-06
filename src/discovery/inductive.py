from __future__ import annotations

from typing import Any

import pandas as pd
import pm4py
from pm4py.algo.discovery.inductive import algorithm as inductive_miner

from src.utils.cache import cached_discovery
from src.utils.log_utils import get_logger

logger = get_logger(__name__)

_VARIANTS = {
    "im": inductive_miner.Variants.IM,
    "imf": inductive_miner.Variants.IMf,
    "imd": inductive_miner.Variants.IMd,
}


@cached_discovery()
def discover_inductive(
    df: pd.DataFrame,
    noise_threshold: float = 0.0,
    variant: str = "im",
) -> tuple[Any, Any, Any]:
    """Discover a Petri net using the Inductive Miner.

    variant: "im" (exact), "imf" (noise-tolerant), or "imd" (directly-follows
    based -- discovers from a typed DFG instead of the full log, much cheaper
    on large event logs).
    """
    variant_key = variant.lower()
    im_variant = _VARIANTS.get(variant_key)
    if im_variant is None:
        raise ValueError(f"Unknown inductive miner variant: {variant!r}. Use 'im', 'imf', or 'imd'.")

    log = pm4py.format_dataframe(df, case_id="case:concept:name", activity_key="concept:name", timestamp_key="time:timestamp")
    parameters: dict[str, Any] = {"noise_threshold": noise_threshold}
    source = pm4py.discover_dfg_typed(log) if im_variant is inductive_miner.Variants.IMd else log

    process_tree = inductive_miner.apply(source, variant=im_variant, parameters=parameters)
    net, im, fm = pm4py.convert_to_petri_net(process_tree)
    logger.info(
        "Inductive miner (%s, noise=%.2f): %d places, %d transitions",
        variant_key,
        noise_threshold,
        len(net.places),
        len(net.transitions),
    )
    return net, im, fm
