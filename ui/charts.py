"""
ui/charts.py
Chart caching and rendering for the FMEA Risk Analyzer.
"""
from __future__ import annotations
import hashlib
import streamlit as st
import pandas as pd
from src.plotly_charts import pareto_chart_plotly, risk_heatmap_plotly


def get_or_build_charts(
    df_filtered: pd.DataFrame,
    rpn_min: int,
    sev9_only: bool,
    process_steps: list[str],
    dark: bool,
) -> tuple:
    """Return (pareto_fig, heatmap_fig) from session cache or rebuild if stale."""
    _df_hash = hashlib.md5(df_filtered.reset_index(drop=True).to_json().encode()).hexdigest()
    cache_key = (_df_hash, rpn_min, sev9_only, tuple(sorted(process_steps)), dark)

    if st.session_state.get("_chart_cache_key") != cache_key or "pareto_fig" not in st.session_state:
        if not df_filtered.empty:
            st.session_state["pareto_fig"]  = pareto_chart_plotly(df_filtered, dark=dark)
            st.session_state["heatmap_fig"] = risk_heatmap_plotly(df_filtered, dark=dark)
        else:
            st.session_state["pareto_fig"]  = None
            st.session_state["heatmap_fig"] = None
        st.session_state["_chart_cache_key"] = cache_key

    return st.session_state.get("pareto_fig"), st.session_state.get("heatmap_fig")
