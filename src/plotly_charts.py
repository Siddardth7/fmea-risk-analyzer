"""
plotly_charts.py
FMEA Risk Prioritization Tool — Plotly Visualization Layer (Streamlit)

Functions:
    pareto_chart_plotly(df)   — Interactive Pareto chart of failure modes ranked by RPN
    risk_heatmap_plotly(df)   — Interactive Severity × Occurrence heatmap

Both functions return a plotly.graph_objects.Figure ready for st.plotly_chart().
They accept the same analyzed DataFrame as visualizer.py (output of run_pipeline).

Author: Siddardth | M.S. Aerospace Engineering, UIUC
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Color palette — aligned with Risk_Tier thresholds in rpn_engine.py
# ---------------------------------------------------------------------------

TIER_COLORS = {
    "Red":    "#e74c3c",
    "Yellow": "#f39c12",
    "Green":  "#27ae60",
}

TIER_LABELS = {
    "Red":    "Red — Immediate action",
    "Yellow": "Yellow — Action recommended",
    "Green":  "Green — Monitor",
}

# ---------------------------------------------------------------------------
# pareto_chart_plotly
# ---------------------------------------------------------------------------

def pareto_chart_plotly(df: pd.DataFrame) -> go.Figure:
    """
    Generate an interactive Plotly Pareto chart for use in Streamlit.

    Combines a descending bar chart (colored by Risk_Tier) with a
    cumulative RPN % line and an 80 % reference line.

    Parameters
    ----------
    df : pd.DataFrame
        Analyzed FMEA DataFrame — output of run_pipeline() or rank_by_rpn().
        Must contain columns: Failure_Mode, RPN, Risk_Tier.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    df_sorted = df.sort_values("RPN", ascending=False).reset_index(drop=True)

    labels         = [str(fm)[:35] for fm in df_sorted["Failure_Mode"]]
    rpns           = df_sorted["RPN"].values.astype(float)
    tiers          = df_sorted["Risk_Tier"].values
    bar_colors     = [TIER_COLORS.get(t, "#95a5a6") for t in tiers]
    cumulative_pct = np.cumsum(rpns) / rpns.sum() * 100 if rpns.sum() > 0 else rpns * 0

    fig = go.Figure()

    # --- Single Bar trace with per-bar colors (works across all Plotly 5/6 versions) ---
    hover_texts = [
        f"<b>{labels[i]}</b><br>RPN: {int(rpns[i])}<br>Tier: {tiers[i]}"
        for i in range(len(labels))
    ]
    fig.add_trace(go.Bar(
        x=labels,
        y=rpns,
        marker_color=bar_colors,
        yaxis="y1",
        text=[str(int(r)) for r in rpns],
        textposition="outside",
        hovertext=hover_texts,
        hoverinfo="text",
        showlegend=False,
        name="RPN",
    ))

    # --- Invisible scatter traces for the legend (one per tier) ---
    for tier_name, tier_color in TIER_COLORS.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(size=10, color=tier_color, symbol="square"),
            name=TIER_LABELS[tier_name],
            yaxis="y1",
        ))

    # --- Cumulative % line (right y-axis) ---
    fig.add_trace(go.Scatter(
        x=labels,
        y=cumulative_pct,
        mode="lines+markers",
        name="Cumulative RPN %",
        yaxis="y2",
        line=dict(color="#2c3e50", width=2),
        marker=dict(size=5),
        hovertemplate="<b>%{x}</b><br>Cumulative: %{y:.1f}%<extra></extra>",
    ))

    # --- 80% reference line drawn as a Scatter on y2 (avoids add_hline yref issues) ---
    fig.add_trace(go.Scatter(
        x=[labels[0], labels[-1]] if len(labels) > 0 else [],
        y=[80, 80],
        mode="lines",
        yaxis="y2",
        line=dict(color="#7f8c8d", dash="dash", width=1.2),
        name="80% threshold",
        hoverinfo="skip",
    ))

    fig.update_layout(
        title=dict(
            text="FMEA Pareto Chart — Failure Modes Ranked by RPN",
            font=dict(size=15, color="#2c3e50"),
        ),
        xaxis=dict(
            title=dict(text="Failure Mode"),
            tickangle=-45,
            tickfont=dict(size=9),
        ),
        yaxis=dict(
            title=dict(text="RPN", font=dict(color="#2c3e50")),
        ),
        yaxis2=dict(
            title=dict(text="Cumulative RPN (%)", font=dict(color="#2c3e50")),
            overlaying="y",
            side="right",
            range=[0, 110],
        ),
        barmode="relative",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        height=500,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(b=120),
    )

    return fig


# ---------------------------------------------------------------------------
# risk_heatmap_plotly
# ---------------------------------------------------------------------------

def risk_heatmap_plotly(df: pd.DataFrame) -> go.Figure:
    """
    Generate an interactive Plotly Severity × Occurrence risk heatmap.

    Each occupied cell shows the count of failure modes.
    Cell color reflects the highest Risk_Tier present (Red > Yellow > Green).

    Parameters
    ----------
    df : pd.DataFrame
        Analyzed FMEA DataFrame — output of run_pipeline() or rank_by_rpn().
        Must contain columns: Severity, Occurrence, Risk_Tier.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    TIER_RANK  = {"Green": 1, "Yellow": 2, "Red": 3}
    # 0 = empty cell

    grid_count     = np.zeros((10, 10), dtype=int)
    grid_tier_rank = np.zeros((10, 10), dtype=int)

    for _, row in df.iterrows():
        s = int(row["Severity"])   - 1   # 0-indexed
        o = int(row["Occurrence"]) - 1
        grid_count[s, o] += 1
        tier_r = TIER_RANK.get(row["Risk_Tier"], 1)
        if tier_r > grid_tier_rank[s, o]:
            grid_tier_rank[s, o] = tier_r

    # Colorscale: 0=empty, 1=Green, 2=Yellow, 3=Red
    colorscale = [
        [0.00, "#f0f0f0"],   # empty
        [0.01, "#f0f0f0"],
        [0.34, "#27ae60"],   # Green
        [0.34, "#27ae60"],
        [0.67, "#f39c12"],   # Yellow
        [0.67, "#f39c12"],
        [1.00, "#e74c3c"],   # Red
    ]

    # Annotation text: count if > 0, else blank
    text_matrix = [
        [str(grid_count[i, j]) if grid_count[i, j] > 0 else ""
         for j in range(10)]
        for i in range(10)
    ]

    # Hover text
    tier_name_map = {0: "No failures", 1: "Green", 2: "Yellow", 3: "Red"}
    hover_matrix = [
        [
            f"Severity: {i+1}<br>Occurrence: {j+1}<br>"
            f"Count: {grid_count[i,j]}<br>Tier: {tier_name_map[grid_tier_rank[i,j]]}"
            for j in range(10)
        ]
        for i in range(10)
    ]

    fig = go.Figure(data=go.Heatmap(
        z=grid_tier_rank,
        x=list(range(1, 11)),
        y=list(range(1, 11)),
        colorscale=colorscale,
        zmin=0,
        zmax=3,
        showscale=False,
        text=text_matrix,
        texttemplate="%{text}",
        textfont=dict(size=12, color="white"),
        hoverinfo="text",
        hovertext=hover_matrix,
        xgap=2,
        ygap=2,
    ))

    # Invisible scatter traces for the legend
    for tier_name, tier_color in TIER_COLORS.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(size=12, color=tier_color, symbol="square"),
            name=TIER_LABELS[tier_name],
            showlegend=True,
        ))

    fig.update_layout(
        title=dict(
            text="FMEA Risk Heatmap — Severity × Occurrence",
            font=dict(size=15, color="#2c3e50"),
        ),
        xaxis=dict(
            title="Occurrence (O)",
            tickmode="linear",
            tick0=1, dtick=1,
            constrain="domain",
        ),
        yaxis=dict(
            title="Severity (S)",
            tickmode="linear",
            tick0=1, dtick=1,
            scaleanchor="x",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        height=520,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    return fig
