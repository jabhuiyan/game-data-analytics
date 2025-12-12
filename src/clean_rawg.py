"""Cleaning script for RAWG data with interruption-proofing and logging.

Writes `data/processed/rawg_cleaned.csv`. If interrupted the script will
resume from a partial file `*.inprogress` and will log errors to
`logs/clean_rawg.log`.
"""
from __future__ import annotations

import logging
import os
import traceback
from datetime import date
from typing import Optional

import pandas as pd

from clean_utils import (
    ensure_dir_for_file,
    join_list_field,
    parse_date_safe,
    parse_list_field,
    within_window,
)


INPUT_CSV = "data/RAWG/rawg_data.csv"
INPUT_JSON = "data/RAWG/rawg_data.json"
OUT_CSV = "data/processed/rawg_cleaned.csv"
OUT_PART = OUT_CSV + ".inprogress"
LOG_PATH = "logs/clean_rawg.log"


def setup_logger() -> logging.Logger:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    logger = logging.getLogger("clean_rawg")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(LOG_PATH)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    fh.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(fh)
    return logger


def process_chunks(logger: logging.Logger) -> None:
    if not os.path.exists(INPUT_CSV) and not os.path.exists(INPUT_JSON):
        raise FileNotFoundError("No RAWG data found. Run src/rawg_scraper.py first.")

    # Determine already-processed keys (name||release_date) to skip on resume
    seen = set()
    if os.path.exists(OUT_PART):
        try:
            df_seen = pd.read_csv(OUT_PART, dtype=str)
            if "name" in df_seen.columns:
                seen = set((df_seen["name"].fillna("") + "||" + df_seen.get("release_date", "").fillna("")).tolist())
                logger.info("Resuming: found %d already-processed rows in %s", len(seen), OUT_PART)
        except Exception:
            logger.warning("Could not read existing partial output; will reprocess everything")
            seen = set()

    chunk_iter = pd.read_csv(INPUT_CSV, dtype=str, chunksize=500) if os.path.exists(INPUT_CSV) else pd.read_json(INPUT_JSON, lines=False)
    total_written = 0
    header_written = os.path.exists(OUT_PART)
    start = date(2024, 11, 11)
    end = date(2025, 11, 11)

    for chunk in chunk_iter:
        try:
            # Ensure strings
            chunk = chunk.astype(object).where(pd.notnull(chunk), None)

            # Build key and skip already processed
            if "name" not in chunk.columns:
                logger.warning("Chunk missing 'name' column, skipping chunk")
                continue
            key_series = chunk["name"].fillna("") + "||" + chunk.get("release_date", "").fillna("")
            mask_new = ~key_series.isin(seen)
            chunk = chunk[mask_new]
            if chunk.empty:
                continue

            # Normalize list-like columns
            for col in ["genres", "tags", "platforms"]:
                if col in chunk.columns:
                    chunk[col] = chunk[col].fillna("").apply(parse_list_field).apply(lambda lst: join_list_field(lst))

            # Parse release_date to ISO
            def _fmt_date(v):
                dt = parse_date_safe(v)
                return dt.date().isoformat() if dt else ""

            chunk["release_date"] = chunk.get("release_date", "").apply(_fmt_date)

            # Filter by window
            chunk = chunk[chunk["release_date"].apply(lambda s: within_window(parse_date_safe(s), start, end))]
            if chunk.empty:
                continue

            # Fill missing ESRB
            if "esrb" in chunk.columns:
                chunk["esrb"] = chunk["esrb"].fillna("Unknown").astype(str).str.strip()

            # Select columns for Tableau-friendly output
            output_cols = [
                c for c in [
                    "rawg_id",
                    "rawg_slug",
                    "name",
                    "release_date",
                    "genres",
                    "tags",
                    "ratings",
                    "platforms",
                    "esrb",
                    "metacritic",
                    "description",
                ] if c in chunk.columns
            ]
            if not output_cols:
                logger.warning("No expected columns present in chunk; skipping")
                continue

            ensure_dir_for_file(OUT_PART)
            # Append to partial file
            chunk.to_csv(OUT_PART, mode="a", index=False, header=not header_written, columns=output_cols)
            header_written = True

            # Update seen keys
            seen.update((chunk["name"].fillna("") + "||" + chunk.get("release_date", "").fillna("")).tolist())
            total_written += len(chunk)
            logger.info("Wrote %d rows (total_written=%d)", len(chunk), total_written)
        except Exception:
            logger.error("Error processing chunk: %s", traceback.format_exc())
            raise

    # Finalize: dedupe and move to final CSV
    if os.path.exists(OUT_PART):
        df_final = pd.read_csv(OUT_PART, dtype=str)
        # Drop duplicates by name+release_date
        if "name" in df_final.columns:
            keycols = [c for c in ["name", "release_date"] if c in df_final.columns]
            df_final = df_final.drop_duplicates(subset=keycols)
        ensure_dir_for_file(OUT_CSV)
        df_final.to_csv(OUT_CSV, index=False)
        logger.info("Finalized cleaned RAWG CSV to %s (%d rows)", OUT_CSV, len(df_final))
        # remove partial
        try:
            os.remove(OUT_PART)
        except Exception:
            logger.warning("Could not remove partial file %s", OUT_PART)


def main() -> None:
    logger = setup_logger()
    try:
        process_chunks(logger)
    except Exception:
        logger.error("Cleaning failed: %s", traceback.format_exc())
        print("Cleaning failed: see", LOG_PATH)


if __name__ == "__main__":
    main()
