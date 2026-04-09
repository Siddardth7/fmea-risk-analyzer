"""
app.py
FMEA Risk Prioritization Tool — Streamlit Web Application

Usage:
    streamlit run app.py

Features:
    - Upload CSV or Excel FMEA file (or use built-in demo dataset)
    - Color-coded ranked failure mode table (Red / Yellow / Green)
    - Interactive Plotly Pareto chart + Severity × Occurrence heatmap
    - Sidebar filters: RPN threshold slider + Severity ≥ 9 toggle
    - Critical items expander panel
    - Metric badges: High RPN count, Severity ≥ 9 count, Total failure modes

Author: Siddardth | M.S. Aerospace Engineering, UIUC
Engineering reference: AIAG FMEA-4 + AIAG/VDA FMEA Handbook (5th Ed., 2019)
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from src.rpn_engine import (
    RPN_HIGH_THRESHOLD,
    SEVERITY_HIGH_THRESHOLD,
    run_pipeline,
    validate_input,
)
from src.plotly_charts import pareto_chart_plotly, risk_heatmap_plotly
from src.exporter import export_excel, export_pdf

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="FMEA Risk Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEMO_CSV = Path(__file__).parent / "data" / "composite_panel_fmea_demo.csv"

TIER_ROW_COLORS = {
    "Red":    "background-color: #fde8e8; color: #922b21;",
    "Yellow": "background-color: #fef9e7; color: #7d6608;",
    "Green":  "background-color: #eafaf1; color: #1e8449;",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_uploaded(file) -> pd.DataFrame:
    """Load a user-uploaded file (CSV or Excel) into a DataFrame."""
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file)
    elif name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file)
    else:
        raise ValueError(f"Unsupported file type: {file.name}. Please upload .csv or .xlsx.")


def _style_table(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    """Apply row-level background colors based on Risk_Tier."""

    def row_style(row):
        tier = row.get("Risk_Tier", "Green")
        css  = TIER_ROW_COLORS.get(tier, "")
        return [css] * len(row)

    display_cols = [
        "Failure_Mode", "Process_Step", "Component",
        "Severity", "Occurrence", "Detection", "RPN",
        "Risk_Tier", "Flag_High_RPN", "Flag_High_Severity", "Flag_Action_Priority_H",
    ]
    available = [c for c in display_cols if c in df.columns]
    return df[available].style.apply(row_style, axis=1)


def _apply_filters(df: pd.DataFrame, rpn_min: int, sev9_only: bool) -> pd.DataFrame:
    """Filter the analyzed DataFrame based on sidebar controls."""
    mask = df["RPN"] >= rpn_min
    if sev9_only:
        mask = mask & (df["Severity"] >= SEVERITY_HIGH_THRESHOLD)
    return df[mask].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar():
    """Render sidebar and return (raw_df or None, rpn_min, sev9_only)."""
    st.sidebar.title("FMEA Risk Analyzer")
    st.sidebar.markdown(
        "Upload your FMEA file or use the demo dataset to explore the tool."
    )
    st.sidebar.divider()

    # --- File upload ---
    st.sidebar.subheader("📂 Data Source")
    uploaded = st.sidebar.file_uploader(
        "Upload FMEA file",
        type=["csv", "xlsx", "xls"],
        help="Provide a CSV or Excel file with columns: ID, Process_Step, Component, "
             "Function, Failure_Mode, Effect, Severity, Cause, Occurrence, "
             "Current_Control, Detection",
    )

    use_demo = st.sidebar.button(
        "Use Demo Dataset",
        help="Load the built-in composite panel FMEA demo (30 failure modes)",
        use_container_width=True,
    )

    # Persist demo preference in session state
    if use_demo:
        st.session_state["use_demo"] = True
    if uploaded:
        st.session_state["use_demo"] = False

    raw_df = None
    source_label = None

    if uploaded and not st.session_state.get("use_demo"):
        try:
            raw_df = _load_uploaded(uploaded)
            source_label = f"📄 {uploaded.name}"
        except Exception as exc:
            st.sidebar.error(f"Failed to load file: {exc}")
            raw_df = None
    elif st.session_state.get("use_demo"):
        raw_df = pd.read_csv(DEMO_CSV)
        source_label = "📋 Demo dataset (composite panel FMEA)"

    if source_label:
        st.sidebar.caption(source_label)

    st.sidebar.divider()

    # --- Filters (shown only when data is loaded) ---
    st.sidebar.subheader("🔧 Filters")
    rpn_min = st.sidebar.slider(
        "Minimum RPN",
        min_value=0,
        max_value=300,
        value=0,
        step=10,
        help="Show only failure modes with RPN ≥ this value",
        key="rpn_slider",
    )
    sev9_only = st.sidebar.toggle(
        "Severity ≥ 9 only",
        value=False,
        help="Show only safety-critical failure modes (Severity ≥ 9)",
        key="sev9_toggle",
    )

    st.sidebar.divider()
    st.sidebar.caption(
        "Engineering reference: AIAG FMEA-4 (4th Ed.) + "
        "AIAG/VDA FMEA Handbook (5th Ed., 2019)"
    )

    return raw_df, rpn_min, sev9_only


# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

def render_header():
    st.title("🔍 FMEA Risk Prioritization Tool")
    st.markdown(
        "Analyze failure mode effects, calculate **RPN scores**, apply **AIAG FMEA-4 flags**, "
        "and visualize risk across your process. Upload a file or load the demo dataset to begin."
    )


def render_metric_badges(df_filtered: pd.DataFrame, df_full: pd.DataFrame):
    """Render the 3 key metric badges."""
    total_modes  = len(df_filtered)
    high_rpn     = int(df_filtered["Flag_High_RPN"].sum())
    high_sev     = int(df_filtered["Flag_High_Severity"].sum())
    action_h     = int(df_filtered["Flag_Action_Priority_H"].sum())
    red_count    = int((df_filtered["Risk_Tier"] == "Red").sum())
    yellow_count = int((df_filtered["Risk_Tier"] == "Yellow").sum())
    green_count  = int((df_filtered["Risk_Tier"] == "Green").sum())

    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    col1.metric("Total Modes",      total_modes)
    col2.metric("🔴 Red",           red_count,    help="RPN > 100 or Severity ≥ 9")
    col3.metric("🟡 Yellow",        yellow_count, help="RPN 50–100")
    col4.metric("🟢 Green",         green_count,  help="RPN < 50")
    col5.metric("High RPN (>100)",  high_rpn,     help="Flag_High_RPN = True")
    col6.metric("Severity ≥ 9",     high_sev,     help="Safety-critical per AIAG")
    col7.metric("Action Priority H",action_h,     help="RPN ≥ 200 or Severity ≥ 9")


def render_table(df_filtered: pd.DataFrame):
    st.subheader("📋 Ranked Failure Mode Table")
    if df_filtered.empty:
        st.info("No failure modes match the current filter settings.")
        return
    st.dataframe(
        _style_table(df_filtered),
        use_container_width=True,
        height=420,
    )
    st.caption(
        f"{len(df_filtered)} failure mode(s) shown. "
        "Rows: 🔴 Red = immediate action | 🟡 Yellow = recommended | 🟢 Green = monitor"
    )


def render_charts(pareto_fig, heatmap_fig):
    if pareto_fig is None or heatmap_fig is None:
        st.info("Charts will appear once data matches the current filters.")
        return

    st.subheader("📊 Risk Visualizations")
    tab_pareto, tab_heatmap = st.tabs(["Pareto Chart", "Risk Heatmap"])

    with tab_pareto:
        st.plotly_chart(pareto_fig, use_container_width=True)

    with tab_heatmap:
        st.plotly_chart(heatmap_fig, use_container_width=True)


def render_export_buttons(df: pd.DataFrame, pareto_fig, heatmap_fig):
    st.subheader("📥 Export Report")
    col_xl, col_pdf, _ = st.columns([1, 1, 3])

    with col_xl:
        xl_bytes = export_excel(df)
        st.download_button(
            label="📊 Download Excel",
            data=xl_bytes,
            file_name="fmea_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col_pdf:
        if pareto_fig is not None and heatmap_fig is not None:
            pdf_bytes = export_pdf(df, pareto_fig, heatmap_fig)
            st.download_button(
                label="📄 Download PDF",
                data=pdf_bytes,
                file_name="fmea_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.button("📄 Download PDF", disabled=True, use_container_width=True,
                      help="PDF requires at least one row in the filtered table")


def render_critical_panel(df_filtered: pd.DataFrame):
    """Expander showing only flagged (critical) failure modes."""
    critical = df_filtered[df_filtered["Flag_Action_Priority_H"] == True]  # noqa: E712

    label = (
        f"⚠️ Critical Failure Modes — Action Priority H  ({len(critical)} item{'s' if len(critical) != 1 else ''})"
    )

    with st.expander(label, expanded=len(critical) > 0):
        if critical.empty:
            st.info("No critical failure modes under current filters.")
        else:
            st.markdown(
                "These failure modes have **RPN ≥ 200 or Severity ≥ 9** and require "
                "immediate corrective action per AIAG FMEA-4."
            )
            display_cols = [
                c for c in
                ["Failure_Mode", "Process_Step", "Severity", "Occurrence",
                 "Detection", "RPN", "Risk_Tier"]
                if c in critical.columns
            ]
            st.dataframe(
                critical[display_cols].reset_index(drop=True),
                use_container_width=True,
            )


# ---------------------------------------------------------------------------
# Landing page (no data loaded)
# ---------------------------------------------------------------------------

def render_landing():
    st.info(
        "👈  Upload a CSV/Excel file or click **Use Demo Dataset** in the sidebar to begin."
    )
    with st.expander("📐 Required CSV/Excel schema"):
        st.markdown("""
| Column | Type | Description |
|---|---|---|
| `ID` | int | Unique row identifier |
| `Process_Step` | str | Manufacturing or process step name |
| `Component` | str | Part or sub-assembly |
| `Function` | str | Intended function of the component |
| `Failure_Mode` | str | How the component can fail |
| `Effect` | str | Consequence of the failure |
| `Severity` | int (1–10) | Severity of the effect (AIAG scale) |
| `Cause` | str | Root cause of the failure mode |
| `Occurrence` | int (1–10) | Likelihood of occurrence |
| `Current_Control` | str | Existing controls in place |
| `Detection` | int (1–10) | Ability to detect before reaching customer |

**RPN = Severity × Occurrence × Detection** (range 1–1000)
        """)


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------

def main():
    render_header()

    raw_df, rpn_min, sev9_only = render_sidebar()

    if raw_df is None:
        render_landing()
        return

    # --- Validate & run pipeline ---
    try:
        validate_input(raw_df)
    except ValueError as exc:
        st.error(f"**Input validation failed:** {exc}")
        st.stop()

    try:
        df_analyzed = run_pipeline(raw_df)
    except (ValueError, KeyError) as exc:
        st.error(f"**Pipeline error:** {exc}")
        st.stop()

    # --- Apply filters ---
    df_filtered = _apply_filters(df_analyzed, rpn_min, sev9_only)

    # --- Build charts once; cache in session_state keyed to filter state ---
    _cache_key = (rpn_min, sev9_only, len(df_filtered))
    if st.session_state.get("_chart_cache_key") != _cache_key or "pareto_fig" not in st.session_state:
        if not df_filtered.empty:
            st.session_state["pareto_fig"]  = pareto_chart_plotly(df_filtered)
            st.session_state["heatmap_fig"] = risk_heatmap_plotly(df_filtered)
        else:
            st.session_state["pareto_fig"]  = None
            st.session_state["heatmap_fig"] = None
        st.session_state["_chart_cache_key"] = _cache_key

    pareto_fig  = st.session_state.get("pareto_fig")
    heatmap_fig = st.session_state.get("heatmap_fig")

    # --- Render UI ---
    render_metric_badges(df_filtered, df_analyzed)
    st.divider()

    left_col, right_col = st.columns([1.1, 1], gap="large")

    with left_col:
        render_table(df_filtered)

    with right_col:
        render_charts(pareto_fig, heatmap_fig)

    st.divider()
    render_critical_panel(df_filtered)
    st.divider()
    render_export_buttons(df_filtered, pareto_fig, heatmap_fig)


if __name__ == "__main__":
    main()
