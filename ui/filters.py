"""
ui/filters.py
Sidebar filter rendering and DataFrame filtering for the FMEA Risk Analyzer.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st


def render_rpn_slider() -> int:
    _rpn_max = int(st.session_state.get("_dataset_rpn_max", 1000))
    return st.sidebar.slider(
        "Minimum RPN",
        min_value=0,
        max_value=max(_rpn_max, 10),
        value=min(st.session_state.get("rpn_slider", 0), _rpn_max),
        step=10,
        help="Show only failure modes with RPN ≥ this value (max reflects your dataset)",
        key="rpn_slider",
    )


def render_severity_toggle() -> bool:
    return st.sidebar.toggle(
        "Severity ≥ 9 only",
        value=False,
        help="Show only safety-critical failure modes",
        key="sev9_toggle",
    )


def render_process_filter(df: pd.DataFrame) -> list[str]:
    st.sidebar.divider()
    st.sidebar.subheader("📍  Process Steps")
    all_steps = sorted(df["Process_Step"].unique().tolist())
    selected = st.sidebar.multiselect(
        "Show steps",
        options=all_steps,
        default=all_steps,
        key="process_steps",
        help="Filter to specific manufacturing process steps",
    )
    return selected if selected else all_steps


def apply_filters(
    df: pd.DataFrame,
    rpn_min: int,
    sev9_only: bool,
    process_steps: list[str],
) -> pd.DataFrame:
    filtered = df[df["RPN"] >= rpn_min]
    if sev9_only:
        filtered = filtered[filtered["Severity"] >= 9]
    if process_steps:
        filtered = filtered[filtered["Process_Step"].isin(process_steps)]
    return filtered
