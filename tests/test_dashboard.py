from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

DASHBOARD_PATH = str(Path(__file__).parent.parent / "src" / "viz" / "dashboard.py")


class TestDashboard:
    def test_dashboard_runs_without_exception(self):
        at = AppTest.from_file(DASHBOARD_PATH)
        at.run(timeout=60)
        assert not at.exception

    def test_dashboard_loads_data_and_renders_tabs(self):
        at = AppTest.from_file(DASHBOARD_PATH)
        at.run(timeout=60)
        assert not at.exception
        assert len(at.tabs) == 4
        assert any("Loaded" in s.value for s in at.sidebar.success)

    def test_dashboard_switches_process(self):
        at = AppTest.from_file(DASHBOARD_PATH)
        at.run(timeout=60)
        at.sidebar.selectbox[0].set_value("P2P").run(timeout=60)
        assert not at.exception
        assert any("Loaded" in s.value for s in at.sidebar.success)
