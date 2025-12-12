# GOTY 2025 Analysis

Clean, reproducible analysis of games released in the Nov 2024 → Nov 2025 window. This project collects, cleans, and analyzes game metadata from three sources (RAWG, Metacritic, Steam) and produces recruiter-ready artifacts and short technical deliverables.

Why this project matters
- Curated shortlist creation: I built per-category Top‑10 lists (by rating) suitable for awards, press kits, and editorial pipelines.
- Cross-source pipeline: data was ingested from public sources, cleaned with interruption-safe pipelines, deduplicated and normalized, and written to `data/processed/` for downstream use.
- Reproducible analysis: all notebooks run headlessly and produce the same CSV outputs so results can be re-generated reliably.

High-level deliverables
- Scrapers & Cleaners: automated scraping and robust cleaners for RAWG, Metacritic and Steam (in `src/`).
- Cleaned datasets: final cleaned CSVs in `data/processed/` (e.g. `rawg_cleaned.csv`, `metacritic_cleaned.csv`, `steam_cleaned.csv`).
- Notebooks (headless-ready): Plotly EDA notebooks per source, an awards-analysis notebook, a RAWG-only Top‑10 notebook (`notebooks/top10_analysis.ipynb`), and an ML demo notebook (uses only Metacritic raw CSV as required).
- Lookup CLI: a small `src/game_lookup.py` utility to inspect games from cleaned data.
- Outputs: per-category Top‑10 CSVs like `data/processed/top10_rawg_best_<category>.csv` and `data/processed/top10_rawg_all.csv`.

What to open first
1. `notebooks/top10_analysis-executed.ipynb` — executed copy showing the RAWG Top‑10 per category and an overall Top‑10.
2. `data/processed/` — contains the per-category CSV exports, combined CSV, and cleaned source CSVs.

Quick notes
- The ML demo uses only the Metacritic raw dataset (required constraint) and includes a short model comparison and a saved joblib model.
- Notebooks are designed to run headless. If you want a PDF of any notebook: export to HTML then print-to-PDF (recommended) or install TeX (`xelatex`) to use LaTeX-based PDF export.

Contact
If you want a 5‑minute walkthrough, email me and I’ll demo the notebooks and the Top‑10 selection logic live.

---
For a technical deep-dive aimed at data analysts, open `README_ANALYST.md` in this repo.
