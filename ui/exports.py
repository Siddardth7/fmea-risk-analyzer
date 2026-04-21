"""
ui/exports.py
Export button rendering with lazy caching and error isolation.
"""
from __future__ import annotations
import hashlib
import streamlit as st
import pandas as pd
from src.exporter import export_excel, export_pdf, _sanitize_for_export


def _export_cache_key(
    df: pd.DataFrame,
    rpn_min: int,
    sev9_only: bool,
    process_steps: list[str],
    export_type: str,
) -> tuple:
    df_hash = hashlib.md5(df.reset_index(drop=True).to_json().encode()).hexdigest()
    return (df_hash, rpn_min, sev9_only, tuple(sorted(process_steps)), export_type)


def render_export_buttons(
    df: pd.DataFrame,
    pareto_fig,
    heatmap_fig,
    rpn_min: int,
    sev9_only: bool,
    process_steps: list[str],
) -> None:
    st.subheader("📥  Export Report")
    col_xl, col_pdf, col_csv, _ = st.columns([1, 1, 1, 3])

    # Excel
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

    # PDF
    pdf_key = _export_cache_key(df, rpn_min, sev9_only, process_steps, "pdf")
    if st.session_state.get("_pdf_cache_key") != pdf_key:
        try:
            pdf_data = export_pdf(df) if (pareto_fig is not None and heatmap_fig is not None) else None
            st.session_state["_pdf_bytes"] = pdf_data
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

    # CSV
    with col_csv:
        st.download_button(
            label="📋  Download CSV",
            data=_sanitize_for_export(df).to_csv(index=False).encode("utf-8"),
            file_name="fmea_analysis.csv",
            mime="text/csv",
            use_container_width=True,
            help="Full analyzed dataset with all calculated columns",
        )
