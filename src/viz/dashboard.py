"""Streamlit dashboard for process mining visualisation."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.analysis.bottlenecks import find_bottlenecks
from src.analysis.kpis import compute_cycle_time
from src.analysis.variants import compute_variants
from src.config import config
from src.data.generators.synthetic import generate_o2c_log, generate_p2p_log
from src.discovery.inductive import discover_inductive
from src.viz import charts
from src.viz.petri_render import VisualizationUnavailableError, render_petri

st.set_page_config(page_title="Process Mining Dashboard", layout="wide")


@st.cache_data(show_spinner=False)
def generate_data(process: str, n_cases: int, noise: float, seed: int) -> pd.DataFrame:
    fn = generate_o2c_log if process == "O2C" else generate_p2p_log
    return fn(n_cases=n_cases, noise_level=noise, seed=seed)


def load_data() -> pd.DataFrame:
    process = st.sidebar.selectbox("Process", ["O2C", "P2P"])
    n_cases = st.sidebar.slider("Cases", 10, 500, 100)
    noise = st.sidebar.slider("Noise", 0.0, 1.0, 0.2)
    seed = st.sidebar.number_input("Seed", 0, 9999, 42)
    st.sidebar.button("Generate / Reload")
    df = generate_data(process, n_cases, noise, int(seed))
    st.session_state["df"] = df
    st.session_state["process"] = process
    return df


@st.cache_resource(show_spinner=False)
def get_process_model(df: pd.DataFrame) -> tuple[Any, Any, Any]:
    return discover_inductive(
        df,
        noise_threshold=config.discovery.noise_threshold,
        variant=config.discovery.variant,
    )


def main() -> None:
    st.title("Process Mining Dashboard")

    df = load_data()
    st.sidebar.success(f"Loaded: {len(df)} events, {df['case:concept:name'].nunique()} cases")

    with st.spinner("Discovering process model..."):
        try:
            net, im, fm = get_process_model(df)
        except Exception as e:
            st.error(f"Error discovering process model: {e}")
            return

    tab1, tab2, tab3, tab4 = st.tabs(["Model", "KPIs", "Variants", "Bottlenecks"])

    with tab1:
        st.subheader("Discovered Petri Net")
        try:
            gviz = render_petri(net, im, fm)
            st.graphviz_chart(gviz if isinstance(gviz, str) else str(gviz))
        except VisualizationUnavailableError:
            st.info("Petri net visualization requires the Graphviz system package ('dot') to be installed.")

    with tab2:
        st.subheader("Cycle Time Distribution")
        cycle = compute_cycle_time(df)
        fig = charts.plot_cycle_time_distribution(cycle)
        st.plotly_chart(fig, width="stretch")

        st.subheader("Activity Frequency")
        fig2 = charts.plot_activity_frequency(df)
        st.plotly_chart(fig2, width="stretch")

    with tab3:
        st.subheader("Variant Distribution")
        variants = compute_variants(df)
        fig3 = charts.plot_variant_distribution(variants, top_n=config.analysis.top_variants)
        st.plotly_chart(fig3, width="stretch")
        st.dataframe(variants, width="stretch")

    with tab4:
        st.subheader("Bottleneck Activities")
        bottlenecks = find_bottlenecks(df, threshold_percentile=config.analysis.bottleneck_percentile)
        st.dataframe(bottlenecks, width="stretch")

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Algorithmic Process Mining**")


if __name__ == "__main__":  # pragma: no cover
    main()
