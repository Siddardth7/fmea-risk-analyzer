"""
plotly_charts.py
FMEA Risk Prioritization Tool — Plotly Visualization Layer (Streamlit)

Functions:
    pareto_chart_plotly(df, dark)   — Interactive Pareto chart of failure modes ranked by RPN
    risk_heatmap_plotly(df, dark)   — Interactive Severity × Occurrence heatmap

Both functions return a plotly.graph_objects.Figure ready for st.plotly_chart().

Author: Siddardth | M.S. Aerospace Engineering, UIUC
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Professional color palette — calibrated for clarity, not saturation
# ---------------------------------------------------------------------------

TIER_COLORS = {
    "Red":    "#DC2626",   # professional red (not garish coral)
    "Yellow": "#D97706",   # warm amber (not orange)
    "Green":  "#16A34A",   # clean green
}

TIER_LABELS = {
    "Red":    "Red — Immediate action",
    "Yellow": "Yellow — Action recommended",
    "Green":  "Green — Monitor",
}

# ---------------------------------------------------------------------------
# Theme helpers
# ---------------------------------------------------------------------------

def _theme(dark: bool) -> dict:
    if dark:
        return dict(
            bg="#161B22",
            paper="#0D1117",
            text="#C9D1D9",
            text_muted="#6E7681",
            grid="#21262D",
            line="#58A6FF",
            ref_line="#6E7681",
            axis_line="#30363D",
        )
    return dict(
        bg="#FFFFFF",
        paper="#FFFFFF",
        text="#1E293B",
        text_muted="#94A3B8",
        grid="#F1F5F9",
        line="#2563EB",
        ref_line="#94A3B8",
        axis_line="#E2E8F0",
    )


# ---------------------------------------------------------------------------
# pareto_chart_plotly
# ---------------------------------------------------------------------------

def pareto_chart_plotly(df: pd.DataFrame, dark: bool = False) -> go.Figure:
    """
    Interactive Plotly Pareto chart.

    Combines a descending bar chart (colored by Risk_Tier) with a
    cumulative RPN % line and an 80% reference line.
    """
    t = _theme(dark)

    df_sorted  = df.sort_values("RPN", ascending=False).reset_index(drop=True)
    labels     = [str(fm)[:40] for fm in df_sorted["Failure_Mode"]]
    rpns       = df_sorted["RPN"].values.astype(float)
    tiers      = df_sorted["Risk_Tier"].values
    bar_colors = [TIER_COLORS.get(tier, "#94A3B8") for tier in tiers]
    cum_pct    = np.cumsum(rpns) / rpns.sum() * 100 if rpns.sum() > 0 else rpns * 0

    fig = go.Figure()

    # Bar trace
    hover_texts = [
        f"<b>{labels[i]}</b><br>"
        f"RPN: <b>{int(rpns[i])}</b><br>"
        f"Risk Tier: {tiers[i]}<br>"
        f"Rank: #{i+1} of {len(labels)}"
        for i in range(len(labels))
    ]
    fig.add_trace(go.Bar(
        x=labels,
        y=rpns,
        marker_color=bar_colors,
        marker_line_width=0,
        marker_opacity=0.9,
        yaxis="y1",
        text=[str(int(r)) for r in rpns],
        textposition="outside",
        textfont=dict(size=9, color=t["text_muted"], family="Inter, sans-serif"),
        hovertext=hover_texts,
        hoverinfo="text",
        showlegend=False,
        name="RPN",
    ))

    # Invisible legend markers for tiers
    for tier_name, tier_color in TIER_COLORS.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(size=11, color=tier_color, symbol="square"),
            name=TIER_LABELS[tier_name],
            yaxis="y1",
        ))

    # Cumulative % line
    fig.add_trace(go.Scatter(
        x=labels,
        y=cum_pct,
        mode="lines+markers",
        name="Cumulative RPN %",
        yaxis="y2",
        line=dict(color=t["line"], width=2),
        marker=dict(size=4, color=t["line"]),
        hovertemplate="<b>%{x}</b><br>Cumulative: %{y:.1f}%<extra></extra>",
    ))

    # 80% reference line
    if len(labels) > 0:
        fig.add_trace(go.Scatter(
            x=[labels[0], labels[-1]],
            y=[80, 80],
            mode="lines",
            yaxis="y2",
            line=dict(color=t["ref_line"], dash="dot", width=1.2),
            name="80% threshold",
            hoverinfo="skip",
        ))

    fig.update_layout(
        title=dict(
            text="Failure Modes Ranked by RPN — Pareto Analysis",
            font=dict(size=15, color=t["text"], family="Inter, sans-serif"),
            x=0.0,
            pad=dict(b=8),
        ),
        xaxis=dict(
            title=dict(text="Failure Mode", font=dict(color=t["text_muted"], size=11,
                                                       family="Inter, sans-serif")),
            tickangle=-50,
            tickfont=dict(size=9, color=t["text_muted"], family="Inter, sans-serif"),
            gridcolor=t["grid"],
            linecolor=t["axis_line"],
            showline=True,
        ),
        yaxis=dict(
            title=dict(text="Risk Priority Number (RPN)",
                       font=dict(color=t["text_muted"], size=11, family="Inter, sans-serif")),
            tickfont=dict(color=t["text_muted"], family="Inter, sans-serif"),
            gridcolor=t["grid"],
            linecolor=t["axis_line"],
            showline=True,
            zeroline=False,
        ),
        yaxis2=dict(
            title=dict(text="Cumulative RPN (%)",
                       font=dict(color=t["text_muted"], size=11, family="Inter, sans-serif")),
            overlaying="y",
            side="right",
            range=[0, 112],
            tickfont=dict(color=t["text_muted"], family="Inter, sans-serif"),
            gridcolor="rgba(0,0,0,0)",
            showline=False,
        ),
        barmode="relative",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=t["text"], size=11, family="Inter, sans-serif"),
            bgcolor="rgba(0,0,0,0)",
        ),
        height=580,
        plot_bgcolor=t["bg"],
        paper_bgcolor=t["paper"],
        font=dict(color=t["text"], family="Inter, sans-serif"),
        margin=dict(l=60, r=80, t=80, b=160),
        hoverlabel=dict(
            bgcolor=t["bg"],
            font=dict(color=t["text"], size=12, family="Inter, sans-serif"),
            bordercolor=t["axis_line"],
        ),
    )

    return fig


# ---------------------------------------------------------------------------
# risk_heatmap_plotly
# ---------------------------------------------------------------------------

def risk_heatmap_plotly(df: pd.DataFrame, dark: bool = False) -> go.Figure:
    """
    Interactive Plotly Severity × Occurrence risk heatmap.

    Each cell shows the count of failure modes at that S × O combination.
    Color reflects the worst Risk_Tier present (Red > Yellow > Green).
    """
    t = _theme(dark)
    empty_color = "#21262D" if dark else "#F8FAFC"

    TIER_RANK = {"Green": 1, "Yellow": 2, "Red": 3}

    grid_count     = np.zeros((10, 10), dtype=int)
    grid_tier_rank = np.zeros((10, 10), dtype=int)

    for _, row in df.iterrows():
        s = int(row["Severity"])   - 1
        o = int(row["Occurrence"]) - 1
        grid_count[s, o] += 1
        tier_r = TIER_RANK.get(row["Risk_Tier"], 1)
        if tier_r > grid_tier_rank[s, o]:
            grid_tier_rank[s, o] = tier_r

    colorscale = [
        [0.00, empty_color],
        [0.01, empty_color],
        [0.34, "#16A34A"],
        [0.34, "#16A34A"],
        [0.67, "#D97706"],
        [0.67, "#D97706"],
        [1.00, "#DC2626"],
    ]

    text_matrix = [
        [str(grid_count[i, j]) if grid_count[i, j] > 0 else ""
         for j in range(10)]
        for i in range(10)
    ]

    tier_name_map = {0: "No failures", 1: "Green", 2: "Yellow", 3: "Red"}
    hover_matrix = [
        [
            f"<b>Severity {i+1} × Occurrence {j+1}</b><br>"
            f"Failure modes: <b>{grid_count[i,j]}</b><br>"
            f"Worst tier: {tier_name_map[grid_tier_rank[i,j]]}"
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
        textfont=dict(size=13, color="white", family="Inter, sans-serif"),
        hoverinfo="text",
        hovertext=hover_matrix,
        xgap=3,
        ygap=3,
    ))

    # Legend markers
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
            text="Risk Heatmap — Severity × Occurrence Matrix",
            font=dict(size=15, color=t["text"], family="Inter, sans-serif"),
            x=0.0,
            pad=dict(b=8),
        ),
        xaxis=dict(
            title=dict(text="Occurrence (O)",
                       font=dict(color=t["text_muted"], size=11, family="Inter, sans-serif")),
            tickmode="linear",
            tick0=1, dtick=1,
            constrain="domain",
            tickfont=dict(color=t["text_muted"], family="Inter, sans-serif"),
            gridcolor=t["grid"],
            showline=True,
            linecolor=t["axis_line"],
        ),
        yaxis=dict(
            title=dict(text="Severity (S)",
                       font=dict(color=t["text_muted"], size=11, family="Inter, sans-serif")),
            tickmode="linear",
            tick0=1, dtick=1,
            scaleanchor="x",
            tickfont=dict(color=t["text_muted"], family="Inter, sans-serif"),
            gridcolor=t["grid"],
            showline=True,
            linecolor=t["axis_line"],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=t["text"], size=11, family="Inter, sans-serif"),
            bgcolor="rgba(0,0,0,0)",
        ),
        height=540,
        plot_bgcolor=t["bg"],
        paper_bgcolor=t["paper"],
        font=dict(color=t["text"], family="Inter, sans-serif"),
        margin=dict(l=60, r=40, t=80, b=60),
        hoverlabel=dict(
            bgcolor=t["bg"],
            font=dict(color=t["text"], size=12, family="Inter, sans-serif"),
            bordercolor=t["axis_line"],
        ),
    )

    return fig
