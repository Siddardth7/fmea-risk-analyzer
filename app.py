"""
app.py
FMEA Risk Prioritization Tool — Streamlit Web Application

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
# Design system tokens
# ---------------------------------------------------------------------------

_LIGHT = {
    "bg":         "#F8FAFC",
    "card_bg":    "#FFFFFF",
    "border":     "#E2E8F0",
    "text_pri":   "#0F172A",
    "text_sec":   "#64748B",
    "text_muted": "#94A3B8",
    "primary":    "#2563EB",
    "red":        "#DC2626",
    "amber":      "#D97706",
    "green":      "#16A34A",
    "purple":     "#7C3AED",
    "info_bg":    "#EFF6FF",
    "info_border":"#2563EB",
    "warn_bg":    "#FFFBEB",
    "warn_border":"#D97706",
    "progress_bg":"#E2E8F0",
    "sidebar_bg": "#F1F5F9",
}

_DARK = {
    "bg":         "#0D1117",
    "card_bg":    "#161B22",
    "border":     "#30363D",
    "text_pri":   "#F0F6FC",
    "text_sec":   "#8B949E",
    "text_muted": "#6E7681",
    "primary":    "#388BFD",
    "red":        "#F85149",
    "amber":      "#D29922",
    "green":      "#3FB950",
    "purple":     "#BC8CFF",
    "info_bg":    "#1C2128",
    "info_border":"#388BFD",
    "warn_bg":    "#2D1F0E",
    "warn_border":"#D29922",
    "progress_bg":"#21262D",
    "sidebar_bg": "#161B22",
}

# ---------------------------------------------------------------------------
# CSS injection
# ---------------------------------------------------------------------------

_FONT_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
</style>
"""

_BASE_CSS = """
<style>
/* ===== TYPOGRAPHY ===== */
/* Apply Inter to named text elements only — exclude span/div to preserve
   Streamlit's icon font (icon glyphs live on <span> pseudo-elements) */
.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
.stApp p, .stApp label, .stApp button, .stApp a,
.stApp input, .stApp textarea, .stApp select,
.stApp td, .stApp th, .stApp li, .stApp small {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* ===== LAYOUT ===== */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1440px !important;
}

/* ===== HEADINGS ===== */
.stApp h1 {
    font-size: 24px !important;
    font-weight: 700 !important;
    color: #0F172A !important;
    letter-spacing: -0.01em !important;
    line-height: 1.3 !important;
}
.stApp h2, .stApp h3 {
    font-size: 16px !important;
    font-weight: 600 !important;
    color: #1E293B !important;
    margin-bottom: 0.5rem !important;
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    background-color: #F1F5F9 !important;
    border-right: 1px solid #E2E8F0 !important;
}
section[data-testid="stSidebar"] h1 {
    font-size: 15px !important;
    font-weight: 700 !important;
    color: #0F172A !important;
    letter-spacing: -0.01em !important;
}
section[data-testid="stSidebar"] .stMarkdown p {
    font-size: 12px !important;
    color: #64748B !important;
    line-height: 1.5 !important;
}
section[data-testid="stSidebar"] label {
    font-size: 12px !important;
    color: #374151 !important;
    font-weight: 500 !important;
}
section[data-testid="stSidebar"] small {
    font-size: 11px !important;
    color: #94A3B8 !important;
}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #E2E8F0 !important;
    gap: 0 !important;
    padding: 0 !important;
    margin-bottom: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 10px 20px !important;
    color: #64748B !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important;
    border-radius: 0 !important;
    transition: color 0.15s ease !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #2563EB !important;
    background: #F0F7FF !important;
}
.stTabs [aria-selected="true"] {
    color: #2563EB !important;
    border-bottom: 2px solid #2563EB !important;
    background: transparent !important;
    font-weight: 600 !important;
}

/* ===== DOWNLOAD BUTTONS ===== */
.stDownloadButton > button {
    background: #2563EB !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    padding: 9px 16px !important;
    transition: background 0.15s ease, box-shadow 0.15s ease !important;
    width: 100% !important;
    letter-spacing: 0.01em !important;
}
.stDownloadButton > button:hover {
    background: #1D4ED8 !important;
    box-shadow: 0 4px 14px rgba(37,99,235,0.3) !important;
}
.stDownloadButton > button:disabled {
    background: #CBD5E1 !important;
    color: #94A3B8 !important;
    cursor: not-allowed !important;
    box-shadow: none !important;
}

/* ===== REGULAR BUTTONS ===== */
.stButton > button {
    border: 1px solid #CBD5E1 !important;
    border-radius: 6px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #374151 !important;
    background: white !important;
    transition: all 0.15s ease !important;
    letter-spacing: 0.01em !important;
}
.stButton > button:hover {
    border-color: #2563EB !important;
    color: #2563EB !important;
    background: #EFF6FF !important;
}

/* ===== INFO/ALERT BOXES ===== */
div[data-testid="stInfo"] {
    background: #EFF6FF !important;
    border: none !important;
    border-left: 4px solid #2563EB !important;
    border-radius: 6px !important;
    padding: 12px 16px !important;
}
div[data-testid="stInfo"] p { color: #1E40AF !important; font-size: 13px !important; }

div[data-testid="stWarning"] {
    background: #FFFBEB !important;
    border: none !important;
    border-left: 4px solid #D97706 !important;
    border-radius: 6px !important;
}
div[data-testid="stWarning"] p { color: #92400E !important; font-size: 13px !important; }

div[data-testid="stSuccess"] {
    background: #F0FDF4 !important;
    border: none !important;
    border-left: 4px solid #16A34A !important;
    border-radius: 6px !important;
}
div[data-testid="stSuccess"] p { color: #14532D !important; font-size: 13px !important; }

div[data-testid="stError"] {
    background: #FEF2F2 !important;
    border: none !important;
    border-left: 4px solid #DC2626 !important;
    border-radius: 6px !important;
}

/* ===== DATA TABLE ===== */
.stDataFrame {
    border-radius: 8px !important;
    border: 1px solid #E2E8F0 !important;
    overflow: hidden !important;
}

/* ===== EXPANDER ===== */
.streamlit-expanderHeader {
    font-size: 13px !important;
    font-weight: 500 !important;
    background: #F8FAFC !important;
    border-radius: 6px !important;
    border: 1px solid #E2E8F0 !important;
    color: #374151 !important;
}

/* ===== CAPTION ===== */
.stCaption p {
    font-size: 11px !important;
    color: #94A3B8 !important;
}

/* ===== DIVIDER ===== */
hr {
    border: none !important;
    border-top: 1px solid #E2E8F0 !important;
    margin: 1.5rem 0 !important;
}

/* ===== METRIC CONTAINERS (fallback if custom HTML not rendered) ===== */
div[data-testid="metric-container"] {
    background: white !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    padding: 14px 18px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
}
div[data-testid="stMetricLabel"] p {
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    color: #64748B !important;
}
div[data-testid="stMetricValue"] {
    font-size: 28px !important;
    font-weight: 700 !important;
    color: #0F172A !important;
}
</style>
"""

_DARK_CSS = """
<style>
.stApp { background-color: #0D1117 !important; }
.stApp h1 { color: #F0F6FC !important; }
.stApp h2, .stApp h3 { color: #C9D1D9 !important; }
.stApp p, .stApp li { color: #C9D1D9 !important; }

section[data-testid="stSidebar"] {
    background-color: #161B22 !important;
    border-right-color: #30363D !important;
}
section[data-testid="stSidebar"] h1 { color: #F0F6FC !important; }
section[data-testid="stSidebar"] .stMarkdown p { color: #8B949E !important; }
section[data-testid="stSidebar"] label { color: #C9D1D9 !important; }

.stTabs [data-baseweb="tab-list"] { border-bottom-color: #30363D !important; }
.stTabs [data-baseweb="tab"] { color: #8B949E !important; }
.stTabs [data-baseweb="tab"]:hover { background: #1C2128 !important; color: #58A6FF !important; }
.stTabs [aria-selected="true"] { color: #58A6FF !important; border-bottom-color: #58A6FF !important; }

.stDownloadButton > button {
    background: #1F6FEB !important;
    color: white !important;
}
.stDownloadButton > button:hover {
    background: #388BFD !important;
    box-shadow: 0 4px 14px rgba(56,139,253,0.3) !important;
}
.stButton > button {
    background: #21262D !important;
    border-color: #30363D !important;
    color: #C9D1D9 !important;
}
.stButton > button:hover {
    border-color: #58A6FF !important;
    color: #58A6FF !important;
    background: #1C2128 !important;
}

div[data-testid="stInfo"] {
    background: #1C2128 !important;
    border-left-color: #388BFD !important;
}
div[data-testid="stInfo"] p { color: #A5C8FF !important; }
div[data-testid="stWarning"] {
    background: #2D1F0E !important;
    border-left-color: #D29922 !important;
}
div[data-testid="stWarning"] p { color: #E3B341 !important; }
div[data-testid="stSuccess"] {
    background: #0D2818 !important;
    border-left-color: #3FB950 !important;
}
div[data-testid="stSuccess"] p { color: #56D364 !important; }

.stDataFrame { border-color: #30363D !important; }
.streamlit-expanderHeader {
    background: #161B22 !important;
    border-color: #30363D !important;
    color: #C9D1D9 !important;
}
.stCaption p { color: #6E7681 !important; }
hr { border-top-color: #30363D !important; }

div[data-testid="metric-container"] {
    background-color: #161B22 !important;
    border-color: #30363D !important;
}
div[data-testid="stMetricLabel"] p { color: #8B949E !important; }
div[data-testid="stMetricValue"] { color: #F0F6FC !important; }
</style>
"""


def _inject_css(dark: bool) -> None:
    st.markdown(_FONT_CSS, unsafe_allow_html=True)
    st.markdown(_BASE_CSS, unsafe_allow_html=True)
    if dark:
        st.markdown(_DARK_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tok(dark: bool) -> dict:
    return _DARK if dark else _LIGHT


def _load_uploaded(file) -> pd.DataFrame:
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file)
    elif name.endswith((".xlsx", ".xls")):
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
    """Render sidebar controls. Returns (raw_df, rpn_min, sev9_only, dark, project_name, author_name)."""
    st.sidebar.title("FMEA Risk Analyzer")
    st.sidebar.markdown("Upload your FMEA file or load the demo dataset to begin.")
    st.sidebar.divider()

    dark = st.sidebar.toggle(
        "Dark Mode",
        value=st.session_state.get("dark_mode", False),
        key="dark_mode",
    )

    st.sidebar.divider()
    st.sidebar.subheader("Data Source")

    uploaded = st.sidebar.file_uploader(
        "Upload FMEA file",
        type=["csv", "xlsx", "xls"],
        help=(
            "CSV or Excel with 11 columns: ID, Process_Step, Component, "
            "Function, Failure_Mode, Effect, Severity, Cause, "
            "Occurrence, Current_Control, Detection"
        ),
    )
    use_demo = st.sidebar.button(
        "Use Demo Dataset",
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
            source_label = f"Loaded: {uploaded.name}"
        except Exception as exc:
            st.sidebar.error(f"Failed to load: {exc}")
    elif st.session_state.get("use_demo"):
        raw_df = pd.read_csv(DEMO_CSV)
        source_label = "Demo: composite panel FMEA (30 rows)"

    if source_label:
        st.sidebar.caption(source_label)

    st.sidebar.divider()
    st.sidebar.subheader("Filters")

    rpn_min = st.sidebar.slider(
        "Minimum RPN",
        min_value=0, max_value=300, value=0, step=10,
        help="Show only failure modes with RPN ≥ this value",
        key="rpn_slider",
    )
    sev9_only = st.sidebar.toggle(
        "Severity ≥ 9 only",
        value=False,
        help="Show only safety-critical failure modes",
        key="sev9_toggle",
    )

    st.sidebar.divider()
    st.sidebar.subheader("Export Settings")
    project_name = st.sidebar.text_input(
        "Project / System Name",
        value="",
        placeholder="e.g. Composite Panel Assembly",
        help="Used as the report title in PDF export",
        key="project_name",
    )
    author_name = st.sidebar.text_input(
        "Author Name",
        value="",
        placeholder="e.g. J. Smith",
        help="Appears on the PDF cover page",
        key="author_name",
    )

    return raw_df, rpn_min, sev9_only, dark, project_name, author_name


def render_process_filter(df: pd.DataFrame) -> list:
    """Render process step multiselect in sidebar after data is loaded."""
    st.sidebar.divider()
    st.sidebar.subheader("Process Steps")
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

def render_header(dark: bool) -> None:
    st.title("FMEA Risk Prioritization Tool")
    st.caption(
        "Analyze failure modes, calculate RPN scores, apply AIAG FMEA-4 criticality flags, "
        "and visualize risk concentration across your manufacturing process."
    )


# ---------------------------------------------------------------------------
# KPI cards (custom HTML)
# ---------------------------------------------------------------------------

def render_metric_badges(df: pd.DataFrame, dark: bool) -> None:
    tok = _tok(dark)
    total    = len(df)
    red      = int((df["Risk_Tier"] == "Red").sum())
    yellow   = int((df["Risk_Tier"] == "Yellow").sum())
    green    = int((df["Risk_Tier"] == "Green").sum())
    high_rpn = int(df["Flag_High_RPN"].sum())
    high_sev = int(df["Flag_High_Severity"].sum())
    action_h = int(df["Flag_Action_Priority_H"].sum())

    metrics = [
        ("TOTAL MODES",    total,    tok["primary"], ""),
        ("CRITICAL",       red,      tok["red"],     "Immediate action"),
        ("WARNING",        yellow,   tok["amber"],   "Action recommended"),
        ("ACCEPTABLE",     green,    tok["green"],   "Monitor"),
        ("HIGH RPN",       high_rpn, tok["purple"],  "RPN > 100"),
        ("SEVERITY ≥ 9",   high_sev, tok["red"],     "Safety-critical"),
        ("ACTION PRIO H",  action_h, tok["amber"],   "RPN ≥ 200 or Sev ≥ 9"),
    ]

    shadow = "0.12" if dark else "0.05"
    cols = st.columns(7)
    for col, (label, value, color, sub) in zip(cols, metrics):
        sub_part = f'<span style="display:block;font-size:10px;color:{tok["text_muted"]};margin-top:3px;">{sub}</span>' if sub else ""
        col.markdown(
            f'<div style="background:{tok["card_bg"]};border:1px solid {tok["border"]};border-radius:8px;padding:14px 16px 12px;border-top:3px solid {color};box-shadow:0 1px 3px rgba(0,0,0,{shadow});"><span style="display:block;font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:{tok["text_sec"]};margin-bottom:6px;">{label}</span><span style="display:block;font-size:28px;font-weight:700;color:{tok["text_pri"]};line-height:1.1;">{value}</span>{sub_part}</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Auto-insights banner (custom HTML)
# ---------------------------------------------------------------------------

def render_insights(df: pd.DataFrame, dark: bool) -> None:
    if df.empty or len(df) < 2:
        return

    tok = _tok(dark)
    total_rpn  = df["RPN"].sum()
    top_n      = min(3, len(df))
    top_pct    = df.nlargest(top_n, "RPN")["RPN"].sum() / total_rpn * 100 if total_rpn else 0
    top_item   = df.iloc[0]
    red_count  = int((df["Risk_Tier"] == "Red").sum())
    sev9_count = int(df["Flag_High_Severity"].sum())

    parts = [
        f"Top {top_n} failure modes account for **{top_pct:.0f}%** of total RPN.",
        f"Highest risk: **{str(top_item['Failure_Mode'])[:60]}** "
        f"(RPN = {int(top_item['RPN'])}, {top_item['Process_Step']}).",
    ]
    if red_count:
        parts.append(f"**{red_count}** item(s) in the Red tier require immediate corrective action.")
    if sev9_count:
        parts.append(f"**{sev9_count}** safety-critical failure mode(s) flagged (Severity ≥ 9).")

    st.info("  ·  ".join(parts))


# ---------------------------------------------------------------------------
# Risk Table tab
# ---------------------------------------------------------------------------

def render_table(df: pd.DataFrame, dark: bool) -> None:
    st.subheader("Ranked Failure Mode Table")
    if df.empty:
        st.info("No failure modes match the current filter settings.")
        return

    tok = _tok(dark)
    col_left, col_right = st.columns([3, 1])

    with col_left:
        st.dataframe(
            _style_table(df, dark),
            use_container_width=True,
            height=520,
        )
        st.caption(
            f"{len(df)} failure mode(s) shown  ·  "
            "Red = immediate action  ·  Yellow = recommended  ·  Green = monitor"
        )

    with col_right:
        red    = int((df["Risk_Tier"] == "Red").sum())
        yellow = int((df["Risk_Tier"] == "Yellow").sum())
        green  = int((df["Risk_Tier"] == "Green").sum())
        total  = len(df)

        def pct(n):
            return n / total * 100 if total else 0

        html = f'<div style="background:{tok["card_bg"]};border:1px solid {tok["border"]};border-radius:8px;padding:16px;font-size:13px;">'
        html += f'<div style="font-size:10px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:{tok["text_sec"]};margin-bottom:14px;">Risk Distribution</div>'
        for label, count, color in [
            ("Critical",   red,    tok["red"]),
            ("Warning",    yellow, tok["amber"]),
            ("Acceptable", green,  tok["green"]),
        ]:
            w = pct(count)
            html += f'<div style="margin-bottom:12px;"><div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="font-size:12px;font-weight:500;color:{tok["text_pri"]};">{label}</span><span style="font-size:12px;color:{tok["text_sec"]};">{count} ({w:.0f}%)</span></div><div style="background:{tok["progress_bg"]};border-radius:4px;height:5px;"><div style="background:{color};width:{w:.1f}%;height:5px;border-radius:4px;"></div></div></div>'
        if total:
            avg_rpn   = df["RPN"].mean()
            max_rpn   = df["RPN"].max()
            total_rpn = df["RPN"].sum()
            html += f'<div style="border-top:1px solid {tok["border"]};margin-top:14px;padding-top:14px;"><div style="display:flex;justify-content:space-between;margin-bottom:6px;"><span style="font-size:11px;color:{tok["text_sec"]};">Avg RPN</span><span style="font-size:11px;font-weight:600;color:{tok["text_pri"]};">{avg_rpn:.0f}</span></div><div style="display:flex;justify-content:space-between;margin-bottom:6px;"><span style="font-size:11px;color:{tok["text_sec"]};">Max RPN</span><span style="font-size:11px;font-weight:600;color:{tok["text_pri"]};">{int(max_rpn)}</span></div><div style="display:flex;justify-content:space-between;"><span style="font-size:11px;color:{tok["text_sec"]};">Total RPN</span><span style="font-size:11px;font-weight:600;color:{tok["text_pri"]};">{int(total_rpn)}</span></div></div>'
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Pareto chart tab
# ---------------------------------------------------------------------------

def render_pareto(pareto_fig, dark: bool) -> None:
    st.subheader("Pareto Chart — Failure Modes Ranked by RPN")
    st.caption(
        "Bars sorted highest to lowest RPN. The cumulative % line shows where 80% of total risk "
        "is concentrated. Focus corrective action on failure modes to the left of the 80% threshold."
    )
    if pareto_fig is None:
        st.info("No data to display under current filters.")
        return
    st.plotly_chart(pareto_fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Heatmap tab
# ---------------------------------------------------------------------------

def render_heatmap(heatmap_fig, dark: bool) -> None:
    st.subheader("Risk Heatmap — Severity × Occurrence")
    st.caption(
        "Each cell shows the count of failure modes with that Severity × Occurrence combination. "
        "Color reflects the worst Risk Tier in the cell. Clustering in the top-right corner "
        "(high S, high O) indicates systemic process problems."
    )
    if heatmap_fig is None:
        st.info("No data to display under current filters.")
        return
    st.plotly_chart(heatmap_fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Critical items tab
# ---------------------------------------------------------------------------

def render_critical_panel(df: pd.DataFrame, dark: bool) -> None:
    tok = _tok(dark)
    critical = df[df["Flag_Action_Priority_H"] == True]  # noqa: E712

    if critical.empty:
        st.success("No critical failure modes under current filters.")
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

    with st.expander("What to do with these items"):
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
# Export section (custom HTML header + styled buttons)
# ---------------------------------------------------------------------------

def render_export_buttons(
    df: pd.DataFrame,
    pareto_fig,
    heatmap_fig,
    project_name: str,
    author_name: str,
    dark: bool,
) -> None:
    st.subheader("Export Report")
    st.caption("Download your analysis as a professional PDF report, an Excel engineering workbook, or raw CSV.")

    col_xl, col_pdf, col_csv, _ = st.columns([1, 1, 1, 3])

    with col_xl:
        st.download_button(
            label="Download Excel",
            data=export_excel(df, project_name=project_name),
            file_name="fmea_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            help="5-sheet engineering workbook: Summary, Ranked Failures, Critical Items, Methodology, Metadata",
        )

    with col_pdf:
        if pareto_fig is not None and heatmap_fig is not None:
            st.download_button(
                label="Download PDF",
                data=export_pdf(
                    df, pareto_fig, heatmap_fig,
                    project_name=project_name,
                    author_name=author_name,
                ),
                file_name="fmea_report.pdf",
                mime="application/pdf",
                use_container_width=True,
                help="7-section industry report: Cover, Executive Summary, Methodology, Results, Charts, Critical Items, Recommendations",
            )
        else:
            st.button(
                "Download PDF",
                disabled=True,
                use_container_width=True,
                help="Requires at least one row in the filtered table",
            )

    with col_csv:
        st.download_button(
            label="Download CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="fmea_analysis.csv",
            mime="text/csv",
            use_container_width=True,
            help="Full analyzed dataset with all calculated columns",
        )


# ---------------------------------------------------------------------------
# Landing page
# ---------------------------------------------------------------------------

def render_landing(dark: bool) -> None:
    tok = _tok(dark)
    st.info("Upload a CSV/Excel file or click **Use Demo Dataset** in the sidebar to begin.")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        with st.expander("Required CSV/Excel schema"):
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
        with st.expander("How RPN and Risk Tiers work"):
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
| Red | RPN > 100 OR Severity ≥ 9 | Immediate corrective action |
| Yellow | RPN 50–100 | Action recommended |
| Green | RPN < 50 | Monitor |
""")

    # How it works section
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**How it works**")
    tok = _tok(dark)
    how_cols = st.columns(4)
    for col, (num, title, desc) in zip(how_cols, [
        ("01", "Upload",    "Import CSV or Excel FMEA worksheet"),
        ("02", "Analyze",   "RPN calculated + AIAG flags applied"),
        ("03", "Visualize", "Pareto chart, heatmap, ranked table"),
        ("04", "Export",    "PDF report or Excel workbook"),
    ]):
        col.markdown(
            f'<div style="text-align:center;padding:20px 12px;background:{tok["card_bg"]};border:1px solid {tok["border"]};border-radius:8px;"><div style="font-size:22px;font-weight:700;color:{tok["primary"]};margin-bottom:4px;">{num}</div><div style="font-size:13px;font-weight:600;color:{tok["text_pri"]};margin-bottom:4px;">{title}</div><div style="font-size:12px;color:{tok["text_sec"]};">{desc}</div></div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------

def main() -> None:
    raw_df, rpn_min, sev9_only, dark, project_name, author_name = render_sidebar()

    _inject_css(dark)
    render_header(dark)

    if raw_df is None:
        st.sidebar.divider()
        st.sidebar.caption(
            "Engineering ref: AIAG FMEA-4 (4th Ed.) + "
            "AIAG/VDA FMEA Handbook (5th Ed., 2019)"
        )
        render_landing(dark)
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
    except (ValueError, KeyError) as exc:
        st.error(f"**Pipeline error:** {exc}")
        st.stop()

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
    _cache_key = (rpn_min, sev9_only, tuple(sorted(process_steps)), len(df_filtered), dark)
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
    render_metric_badges(df_filtered, dark)
    render_insights(df_filtered, dark)
    st.divider()

    tab_table, tab_pareto, tab_heatmap, tab_critical = st.tabs([
        "Risk Table",
        "Pareto Chart",
        "Risk Heatmap",
        "Critical Items",
    ])

    with tab_table:
        render_table(df_filtered, dark)

    with tab_pareto:
        render_pareto(pareto_fig, dark)

    with tab_heatmap:
        render_heatmap(heatmap_fig, dark)

    with tab_critical:
        render_critical_panel(df_filtered, dark)

    st.divider()
    render_export_buttons(
        df_filtered, pareto_fig, heatmap_fig,
        project_name=project_name,
        author_name=author_name,
        dark=dark,
    )


if __name__ == "__main__":
    main()
