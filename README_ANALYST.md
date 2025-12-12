# GOTY 2025 Analysis — Detailed README for Data Analysts

This document explains the full pipeline, design decisions, cleaning logic, notebooks, and how to reproduce everything. It is intended for data scientists, analysts, and engineers who want to audit, extend, or reproduce the work.

Contents
- Project goals
- Data sources & schemas
- ETL and cleaning
- Rating, deduplication & category matching logic
- Notebooks and headless execution
- Outputs
- Reproducibility, tests & quality gates
- Troubleshooting
- Next steps and improvements

Project goals
- Collect all candidate games released between 2024-11-11 and 2025-11-11.
- Produce interruption-safe cleaning pipelines for RAWG, Metacritic, and Steam.
- Generate per-category Top‑10 lists (by rating) and merged outputs for awards analysis.
- Provide lightweight ML demo limited to Metacritic raw data (`data/metacritic/metacritic_dataset_raw.csv`).

Data sources & where to find them
- RAWG: `data/RAWG/rawg_data.csv` (original raw pull used by `src/rawg_scraper.py`). Key fields captured: name, release_date, genres, tags, ratings, platforms, esrb, metacritic, description.
- Metacritic: `data/metacritic/` contains raw and cleaned files. The ML demo uses `data/metacritic/metacritic_dataset_raw.csv` per project constraint.
- Steam: `data/steam2025/bestSelling_games.csv` (used by cleaners). Cleaned versions are stored in `data/processed/`.

Repository layout (important files)
- `src/` — scrapers, cleaners and small CLI tools (e.g., `rawg_scraper.py`, `clean_rawg.py`, `clean_metacritic.py`, `clean_steam.py`, `game_lookup.py`).
- `data/` — raw inputs and `processed/` outputs.
- `notebooks/` — all notebooks including `top10_analysis.ipynb` (RAWG-focused Top‑10), `awards_analysis.ipynb`, EDA notebooks per source, and the ML demo. Executed versions (with outputs) have `-executed.ipynb` suffix.

Cleaning & interruption-safe patterns
- Each cleaner is designed to be interruption-tolerant. Pattern used:
  - Process source rows in chunks where feasible.
  - Write `.inprogress` partial CSVs at safe checkpoints.
  - On restart, the cleaner picks up from the last complete chunk.
  - This minimizes lost progress during long scrapes or when rate-limits apply.

Rating score computation
- A common comparable column `rating_score` is computed to rank titles across sources:
  - Prefer explicit `metacritic` numeric score when present.
  - Else, use `ratings` (RAWG) or `user_score` scaled to 0–100 (e.g., `ratings * 20`).
  - `rating_score` stored as float and used for sorting and Top‑10 selection.

Deduplication strategy
- For per-category Top‑10s we deduplicate games by a normalized `name_key`:
  - `name_key = name.strip().lower()`
  - Sorting priority: `rating_score`, then `metacritic`, then `ratings` (descending). We keep the first occurrence per `name_key` after sorting.
  - This keeps the highest-rated record for identically named entries (editions, variants remain separate unless names normalize equal).

Category matching logic (how Top‑10s are formed)
- Categories are defined in `notebooks/top10_analysis.ipynb` (the `CATEGORY_KEYWORDS` dictionary).
- Matching is heuristic, vectorized and fast:
  - For each category, build a safe regex from keywords (escape special chars).
  - Apply `.str.contains(regex, case=False, na=False)` across multiple text fields (`genres`, `tags`, `name`, `description` where available).
  - The union of matches across fields forms the category membership.
  - From the matched rows we sort by `rating_score`, drop NA `rating_score`, and keep top 10.

Per-category output files
- For RAWG the notebook writes one CSV per category named:
  - `data/processed/top10_rawg_best_<slug>.csv` (slug is category lowercased and sanitized)
  - Also writes a combined `data/processed/top10_rawg_all.csv` containing all per-category rows with added `category` and `source` columns.

Notebooks and what each does
- `notebooks/top10_analysis.ipynb` — RAWG-only Top‑10 generator. Runs headless and writes per-category CSVs and a combined CSV. Prints human-readable Top‑10 lists in separate cells (one cell per category). The top-10 logic is vectorized for speed.
- `notebooks/awards_analysis.ipynb` — per-source awards analysis. This notebook was refactored to avoid constructing a brittle unified table; it computes Top‑10s per source.
- `notebooks/*.ipynb` — EDA notebooks per source (Plotly visualizations) and the ML demo notebook.
- ML demo: uses `data/metacritic/metacritic_dataset_raw.csv` only (as required). It includes:
  - a small feature table and preprocessing pipeline,
  - model comparison (a couple of baseline models plus one tuned tree-based model),
  - metrics (MAE/RMSE/accuracy depending on the target), and
  - saves the final model with `joblib`.

Running everything locally (reproducible steps)
1) Create & activate venv (Python 3.12 recommended):
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```
2) Scrape / re-run cleaners (if you want fresh data):
```bash
# run a cleaner or scraper script in src/ (examples)
python src/rawg_scraper.py    # respects rate-limits and date-window
python src/clean_rawg.py     # produces data/processed/rawg_cleaned.csv
```
3) Run the RAWG Top-10 notebook headless (nbconvert):
```bash
source .venv/bin/activate
python -m nbconvert --to notebook --execute notebooks/top10_analysis.ipynb --output top10_analysis-executed.ipynb --output-dir=notebooks --ExecutePreprocessor.timeout=1200
```
4) Inspect `data/processed/` for per-category CSVs and the combined CSV.

Notes about headless runs & PDF export
- Notebooks are designed to run without manual interaction. If nbconvert complains about PDF exporting, it is usually because TeX (`xelatex`) is missing. The simple workaround is to export to HTML and then print-to-PDF from your browser or use `wkhtmltopdf`.

Troubleshooting common issues
- FileNotFoundError for RAWG source: ensure `data/RAWG/rawg_data.csv` is present or that cleaners have run.
- pyzmq wheel build errors when pip installing: install `libzmq3-dev` (Debian/Ubuntu) or the distro equivalent, upgrade `pip` and `wheel`, and retry `pip install pyzmq`.
- Regex warnings: some category keyword lists contain groups or special chars; the code escapes keywords but you may still see warnings if a keyword has parenthesis — safe to ignore or remove capturing groups.

Quality gates and validation
- Build: no compiled build — PASS (pure Python). 
- Lint/Typecheck: no project-wide linter run included; add `flake8`/`ruff` if desired.
- Tests: there are no automated unit tests included; recommend a small test suite to check cleaners and the top-10 output generation.

Assumptions & limitations
- Matching is heuristic and substring-based; noisy tags or different naming conventions may affect recall/precision.
- Deduplication is name-based and does not attempt fuzzy matching across variants — this avoids accidental merges but may leave some duplicates.

Next steps (recommended)
- Add small unit tests for cleaners and the category matching logic (happy path + edge cases).
- Add fuzzy-matching deduplication (e.g., using fuzzywuzzy/rapidfuzz) optionally with manual review.
- Expand category keyword lists or provide a small UI for manual candidate curation.
- Add a CI job that executes notebooks headless and verifies expected CSV outputs exist.

Contact & provenance
- The notebook execution logs and executed notebook copies are stored under `notebooks/` with `-executed.ipynb` suffix when run.
- If you need additional breakdowns, alternate category lists, or help deploying this pipeline, open an issue or contact me directly.
