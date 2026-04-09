"""
exporter.py
FMEA Risk Prioritization Tool — Export Layer

Functions:
    export_excel(df)                        → bytes  (openpyxl .xlsx)
    export_pdf(df, pareto_fig, heatmap_fig) → bytes  (fpdf2 .pdf)

Both return raw bytes suitable for st.download_button().

Author: Siddardth | M.S. Aerospace Engineering, UIUC
"""

from __future__ import annotations

import io
import os
import tempfile
from datetime import datetime
from typing import Any

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TIER_FILL = {
    "Red":    PatternFill(start_color="FCE4E4", end_color="FCE4E4", fill_type="solid"),
    "Yellow": PatternFill(start_color="FFF9E6", end_color="FFF9E6", fill_type="solid"),
    "Green":  PatternFill(start_color="E8F8EF", end_color="E8F8EF", fill_type="solid"),
}

_HEADER_FILL = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
_HEADER_FONT = Font(bold=True, color="FFFFFF", size=10)
_BOLD_FONT   = Font(bold=True, size=10)
_NORMAL_FONT = Font(size=10)

_EXPORT_COLUMNS = [
    "ID", "Process_Step", "Component", "Failure_Mode",
    "Effect", "Severity", "Occurrence", "Detection",
    "RPN", "Risk_Tier",
    "Flag_High_RPN", "Flag_High_Severity", "Flag_Action_Priority_H",
]

_COL_WIDTHS = {
    "ID": 6, "Process_Step": 20, "Component": 16, "Failure_Mode": 28,
    "Effect": 24, "Severity": 10, "Occurrence": 12, "Detection": 11,
    "RPN": 8, "Risk_Tier": 12,
    "Flag_High_RPN": 14, "Flag_High_Severity": 16, "Flag_Action_Priority_H": 20,
}

_TOOL_VERSION = "1.0.0"

# PDF layout constants
_PDF_TIER_RGB = {
    "Red":    (252, 228, 228),
    "Yellow": (255, 249, 230),
    "Green":  (232, 248, 239),
}

_PDF_TABLE_COLS = [
    ("ID",           10),
    ("Process Step", 38),
    ("Failure Mode", 52),
    ("S",             8),
    ("O",             8),
    ("D",             8),
    ("RPN",          12),
    ("Tier",         16),
    ("Flags",        65),
]


# ---------------------------------------------------------------------------
# export_excel
# ---------------------------------------------------------------------------

def export_excel(df: pd.DataFrame) -> bytes:
    """
    Export the analyzed FMEA DataFrame to an Excel workbook.

    Sheet 1 — "FMEA Analysis": ranked table with Risk_Tier row coloring.
    Sheet 2 — "Metadata": run timestamp, row counts, flag summary.

    Parameters
    ----------
    df : pd.DataFrame
        Output of run_pipeline() — must include RPN, Risk_Tier, Flag_* columns.

    Returns
    -------
    bytes
        Raw .xlsx bytes suitable for st.download_button().
    """
    wb = openpyxl.Workbook()

    _write_fmea_sheet(wb, df)
    _write_metadata_sheet(wb, df)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _write_fmea_sheet(wb: openpyxl.Workbook, df: pd.DataFrame) -> None:
    ws = wb.active
    ws.title = "FMEA Analysis"

    cols = [c for c in _EXPORT_COLUMNS if c in df.columns]

    # Header row
    for col_idx, col_name in enumerate(cols, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.fill = _HEADER_FILL
        cell.font = _HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 22

    # Data rows
    for row_idx, (_, row) in enumerate(df.iterrows(), start=2):
        tier = str(row.get("Risk_Tier", "Green"))
        fill = _TIER_FILL.get(tier, _TIER_FILL["Green"])
        for col_idx, col_name in enumerate(cols, start=1):
            val = row[col_name]
            # Convert numpy booleans / numpy ints for Excel compatibility
            if hasattr(val, "item"):
                val = val.item()
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.fill = fill
            cell.font = _NORMAL_FONT
            cell.alignment = Alignment(vertical="center", wrap_text=False)

    # Column widths
    for col_idx, col_name in enumerate(cols, start=1):
        width = _COL_WIDTHS.get(col_name, 14)
        ws.column_dimensions[
            openpyxl.utils.get_column_letter(col_idx)
        ].width = width

    ws.freeze_panes = "A2"


def _write_metadata_sheet(wb: openpyxl.Workbook, df: pd.DataFrame) -> None:
    ws = wb.create_sheet("Metadata")

    rows = [
        ("Generated",         datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ("Tool Version",      _TOOL_VERSION),
        ("Engineering Ref",   "AIAG FMEA-4 (4th Ed.) + AIAG/VDA FMEA Handbook (5th Ed., 2019)"),
        ("",                  ""),
        ("Total Rows",        len(df)),
        ("Red (Immediate)",   int((df["Risk_Tier"] == "Red").sum())    if "Risk_Tier"               in df.columns else "N/A"),
        ("Yellow",            int((df["Risk_Tier"] == "Yellow").sum()) if "Risk_Tier"               in df.columns else "N/A"),
        ("Green",             int((df["Risk_Tier"] == "Green").sum())  if "Risk_Tier"               in df.columns else "N/A"),
        ("High RPN (>100)",   int(df["Flag_High_RPN"].sum())           if "Flag_High_RPN"           in df.columns else "N/A"),
        ("Severity >= 9",     int(df["Flag_High_Severity"].sum())      if "Flag_High_Severity"      in df.columns else "N/A"),
        ("Action Priority H", int(df["Flag_Action_Priority_H"].sum())  if "Flag_Action_Priority_H"  in df.columns else "N/A"),
    ]

    for r_idx, (label, value) in enumerate(rows, start=1):
        ws.cell(r_idx, 1, label).font = _BOLD_FONT
        ws.cell(r_idx, 2, value).font = _NORMAL_FONT

    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 48


# ---------------------------------------------------------------------------
# export_pdf
# ---------------------------------------------------------------------------

def export_pdf(
    df: pd.DataFrame,
    pareto_fig: Any,
    heatmap_fig: Any,
) -> bytes:
    """
    Export the analyzed FMEA DataFrame to a PDF report.

    Page 1: Summary header + flag counts + ranked FMEA table.
    Page 2: Pareto chart (Plotly → PNG via kaleido).
    Page 3: Risk heatmap (Plotly → PNG via kaleido).

    Parameters
    ----------
    df : pd.DataFrame
        Output of run_pipeline().
    pareto_fig : plotly.graph_objects.Figure
        Pareto chart figure from pareto_chart_plotly().
    heatmap_fig : plotly.graph_objects.Figure
        Heatmap figure from risk_heatmap_plotly().

    Returns
    -------
    bytes
        Raw .pdf bytes suitable for st.download_button().
    """
    from fpdf import FPDF
    import plotly.io as pio

    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.set_margins(10, 10, 10)

    _pdf_page1(pdf, df)
    _pdf_chart_page(pdf, pareto_fig,  "Pareto Chart - Failure Modes Ranked by RPN",
                    width=1400, height=700)
    _pdf_chart_page(pdf, heatmap_fig, "Risk Heatmap - Severity x Occurrence",
                    width=900,  height=700)

    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# PDF helpers
# ---------------------------------------------------------------------------

def _flag_str(row: pd.Series) -> str:
    parts = []
    if row.get("Flag_High_RPN"):          parts.append("High RPN")
    if row.get("Flag_High_Severity"):     parts.append("Sev>=9")
    if row.get("Flag_Action_Priority_H"): parts.append("AP-H")
    return ", ".join(parts) if parts else "-"


def _pdf_page1(pdf: Any, df: pd.DataFrame) -> None:
    pdf.add_page()

    # Title bar
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "FMEA Risk Analysis Report",  # ASCII-safe title
             new_x="LMARGIN", new_y="NEXT", align="C", fill=True)
    pdf.ln(2)

    # Sub-header
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(
        0, 5,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}   |   "
        "AIAG FMEA-4 (4th Ed.) + AIAG/VDA FMEA Handbook (5th Ed., 2019)",
        new_x="LMARGIN", new_y="NEXT", align="C",
    )
    pdf.ln(3)

    # Summary metrics
    metrics = [
        ("Total Modes",       len(df)),
        ("Red",               int((df["Risk_Tier"] == "Red").sum())    if "Risk_Tier"               in df.columns else 0),
        ("Yellow",            int((df["Risk_Tier"] == "Yellow").sum()) if "Risk_Tier"               in df.columns else 0),
        ("Green",             int((df["Risk_Tier"] == "Green").sum())  if "Risk_Tier"               in df.columns else 0),
        ("High RPN",          int(df["Flag_High_RPN"].sum())           if "Flag_High_RPN"           in df.columns else 0),
        ("Severity >= 9",     int(df["Flag_High_Severity"].sum())      if "Flag_High_Severity"      in df.columns else 0),
        ("Action Priority H", int(df["Flag_Action_Priority_H"].sum())  if "Flag_Action_Priority_H"  in df.columns else 0),
    ]
    cell_w = 277 / len(metrics)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(44, 62, 80)
    for label, _ in metrics:
        pdf.set_fill_color(240, 243, 246)
        pdf.cell(cell_w, 8, label, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "B", 11)
    for _, value in metrics:
        pdf.cell(cell_w, 8, str(value), border=1, align="C", fill=False)
    pdf.ln(5)

    # Table header
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    for col_label, col_w in _PDF_TABLE_COLS:
        pdf.cell(col_w, 7, col_label, border=1, align="C", fill=True)
    pdf.ln()

    # Data rows
    df2 = df.copy()
    df2["_flags"] = df2.apply(_flag_str, axis=1)
    pdf.set_font("Helvetica", "", 7)

    for _, row in df2.iterrows():
        tier = str(row.get("Risk_Tier", "Green"))
        r, g, b = _PDF_TIER_RGB.get(tier, (255, 255, 255))
        pdf.set_fill_color(r, g, b)
        pdf.set_text_color(40, 40, 40)

        values = [
            str(int(row["ID"]))         if "ID"           in row.index else "",
            str(row.get("Process_Step", ""))[:22],
            str(row.get("Failure_Mode", ""))[:32],
            str(int(row["Severity"]))   if "Severity"     in row.index else "",
            str(int(row["Occurrence"])) if "Occurrence"   in row.index else "",
            str(int(row["Detection"]))  if "Detection"    in row.index else "",
            str(int(row["RPN"]))        if "RPN"          in row.index else "",
            tier,
            str(row.get("_flags", "-"))[:38],
        ]
        for (_, col_w), val in zip(_PDF_TABLE_COLS, values):
            pdf.cell(col_w, 6, val, border=1,
                     align="C" if col_w <= 16 else "L", fill=True)
        pdf.ln()


def _pdf_chart_page(
    pdf: Any,
    fig: Any,
    title: str,
    width: int = 1200,
    height: int = 700,
) -> None:
    """Render a Plotly figure to PNG and embed on a new PDF page."""
    import plotly.io as pio

    pdf.add_page()

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT", align="C", fill=True)
    pdf.ln(4)

    png_bytes = pio.to_image(fig, format="png", width=width, height=height, scale=2)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(png_bytes)
        tmp_path = tmp.name

    try:
        pdf.image(tmp_path, x=10, w=277)
    finally:
        os.unlink(tmp_path)
