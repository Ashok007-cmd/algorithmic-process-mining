from __future__ import annotations

from unittest.mock import patch

import pytest

from src.discovery.dfg import discover_dfg
from src.discovery.heuristics import discover_heuristics_net
from src.discovery.inductive import discover_inductive
from src.viz.petri_render import VisualizationUnavailableError, render_dfg, render_heuristics_net, render_petri


class TestRenderPetri:
    def test_renders_successfully(self, o2c_df):
        net, im, fm = discover_inductive(o2c_df)
        gviz = render_petri(net, im, fm)
        assert gviz is not None

    def test_raises_visualization_error_when_graphviz_missing(self, o2c_df):
        net, im, fm = discover_inductive(o2c_df)
        with patch(
            "pm4py.visualization.petri_net.visualizer.apply",
            side_effect=FileNotFoundError("dot not found"),
        ):
            with pytest.raises(VisualizationUnavailableError):
                render_petri(net, im, fm)


class TestRenderDfg:
    def test_renders_successfully(self, o2c_df):
        dfg, sa, ea = discover_dfg(o2c_df)
        gviz = render_dfg(dfg, sa, ea)
        assert gviz is not None

    def test_trims_to_max_nodes(self, o2c_df):
        dfg, sa, ea = discover_dfg(o2c_df)
        gviz = render_dfg(dfg, sa, ea, max_nodes=2)
        assert gviz is not None

    def test_raises_visualization_error_when_graphviz_missing(self, o2c_df):
        dfg, sa, ea = discover_dfg(o2c_df)
        with patch(
            "pm4py.visualization.dfg.visualizer.apply",
            side_effect=FileNotFoundError("dot not found"),
        ):
            with pytest.raises(VisualizationUnavailableError):
                render_dfg(dfg, sa, ea)


class TestRenderHeuristicsNet:
    def test_renders_successfully(self, o2c_df):
        heu_net = discover_heuristics_net(o2c_df)
        gviz = render_heuristics_net(heu_net)
        assert gviz is not None

    def test_raises_visualization_error_when_graphviz_missing(self, o2c_df):
        heu_net = discover_heuristics_net(o2c_df)
        with patch(
            "pm4py.visualization.heuristics_net.visualizer.apply",
            side_effect=FileNotFoundError("dot not found"),
        ):
            with pytest.raises(VisualizationUnavailableError):
                render_heuristics_net(heu_net)
