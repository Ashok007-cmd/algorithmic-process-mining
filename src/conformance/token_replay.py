from __future__ import annotations

from typing import Any

import pandas as pd
import pm4py

from src.utils.log_utils import get_logger

logger = get_logger(__name__)


def check_token_replay(
    df: pd.DataFrame,
    net: Any,
    initial_marking: Any,
    final_marking: Any,
) -> dict[str, Any]:
    log = pm4py.format_dataframe(df, case_id="case:concept:name", activity_key="concept:name", timestamp_key="time:timestamp")
    result = pm4py.conformance_diagnostics_token_based_replay(log, net, initial_marking, final_marking)
    fitted = sum(1 for r in result if r["trace_is_fit"])
    total = len(result)
    fitness = fitted / total if total > 0 else 0.0
    stats = {
        "total_cases": total,
        "fitted_cases": fitted,
        "non_fitted_cases": total - fitted,
        "fitness": round(fitness, 4),
    }
    logger.info("Token-replay: fitness=%.4f (%d/%d)", fitness, fitted, total)
    return stats
