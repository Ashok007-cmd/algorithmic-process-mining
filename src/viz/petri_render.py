from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pm4py

from src.utils.log_utils import get_logger

logger = get_logger(__name__)


class VisualizationUnavailableError(RuntimeError):
    """Raised when a diagram can't be rendered (typically a missing Graphviz 'dot' binary)."""


def _guard(step: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        logger.warning("%s failed, Graphviz may not be installed: %s", step, e)
        raise VisualizationUnavailableError(f"{step} failed -- ensure the Graphviz system package ('dot') is installed") from e


def render_petri(
    net: Any,
    initial_marking: Any,
    final_marking: Any,
    output_path: Path | None = None,
    fmt: str = "png",
) -> Any:
    from pm4py.visualization.petri_net import visualizer as pn_visualizer

    gviz = _guard(
        "Petri net rendering",
        pn_visualizer.apply,
        net,
        initial_marking,
        final_marking,
        parameters={"format": fmt},
    )
    if output_path:
        _guard(
            "Petri net export",
            pm4py.save_vis_petri_net,
            net,
            initial_marking,
            final_marking,
            str(output_path),
        )
        logger.info("Petri net saved to %s", output_path)
    return gviz


def render_dfg(
    dfg: dict[tuple[str, str], Any],
    start_activities: dict[str, Any],
    end_activities: dict[str, Any],
    output_path: Path | None = None,
    fmt: str = "png",
    max_nodes: int | None = None,
) -> Any:
    from pm4py.visualization.dfg import visualizer as dfg_visualizer

    if max_nodes is not None and max_nodes > 0:
        activities = {a for edge in dfg for a in edge}
        if len(activities) > max_nodes:
            top_edges = sorted(dfg.items(), key=lambda kv: kv[1], reverse=True)[:max_nodes]
            dfg = dict(top_edges)
            kept = {a for edge in dfg for a in edge}
            start_activities = {a: v for a, v in start_activities.items() if a in kept}
            end_activities = {a: v for a, v in end_activities.items() if a in kept}
            logger.info("DFG trimmed to top %d nodes for visualization", max_nodes)

    parameters = {
        dfg_visualizer.Variants.FREQUENCY.value.Parameters.START_ACTIVITIES: start_activities,
        dfg_visualizer.Variants.FREQUENCY.value.Parameters.END_ACTIVITIES: end_activities,
        "format": fmt,
    }
    gviz = _guard(
        "DFG rendering",
        dfg_visualizer.apply,
        dfg,
        variant=dfg_visualizer.Variants.FREQUENCY,
        parameters=parameters,
    )
    if output_path:
        _guard(
            "DFG export",
            pm4py.save_vis_dfg,
            dfg,
            start_activities,
            end_activities,
            str(output_path),
        )
        logger.info("DFG saved to %s", output_path)
    return gviz


def render_heuristics_net(
    heu_net: Any,
    output_path: Path | None = None,
) -> Any:
    from pm4py.visualization.heuristics_net import visualizer as hn_visualizer

    gviz: Any = _guard("Heuristics net rendering", hn_visualizer.apply, heu_net)
    if output_path:
        _guard("Heuristics net export", hn_visualizer.save, gviz, str(output_path))
        logger.info("Heuristics net saved to %s", output_path)
    return gviz
