# FMEA Risk Prioritization Tool

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.56-FF4B4B?logo=streamlit)](https://streamlit.io)
[![Plotly](https://img.shields.io/badge/Plotly-6.6-3F4F75?logo=plotly)](https://plotly.com)
[![Tests](https://img.shields.io/badge/Tests-61%20passing-brightgreen)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> A Python-based Failure Mode and Effects Analysis (FMEA) tool for process engineering.  
> Upload a CSV or Excel FMEA file, get an instant ranked risk table, interactive charts,  
> and one-click PDF + Excel exports — all in a browser.

**Live Demo:** [fmea-risk-analyzer.streamlit.app]([https://fmea-risk-analyzer.streamlit.app](https://fmea-risk-analyzer-mhwzcki9sdzfz5d8rbzsdn.streamlit.app/)) ← *(update after deploy)*  
**Engineering Reference:** AIAG FMEA-4 (4th Ed.) + AIAG/VDA FMEA Handbook (5th Ed., 2019)  
**Author:** Siddardth | M.S. Aerospace Engineering, UIUC

---

## Project Status

| Phase | Scope | Target | Status |
|-------|-------|--------|--------|
| **Phase 1 — Foundation** | RPN engine, demo dataset, CLI | Apr 1, 2026 | ✅ Complete |
| **Phase 2 — Visualization** | Pareto chart, risk heatmap, dataset expansion | Apr 8, 2026 | ✅ Complete |
| **Phase 3 — Streamlit App** | Web UI, file upload, filters, critical flags panel | Apr 15, 2026 | ✅ Complete |
| **Phase 4 — Export & Deploy** | PDF/Excel export, Streamlit Cloud deploy, README | Apr 22, 2026 | ✅ Complete |
| **Launch** | GitHub public + live URL + LinkedIn post | Apr 23, 2026 | ✅ Complete |

---

## Screenshots

| Ranked Table | Pareto Chart | Risk Heatmap |
|:---:|:---:|:---:|
| ![Ranked Table](assets/screenshot_table.png) | ![Pareto](assets/screenshot_pareto.png) | ![Heatmap](assets/screenshot_heatmap.png) |

---

## Features

- **Automated RPN calculation** — Severity × Occurrence × Detection per AIAG FMEA-4
- **AIAG flag detection** — High RPN (>100), Severity >= 9, Action Priority H
- **Color-coded risk table** — Red / Yellow / Green row highlighting by risk tier
- **Interactive Pareto chart** — failure modes ranked by RPN with 80% cumulative line
- **Severity × Occurrence heatmap** — visual risk matrix showing failure mode density
- **Live sidebar filters** — RPN threshold slider + Severity >= 9 toggle, updates all panels instantly
- **Critical items expander** — dedicated view of Action Priority H failure modes
- **One-click exports** — Excel workbook (color-coded, 2 sheets) + PDF report (3 pages with charts)
- **Demo dataset** — 30 realistic composite panel manufacturing failure modes

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/Siddardth7/fmea-risk-analyzer.git
cd fmea-risk-analyzer
pip install -r requirements.txt

# 2. Launch the web app
streamlit run app.py

# 3. Or use the CLI
python fmea_analyzer.py --input data/composite_panel_fmea_demo.csv --charts
```

The app opens at `http://localhost:8501`. Click **Use Demo Dataset** or upload your own file.

---

## Project Structure

```
fmea-risk-analyzer/
├── app.py                              # Streamlit web application
├── fmea_analyzer.py                    # CLI entry point
├── requirements.txt
├── src/
│   ├── rpn_engine.py                   # Core: validate, calculate RPN, flag, rank
│   ├── visualizer.py                   # Matplotlib charts (CLI)
│   ├── plotly_charts.py                # Plotly charts (Streamlit)
│   └── exporter.py                     # Excel + PDF export
├── tests/
│   ├── test_rpn_engine.py              # 13 tests — RPN logic
│   ├── test_visualizer.py              # 16 tests — matplotlib charts
│   ├── test_streamlit_edge_cases.py    # 20 tests — edge cases
│   └── test_exporter.py               # 12 tests — export functions
├── data/
│   └── composite_panel_fmea_demo.csv  # 30-row aerospace demo dataset
├── docs/
│   ├── FMEA_methodology_notes.md      # Engineering write-up
│   ├── ASSUMPTIONS_LOG.md             # Every threshold decision documented
│   └── FMEA_input_schema.md           # Column definitions
└── assets/                            # Screenshots + demo GIF
```

---

## Using Your Own FMEA File

Your CSV or Excel file must include these columns:

| Column | Type | Description |
|---|---|---|
| `ID` | int | Unique row identifier |
| `Process_Step` | str | Manufacturing step name |
| `Component` | str | Part or sub-assembly |
| `Function` | str | Intended function |
| `Failure_Mode` | str | How the component can fail |
| `Effect` | str | Consequence of failure |
| `Severity` | int (1–10) | Severity of effect (AIAG scale) |
| `Cause` | str | Root cause |
| `Occurrence` | int (1–10) | Likelihood of occurrence |
| `Current_Control` | str | Existing controls |
| `Detection` | int (1–10) | Ability to detect before customer |

A blank template is available at `data/fmea_input_template.csv`.

---

## Demo Dataset

`data/composite_panel_fmea_demo.csv` — 30 failure modes across 6 process steps of a carbon fiber composite panel manufacturing process:

- **Prepreg Layup** — ply misalignment, wrong ply count, out-of-life material
- **Bagging** — bag puncture, sealant tape failure, vacuum leak
- **Autoclave Cure** — temperature deviation, pressure loss, cure cycle abort
- **Demold** — part adhesion, edge delamination, handling damage
- **Post-Cure Inspection** — NDI miss, dimensional non-conformance
- **Assembly** — fastener torque error, adhesive bond failure

S/O/D scores are calibrated to realistic aerospace PFMEA values, producing a meaningful 80/20 Pareto distribution where 5–6 failure modes drive 80% of total RPN.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web UI | Streamlit 1.56 |
| Charts | Plotly 6.6 |
| Data | pandas 3.0, numpy 2.4 |
| PDF export | fpdf2 2.8 |
| Excel export | openpyxl 3.1 |
| Chart to PNG | kaleido 1.2 |
| CLI charts | matplotlib 3.10 |
| Tests | pytest 9.0 (61 tests) |

---

## Running Tests

```bash
python3 -m pytest tests/ -v
# 61 tests, all passing
```

---

## Resume Bullet

> **FMEA Risk Prioritization Tool** — Built a Python-based FMEA analysis tool that automates RPN scoring, AIAG FMEA-4 criticality flagging, and risk visualization for aerospace manufacturing. Delivered as a Streamlit web app with interactive Pareto + heatmap charts, live filtering, and one-click PDF/Excel export. Deployed on Streamlit Cloud. (Python, Streamlit, Plotly, openpyxl, fpdf2) [[GitHub](https://github.com/Siddardth7/fmea-risk-analyzer)] [[Live Demo](https://fmea-risk-analyzer.streamlit.app)]

---

## Engineering References

1. AIAG FMEA-4 (4th Edition, 2008) — *Potential Failure Mode and Effects Analysis Reference Manual*
2. AIAG/VDA FMEA Handbook (1st Edition, 2019)
3. See `docs/FMEA_methodology_notes.md` for detailed methodology notes
4. See `docs/ASSUMPTIONS_LOG.md` for every threshold decision with sources
