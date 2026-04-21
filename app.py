"""
app.py
FMEA Risk Prioritization Tool — Streamlit Web Application

Author: Siddardth | M.S. Aerospace Engineering, UIUC
Engineering reference: AIAG FMEA-4 + AIAG/VDA FMEA Handbook (5th Ed., 2019)
"""

import hashlib
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
from src.exporter import export_excel, export_pdf, _sanitize_for_export

# ---------------------------------------------------------------------------
# Page config
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

DARK_TIER_ROW_COLORS = {
    "Red":    "background-color: #3d1515; color: #ff8a80;",
    "Yellow": "background-color: #332500; color: #ffd54f;",
    "Green":  "background-color: #0d2e1a; color: #69f0ae;",
}

# ---------------------------------------------------------------------------
# CSS injection
# ---------------------------------------------------------------------------

_BASE_CSS = """
<style>
div[data-testid="metric-container"] {
    border-radius: 10px;
    padding: 14px 18px;
    border: 1px solid rgba(128,128,128,0.2);
    transition: box-shadow 0.2s;
}
div[data-testid="metric-container"]:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.12);
}
.stTabs [data-baseweb="tab"] {
    font-size: 15px;
    font-weight: 500;
    padding: 10px 20px;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
}
</style>
"""

_DARK_CSS = """
<style>
.stApp { background-color: #0e1117 !important; }
section[data-testid="stSidebar"] { background-color: #161b27 !important; }
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] small { color: #c9d1d9 !important; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: #e6edf3 !important; }
.stApp p, .stApp li, .stApp span { color: #c9d1d9 !important; }
div[data-testid="metric-container"] {
    background-color: #161b27 !important;
    border-color: #30363d !important;
}
div[data-testid="stMetricLabel"] p { color: #8b949e !important; }
div[data-testid="stMetricValue"] { color: #58a6ff !important; }
.stTabs [data-baseweb="tab-list"] { background-color: #0e1117 !important; border-bottom: 1px solid #30363d !important; }
.stTabs [data-baseweb="tab"] { color: #8b949e !important; }
.stTabs [aria-selected="true"] { color: #58a6ff !important; border-bottom: 2px solid #58a6ff !important; }
.streamlit-expanderHeader { background-color: #161b27 !important; color: #e6edf3 !important; }
.stCaption p { color: #8b949e !important; }
hr { border-color: #30363d !important; }
div[data-testid="stInfo"] { background-color: #1c2433 !important; border-color: #30363d !important; }
div[data-testid="stInfo"] p { color: #c9d1d9 !important; }
div[data-testid="stAlert"] p { color: #c9d1d9 !important; }
.stDownloadButton > button {
    background-color: #21262d !important;
    border-color: #30363d !important;
    color: #c9d1d9 !important;
}
.stDownloadButton > button:hover {
    background-color: #30363d !important;
    border-color: #58a6ff !important;
}
</style>
"""


def _inject_css(dark: bool) -> None:
    st.markdown(_BASE_CSS, unsafe_allow_html=True)
    if dark:
        st.markdown(_DARK_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_uploaded(file) -> pd.DataFrame:
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file)
    elif name.endswith(".xlsx"):
        return pd.read_excel(file)
    else:
        raise ValueError(f"Unsupported file type: {file.name}. Please upload .csv or .xlsx.")


def _style_table(df: pd.DataFrame, dark: bool) -> pd.io.formats.style.Styler:
    colors = DARK_TIER_ROW_COLORS if dark else TIER_ROW_COLORS

    def row_style(row):
        return [colors.get(row.get("Risk_Tier", "Green"), "")] * len(row)

    display_cols = [
        "Failure_Mode", "Process_Step", "Component",
        "Severity", "Occurrence", "Detection", "RPN",
        "Risk_Tier", "Flag_High_RPN", "Flag_High_Severity", "Flag_Action_Priority_H",
    ]
    available = [c for c in display_cols if c in df.columns]
    return df[available].style.apply(row_style, axis=1)


def _apply_filters(
    df: pd.DataFrame,
    rpn_min: int,
    sev9_only: bool,
    process_steps: list,
) -> pd.DataFrame:
    mask = df["RPN"] >= rpn_min
    if sev9_only:
        mask = mask & (df["Severity"] >= SEVERITY_HIGH_THRESHOLD)
    if process_steps:
        mask = mask & df["Process_Step"].isin(process_steps)
    return df[mask].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar():
    """Render sidebar controls. Returns (raw_df, rpn_min, sev9_only, dark)."""
    st.sidebar.title("FMEA Risk Analyzer")
    st.sidebar.markdown("Upload your FMEA file or load the demo dataset to begin.")
    st.sidebar.divider()

    dark = st.sidebar.toggle(
        "🌙  Dark Mode",
        value=st.session_state.get("dark_mode", False),
        key="dark_mode",
    )

    st.sidebar.divider()
    st.sidebar.subheader("📂  Data Source")

    uploaded = st.sidebar.file_uploader(
        "Upload FMEA file",
        type=["csv", "xlsx"],
        help=(
            "CSV or Excel with 11 columns: ID, Process_Step, Component, "
            "Function, Failure_Mode, Effect, Severity, Cause, "
            "Occurrence, Current_Control, Detection"
        ),
    )
    use_demo = st.sidebar.button(
        "▶  Use Demo Dataset",
        help="Load 30-row composite panel aerospace FMEA",
        use_container_width=True,
    )

    if use_demo:
        st.session_state["use_demo"] = True
    if uploaded:
        st.session_state["use_demo"] = False

    raw_df = None
    source_label = None

    if uploaded and not st.session_state.get("use_demo"):
        try:
            raw_df = _load_uploaded(uploaded)
            source_label = f"📄  {uploaded.name}"
        except Exception as exc:
            st.sidebar.error(f"Failed to load: {exc}")
    elif st.session_state.get("use_demo"):
        raw_df = pd.read_csv(DEMO_CSV)
        source_label = "📋  Demo: composite panel FMEA (30 rows)"

    if source_label:
        st.sidebar.caption(source_label)

    st.sidebar.divider()
    st.sidebar.subheader("🔧  Filters")

    _rpn_max = int(st.session_state.get("_dataset_rpn_max", 1000))
    rpn_min = st.sidebar.slider(
        "Minimum RPN",
        min_value=0,
        max_value=max(_rpn_max, 10),
        value=min(st.session_state.get("rpn_slider", 0), _rpn_max),
        step=10,
        help="Show only failure modes with RPN ≥ this value (max reflects your dataset)",
        key="rpn_slider",
    )
    sev9_only = st.sidebar.toggle(
        "Severity ≥ 9 only",
        value=False,
        help="Show only safety-critical failure modes",
        key="sev9_toggle",
    )

    return raw_df, rpn_min, sev9_only, dark


def render_process_filter(df: pd.DataFrame) -> list:
    """Render process step multiselect in sidebar after data is loaded."""
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


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

def render_header():
    st.title("🔍  FMEA Risk Prioritization Tool")
    st.markdown(
        "Analyze failure modes, calculate **RPN scores**, apply **AIAG FMEA-4 criticality flags**, "
        "and visualize risk concentration across your manufacturing process."
    )


# ---------------------------------------------------------------------------
# Metric badges
# ---------------------------------------------------------------------------

def render_metric_badges(df: pd.DataFrame) -> None:
    total    = len(df)
    red      = int((df["Risk_Tier"] == "Red").sum())
    yellow   = int((df["Risk_Tier"] == "Yellow").sum())
    green    = int((df["Risk_Tier"] == "Green").sum())
    high_rpn = int(df["Flag_High_RPN"].sum())
    high_sev = int(df["Flag_High_Severity"].sum())
    action_h = int(df["Flag_Action_Priority_H"].sum())

    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    c1.metric("Total Modes",       total)
    c2.metric("🔴  Red",           red,      help="RPN > 100 OR Severity ≥ 9 — immediate action")
    c3.metric("🟡  Yellow",        yellow,   help="RPN 50–100 — corrective action recommended")
    c4.metric("🟢  Green",         green,    help="RPN < 50 — monitor")
    c5.metric("High RPN (>100)",   high_rpn, help="Flag_High_RPN = True")
    c6.metric("Severity ≥ 9",      high_sev, help="Safety-critical per AIAG FMEA-4")
    c7.metric("Action Priority H", action_h, help="RPN ≥ 200 OR Severity ≥ 9")


# ---------------------------------------------------------------------------
# Auto-insights
# ---------------------------------------------------------------------------

def render_insights(df: pd.DataFrame) -> None:
    if df.empty or len(df) < 2:
        return

    total_rpn  = df["RPN"].sum()
    top_n      = min(3, len(df))
    top_pct    = df.nlargest(top_n, "RPN")["RPN"].sum() / total_rpn * 100 if total_rpn else 0
    top_item   = df.iloc[0]
    red_count  = int((df["Risk_Tier"] == "Red").sum())
    sev9_count = int(df["Flag_High_Severity"].sum())

    parts = [
        f"**Top {top_n} failure modes account for {top_pct:.0f}% of total RPN.**",
        f"Highest risk: **{str(top_item['Failure_Mode'])[:60]}** "
        f"(RPN = {int(top_item['RPN'])}, {top_item['Process_Step']}).",
    ]
    if red_count:
        parts.append(f"**{red_count}** item(s) in the Red tier require immediate corrective action.")
    if sev9_count:
        parts.append(f"**{sev9_count}** safety-critical failure mode(s) flagged (Severity ≥ 9).")

    st.info("  \u00a0".join(parts))


# ---------------------------------------------------------------------------
# Risk Table tab
# ---------------------------------------------------------------------------

def render_table(df: pd.DataFrame, dark: bool) -> None:
    st.subheader("📋  Ranked Failure Mode Table")
    if df.empty:
        st.info("No failure modes match the current filter settings.")
        return

    col_left, col_right = st.columns([3, 1])

    with col_left:
        st.dataframe(
            _style_table(df, dark),
            use_container_width=True,
            height=520,
        )
        st.caption(
            f"{len(df)} failure mode(s) shown  |  "
            "🔴 Red = immediate action  |  🟡 Yellow = recommended  |  🟢 Green = monitor"
        )

    with col_right:
        st.markdown("**Risk Distribution**")
        red    = int((df["Risk_Tier"] == "Red").sum())
        yellow = int((df["Risk_Tier"] == "Yellow").sum())
        green  = int((df["Risk_Tier"] == "Green").sum())
        total  = len(df)

        def _pct(n): return f"{n/total*100:.0f}%" if total else "0%"

        st.markdown(f"🔴 **Red:** {red} ({_pct(red)})")
        st.progress(red / total if total else 0, text="")
        st.markdown(f"🟡 **Yellow:** {yellow} ({_pct(yellow)})")
        st.progress(yellow / total if total else 0, text="")
        st.markdown(f"🟢 **Green:** {green} ({_pct(green)})")
        st.progress(green / total if total else 0, text="")

        st.divider()
        if total:
            avg_rpn = df["RPN"].mean()
            max_rpn = df["RPN"].max()
            total_rpn = df["RPN"].sum()
            st.markdown(f"**Avg RPN:** {avg_rpn:.0f}")
            st.markdown(f"**Max RPN:** {int(max_rpn)}")
            st.markdown(f"**Total RPN:** {int(total_rpn)}")


# ---------------------------------------------------------------------------
# Pareto chart tab
# ---------------------------------------------------------------------------

def render_pareto(pareto_fig) -> None:
    st.subheader("📊  Pareto Chart — Failure Modes Ranked by RPN")
    st.markdown(
        "Bars sorted highest to lowest RPN. The **cumulative % line** shows where 80% of total "
        "risk is concentrated. Focus corrective action resources on failure modes to the **left** "
        "of the 80% threshold."
    )
    if pareto_fig is None:
        st.info("No data to display under current filters.")
        return
    st.plotly_chart(pareto_fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Heatmap tab
# ---------------------------------------------------------------------------

def render_heatmap(heatmap_fig) -> None:
    st.subheader("🗺️  Risk Heatmap — Severity × Occurrence")
    st.markdown(
        "Each cell shows the **count of failure modes** with that Severity × Occurrence combination. "
        "Color reflects the worst Risk Tier in the cell. Clustering in the **top-right** corner "
        "(high S, high O) indicates systemic process problems."
    )
    if heatmap_fig is None:
        st.info("No data to display under current filters.")
        return
    st.plotly_chart(heatmap_fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Critical items tab
# ---------------------------------------------------------------------------

def render_critical_panel(df: pd.DataFrame) -> None:
    critical = df[df["Flag_Action_Priority_H"] == True]  # noqa: E712

    if critical.empty:
        st.success("✅  No critical failure modes under current filters.")
        return

    st.warning(
        f"**{len(critical)} failure mode(s)** have RPN ≥ 200 or Severity ≥ 9 and require "
        "immediate corrective action per AIAG FMEA-4."
    )

    display_cols = [
        c for c in
        ["Failure_Mode", "Process_Step", "Component", "Cause",
         "Severity", "Occurrence", "Detection", "RPN", "Risk_Tier",
         "Current_Control"]
        if c in critical.columns
    ]
    st.dataframe(critical[display_cols].reset_index(drop=True), use_container_width=True)

    # Action guidance
    with st.expander("📌  What to do with these items"):
        st.markdown("""
**AIAG FMEA-4 Corrective Action Process:**
1. **Assign ownership** — every Action Priority H item needs a named engineer responsible
2. **Root cause analysis** — use 5-Why or Ishikawa diagram to identify the true cause
3. **Define actions** — target reducing Occurrence (process change) or improving Detection (control upgrade)
4. **Set a deadline** — action plans without dates don't get completed
5. **Re-score after action** — update S/O/D scores and verify Risk_Tier moves to Yellow or Green
6. **Document everything** — AIAG-compliant FMEA requires traceability of all corrective actions
        """)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def _export_cache_key(
    df: pd.DataFrame,
    rpn_min: int,
    sev9_only: bool,
    process_steps: list,
    export_type: str,
) -> tuple:
    """Stable cache key for export bytes — includes filtered data hash and all filter state."""
    df_hash = hashlib.md5(df.reset_index(drop=True).to_json().encode()).hexdigest()
    return (df_hash, rpn_min, sev9_only, tuple(sorted(process_steps)), export_type)


def render_export_buttons(
    df: pd.DataFrame,
    pareto_fig,
    heatmap_fig,
    rpn_min: int,
    sev9_only: bool,
    process_steps: list,
) -> None:
    st.subheader("📥  Export Report")

    col_xl, col_pdf, col_csv, _ = st.columns([1, 1, 1, 3])

    # --- Excel (lazy, cached by filtered-data hash + filter state) ---
    xl_key = _export_cache_key(df, rpn_min, sev9_only, process_steps, "excel")
    if st.session_state.get("_xl_cache_key") != xl_key:
        try:
            st.session_state["_xl_bytes"] = export_excel(df)
            st.session_state["_xl_cache_key"] = xl_key
        except Exception as exc:
            st.session_state["_xl_bytes"] = None
            st.session_state["_xl_cache_key"] = xl_key
            st.warning(f"Excel export unavailable: {exc}")

    with col_xl:
        xl_bytes = st.session_state.get("_xl_bytes")
        st.download_button(
            label="📊  Download Excel",
            data=xl_bytes or b"",
            file_name="fmea_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            disabled=xl_bytes is None,
            help="Color-coded 2-sheet workbook with metadata summary",
        )

    # --- PDF (lazy, cached by filtered-data hash + filter state) ---
    pdf_key = _export_cache_key(df, rpn_min, sev9_only, process_steps, "pdf")
    if st.session_state.get("_pdf_cache_key") != pdf_key:
        try:
            st.session_state["_pdf_bytes"] = export_pdf(df)
            st.session_state["_pdf_cache_key"] = pdf_key
        except Exception as exc:
            st.session_state["_pdf_bytes"] = None
            st.session_state["_pdf_cache_key"] = pdf_key
            st.warning(f"PDF export unavailable: {exc}")

    with col_pdf:
        pdf_bytes = st.session_state.get("_pdf_bytes")
        st.download_button(
            label="📄  Download PDF",
            data=pdf_bytes or b"",
            file_name="fmea_report.pdf",
            mime="application/pdf",
            use_container_width=True,
            disabled=pdf_bytes is None,
            help="3-page A4 landscape: table + Pareto + Heatmap",
        )

    # --- CSV (always fresh — cheap operation, no caching needed) ---
    with col_csv:
        st.download_button(
            label="📋  Download CSV",
            data=_sanitize_for_export(df).to_csv(index=False).encode("utf-8"),
            file_name="fmea_analysis.csv",
            mime="text/csv",
            use_container_width=True,
            help="Full analyzed dataset with all calculated columns",
        )


# ---------------------------------------------------------------------------
# Landing page
# ---------------------------------------------------------------------------

def render_landing() -> None:
    st.info("👈  Upload a CSV/Excel file or click **Use Demo Dataset** in the sidebar to begin.")

    col1, col2 = st.columns(2)

    with col1:
        with st.expander("📐  Required CSV/Excel schema"):
            st.markdown("""
| Column | Type | Description |
|---|---|---|
| `ID` | int | Unique row identifier |
| `Process_Step` | str | Manufacturing process step name |
| `Component` | str | Part or sub-assembly |
| `Function` | str | Intended function |
| `Failure_Mode` | str | How it can fail |
| `Effect` | str | Consequence of the failure |
| `Severity` | int (1–10) | Severity of effect (AIAG scale) |
| `Cause` | str | Root cause |
| `Occurrence` | int (1–10) | Likelihood of occurrence |
| `Current_Control` | str | Existing controls |
| `Detection` | int (1–10) | Ability to detect |

**RPN = Severity × Occurrence × Detection** (range 1–1000)
""")

    with col2:
        with st.expander("📖  How RPN and Risk Tiers work"):
            st.markdown("""
**Risk Priority Number (RPN)** is the core metric of Process FMEA:

`RPN = Severity × Occurrence × Detection`

Each factor is scored 1–10 per AIAG FMEA-4:
- **Severity:** How bad is the effect? (10 = safety failure without warning)
- **Occurrence:** How likely is the cause? (10 = almost certain)
- **Detection:** How well do controls catch it? (10 = no detection possible)

**Risk Tiers:**
| Tier | Condition | Action Required |
|---|---|---|
| 🔴 Red | RPN > 100 OR Severity ≥ 9 | Immediate corrective action |
| 🟡 Yellow | RPN 50–100 | Action recommended |
| 🟢 Green | RPN < 50 | Monitor |
""")


# ---------------------------------------------------------------------------
# Validation summary panel
# ---------------------------------------------------------------------------

def render_validation_summary(df: pd.DataFrame) -> None:
    """Show a compact dataset health panel immediately after upload."""
    score_cols = ["Severity", "Occurrence", "Detection"]
    text_cols  = ["Failure_Mode", "Effect", "Cause"]
    warnings: list[str] = []

    for col in score_cols:
        if col in df.columns:
            if (df[col] == 10).sum() > 0:
                warnings.append(f"{int((df[col] == 10).sum())} row(s) have {col} = 10 (maximum score)")
            if (df[col] == 1).sum() > 0:
                warnings.append(f"{int((df[col] == 1).sum())} row(s) have {col} = 1 (minimum score)")

    for col in text_cols:
        if col in df.columns:
            long = int((df[col].str.len() > 120).sum())
            if long > 0:
                warnings.append(f"{long} row(s) have long '{col}' text (>120 chars — may truncate in PDF)")

    with st.expander("📋  Dataset Health", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("Rows loaded",      len(df))
        c2.metric("Columns present",  len(df.columns))
        c3.metric("Warnings",         len(warnings))
        if warnings:
            for w in warnings:
                st.caption(f"⚠️ {w}")
        else:
            st.caption("✅ No data quality warnings detected.")


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------

def main() -> None:
    raw_df, rpn_min, sev9_only, dark = render_sidebar()

    _inject_css(dark)
    render_header()

    if raw_df is None:
        st.sidebar.divider()
        st.sidebar.caption(
            "Engineering ref: AIAG FMEA-4 (4th Ed.) + "
            "AIAG/VDA FMEA Handbook (5th Ed., 2019)"
        )
        render_landing()
        return

    # --- Validate ---
    try:
        validate_input(raw_df)
    except ValueError as exc:
        st.error(f"**Input validation failed:** {exc}")
        st.stop()

    # --- Pipeline ---
    try:
        df_analyzed = run_pipeline(raw_df)
        st.session_state["_dataset_rpn_max"] = int(df_analyzed["RPN"].max())
    except (ValueError, KeyError) as exc:
        st.error(f"**Pipeline error:** {exc}")
        st.stop()

    render_validation_summary(df_analyzed)

    # --- Process step filter (sidebar, needs data first) ---
    process_steps = render_process_filter(df_analyzed)

    # Sidebar footer
    st.sidebar.divider()
    st.sidebar.caption(
        "Engineering ref: AIAG FMEA-4 (4th Ed.) + "
        "AIAG/VDA FMEA Handbook (5th Ed., 2019)"
    )

    # --- Apply filters ---
    df_filtered = _apply_filters(df_analyzed, rpn_min, sev9_only, process_steps)

    # --- Build / cache charts ---
    _df_hash = hashlib.md5(df_filtered.reset_index(drop=True).to_json().encode()).hexdigest()
    _cache_key = (_df_hash, rpn_min, sev9_only, tuple(sorted(process_steps)), dark)
    if st.session_state.get("_chart_cache_key") != _cache_key or "pareto_fig" not in st.session_state:
        if not df_filtered.empty:
            st.session_state["pareto_fig"]  = pareto_chart_plotly(df_filtered, dark=dark)
            st.session_state["heatmap_fig"] = risk_heatmap_plotly(df_filtered, dark=dark)
        else:
            st.session_state["pareto_fig"]  = None
            st.session_state["heatmap_fig"] = None
        st.session_state["_chart_cache_key"] = _cache_key

    pareto_fig  = st.session_state.get("pareto_fig")
    heatmap_fig = st.session_state.get("heatmap_fig")

    # --- Dashboard ---
    render_metric_badges(df_filtered)
    render_insights(df_filtered)
    st.divider()

    tab_table, tab_pareto, tab_heatmap, tab_critical = st.tabs([
        "📋  Risk Table",
        "📊  Pareto Chart",
        "🗺️  Risk Heatmap",
        "⚠️  Critical Items",
    ])

    with tab_table:
        render_table(df_filtered, dark)

    with tab_pareto:
        render_pareto(pareto_fig)

    with tab_heatmap:
        render_heatmap(heatmap_fig)

    with tab_critical:
        render_critical_panel(df_filtered)

    st.divider()
    render_export_buttons(df_filtered, pareto_fig, heatmap_fig, rpn_min, sev9_only, process_steps)


if __name__ == "__main__":
    main()
