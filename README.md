<p align="center">
  <img src="https://www.gamewallpapers.com/img_script/wallpaper_dir/img.php?src=wallpaper_clair_obscur_expedition_33_06_2560x1080.jpg&height=506&sharpen" alt="Clair Obscur: Expedition 33" width="100%" />
</p>

<h1 align="center">🎮 GOTY 2025 Analysis</h1>

<p align="center">
  <b>Clean and reproducible data analysis of games released between Nov 2024 → Nov 2025</b>
</p>

<p align="center">
  RAWG • Metacritic • Steam • Python • Plotly • Reproducible Pipelines
</p>

---

## ✨ Project Overview

This project collects, cleans, and analyzes **video game metadata** from three major public sources — **RAWG, Metacritic, and Steam** — to produce **award-style shortlists**, **business-ready analytics**, and **reproducible technical artifacts**.

The focus is not just analysis, but **end-to-end data engineering discipline**:
- interruption-safe scraping
- deduplication & normalization
- deterministic outputs suitable for downstream use

---

## 🧠 Why This Project Matters

**For recruiters, analysts, and data teams**

- 🏆 **Curated shortlist creation**  
  Built per-category and overall **Top-10 lists by rating**, suitable for awards, editorial pipelines, or marketing spotlights.

- 🔗 **Cross-source data pipeline**  
  Public data ingested, cleaned, normalized, and written to `data/processed/` for reliable reuse.

- ♻️ **Reproducible analysis**  
  All notebooks run headlessly and regenerate identical CSV outputs — no manual steps, no hidden state.

---

## 📊 Visual Snapshots

<p align="center">
  <img src="https://github.com/jabhuiyan/game-data-analytics/blob/main/figs/fig3.png?raw=true" width="80%" />
</p>

<p align="center">
  <img src="https://github.com/jabhuiyan/game-data-analytics/blob/main/figs/newplotPlatforms.png?raw=true" width="80%" />
</p>

<p align="center">
  <img src="https://github.com/jabhuiyan/game-data-analytics/blob/main/figs/newplotTopDevs.png?raw=true" width="80%" />
</p>

> All figures are generated via Plotly and saved as artifacts for non-technical stakeholders.

---

## 📦 High-Level Deliverables

### 🔧 Scrapers & Cleaners
- Automated scrapers and robust cleaning pipelines for:
  - RAWG
  - Metacritic
  - Steam  
- Located in `src/`, designed to resume safely after interruptions.

### 🗂 Cleaned Datasets
Final normalized CSVs in `data/processed/`, including:
- `rawg_cleaned.csv`
- `metacritic_cleaned.csv`
- `steam_cleaned.csv`

### 📓 Notebooks (Headless-Ready)
- Plotly EDA notebooks per source
- Awards & Top-10 analysis
- RAWG-only Top-10 notebook
- ML demo notebook (Metacritic raw CSV only, per constraint)

### 🔍 Lookup CLI
- `src/game_lookup.py`  
  Lightweight CLI to inspect cleaned game entries without opening notebooks.

---

## 📈 Business-Ready Analytics (Key Outputs)

| File | What It Shows | Business Value |
|-----|--------------|----------------|
| `rawg_genre_counts.csv` | Releases per genre | Identify crowded vs. growing categories |
| `rawg_platform_counts.csv` | Platform distribution | Platform market share & prioritization |
| `top10_rawg_best_overall.csv` | Highest-rated titles | Awards, editorial, and marketing shortlists |

---

## 🚀 What to Open First

1. **`notebooks/top10_analysis-executed.ipynb`**  
   → Fully executed notebook showing Top-10s per category and overall.

2. **`data/processed/`**  
   → Cleaned datasets and per-category CSV exports ready for use.

---

## 📝 Quick Notes

- 🤖 **ML Demo**  
  Uses *only* the Metacritic raw dataset (explicit constraint)  
  Includes:
  - model comparison
  - evaluation
  - saved `joblib` model

- 📄 **Notebook Exporting**  
  Designed to run headlessly  
  - Recommended: export to HTML → print to PDF  
  - Alternative: LaTeX (`xelatex`) PDF export

---

## 📫 Contact

If you want a **5-minute walkthrough**, I’m happy to:
- demo the notebooks
- explain the Top-10 selection logic
- discuss design decisions and trade-offs

📧 *Email me and I’ll walk you through it live.*

---

### 🔍 Technical Deep-Dive

For a more detailed, analyst-focused breakdown of:
- schema decisions
- cleaning logic
- modeling choices  

➡️ Open **`README_ANALYST.md`** in this repo.

