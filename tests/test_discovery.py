from __future__ import annotations

from src.discovery.dfg import discover_dfg, discover_dfg_petri
from src.discovery.heuristics import discover_heuristics_net, discover_heuristics_petri
from src.discovery.inductive import discover_inductive


class TestInductive:
    def test_discover_inductive(self, o2c_df):
        net, im, fm = discover_inductive(o2c_df)
        assert net is not None

    def test_discover_inductive_p2p(self, p2p_df):
        net, im, fm = discover_inductive(p2p_df)
        assert net is not None


class TestHeuristics:
    def test_discover_heuristics_net(self, o2c_df):
        heu_net = discover_heuristics_net(o2c_df)
        assert heu_net is not None

    def test_discover_heuristics_petri(self, o2c_df):
        net, im, fm = discover_heuristics_petri(o2c_df)
        assert net is not None


class TestDfg:
    def test_discover_dfg(self, o2c_df):
        dfg, sa, ea = discover_dfg(o2c_df)
        assert isinstance(dfg, dict)

    def test_discover_dfg_petri(self, o2c_df):
        net, im, fm = discover_dfg_petri(o2c_df)
        assert net is not None
