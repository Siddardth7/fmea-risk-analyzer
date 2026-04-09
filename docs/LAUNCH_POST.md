# Launch Day Assets

## LinkedIn Post

---

Just shipped: FMEA Risk Prioritization Tool — live on Streamlit Cloud

I built a Python tool that automates the tedious parts of Process FMEA for aerospace manufacturing:

- Upload any CSV/Excel FMEA file (or use the built-in 30-row composite panel demo)
- Instant RPN calculation + AIAG FMEA-4 criticality flagging
- Color-coded risk table (Red/Yellow/Green by tier)
- Interactive Pareto chart — see which 20% of failure modes drive 80% of risk
- Severity x Occurrence heatmap
- One-click PDF and Excel export

Built with Python, Streamlit, and Plotly. 61 tests. Every threshold decision documented with AIAG FMEA-4 source citations.

Live demo: https://fmea-risk-analyzer.streamlit.app
GitHub: https://github.com/Siddardth7/fmea-risk-analyzer

If you work in aerospace, automotive, or any manufacturing quality role — this is the kind of tool that turns a 2-hour Excel session into a 30-second analysis.

#Aerospace #Manufacturing #Python #FMEA #QualityEngineering #Streamlit #OpenSource

---

## Resume Bullet (copy-paste ready)

**FMEA Risk Prioritization Tool** — Built a Python-based FMEA analysis tool that automates RPN scoring,
AIAG FMEA-4 criticality flagging, and risk visualization for aerospace manufacturing. Delivered as a
Streamlit web app with interactive Pareto + heatmap charts, live filtering, and one-click PDF/Excel
export. Deployed on Streamlit Cloud. (Python, Streamlit, Plotly, openpyxl, fpdf2)
GitHub: https://github.com/Siddardth7/fmea-risk-analyzer
Live Demo: https://fmea-risk-analyzer.streamlit.app

---

## Deployment Checklist (complete before posting)

- [ ] `https://fmea-risk-analyzer.streamlit.app` loads demo dataset correctly
- [ ] Excel download produces a readable .xlsx with color-coded rows
- [ ] PDF download produces a 3-page PDF with Pareto + heatmap charts
- [ ] Filters (RPN slider + Severity toggle) update table and badges in real time
- [ ] GitHub repo is **public** (Settings > Danger Zone > Change visibility)
- [ ] Repo pinned to GitHub profile (Profile > Customize profile > Pin repositories)
- [ ] Screenshots captured and committed to `assets/`
- [ ] README live URL updated from placeholder to real Streamlit URL
- [ ] LinkedIn post published
- [ ] Resume updated with GitHub + live demo URL

---

## Streamlit Cloud Deploy Steps

1. Go to **share.streamlit.io** and sign in with GitHub
2. Click **New app**
3. Repository: `Siddardth7/fmea-risk-analyzer`
4. Branch: `main`
5. Main file path: `app.py`
6. Click **Deploy** — takes ~2 minutes
7. Copy the live URL and update README.md + LAUNCH_POST.md
