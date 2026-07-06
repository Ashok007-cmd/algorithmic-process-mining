from __future__ import annotations

from typing import Any

import pandas as pd
import pm4py

from src.utils.log_utils import get_logger

logger = get_logger(__name__)


def check_alignments(
    df: pd.DataFrame,
    net: Any,
    initial_marking: Any,
    final_marking: Any,
    max_alignments: int = 0,
) -> dict[str, Any]:
    """Compute alignment-based conformance.

    max_alignments: if > 0 and the log has more cases than this, a random
    sample of that many cases is aligned instead of the full log. Alignment
    computation is worst-case exponential in trace length, so this bounds
    cost on large logs at the expense of statistical precision.
    """
    log = pm4py.format_dataframe(df, case_id="case:concept:name", activity_key="concept:name", timestamp_key="time:timestamp")

    total_cases = log["case:concept:name"].nunique()
    if max_alignments > 0 and total_cases > max_alignments:
        sampled_case_ids = log["case:concept:name"].drop_duplicates().sample(n=max_alignments, random_state=42)
        log = log[log["case:concept:name"].isin(sampled_case_ids)]
        logger.info("Sampling %d/%d cases for alignment computation", max_alignments, total_cases)

    fitness = pm4py.fitness_alignments(log, net, initial_marking, final_marking)
    cases_considered = log["case:concept:name"].nunique()
    fitted = round(fitness["percentage_of_fitting_traces"] / 100 * cases_considered)
    stats = {
        "total_cases": cases_considered,
        "fitted_cases": fitted,
        "non_fitted_cases": cases_considered - fitted,
        "fitness": round(fitness["log_fitness"], 4),
        "average_trace_fitness": round(fitness["average_trace_fitness"], 4),
    }
    logger.info("Alignments: fitness=%.4f (%d/%d fully fit)", stats["fitness"], fitted, cases_considered)
    return stats
