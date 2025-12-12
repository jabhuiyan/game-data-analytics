"""Cleaning script for Steam data with interruption-proofing and logging.

Writes `data/processed/steam_cleaned.csv`. Resumes from partial output
and logs to `logs/clean_steam.log` on errors.
"""
from __future__ import annotations

import logging
import os
import traceback
from datetime import date

import pandas as pd

from clean_utils import ensure_dir_for_file, join_list_field, parse_date_safe, parse_list_field, within_window


INPUT = "data/steam2025/bestSelling_games.csv"
OUT = "data/processed/steam_cleaned.csv"
OUT_PART = OUT + ".inprogress"
LOG_PATH = "logs/clean_steam.log"


def setup_logger() -> logging.Logger:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    logger = logging.getLogger("clean_steam")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(LOG_PATH)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    fh.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(fh)
    return logger


def process(logger: logging.Logger) -> None:
    if not os.path.exists(INPUT):
        raise FileNotFoundError(f"Steam input not found: {INPUT}")

    seen = set()
    if os.path.exists(OUT_PART):
        try:
            df_seen = pd.read_csv(OUT_PART, dtype=str)
            seen = set((df_seen.get("game_name", "").fillna("") + "||" + df_seen.get("release_date", "").fillna("")).tolist())
            logger.info("Resuming steam cleaning; %d rows already present", len(seen))
        except Exception:
            logger.warning("Could not read existing partial output; will reprocess everything")
            seen = set()

    total_written = 0
    header_written = os.path.exists(OUT_PART)
    start = date(2024, 11, 11)
    end = date(2025, 11, 11)

    for chunk in pd.read_csv(INPUT, dtype=str, chunksize=500):
        try:
            chunk = chunk.astype(object).where(pd.notnull(chunk), None)
            key_series = chunk.get("game_name", "").fillna("") + "||" + chunk.get("release_date", "").fillna("")
            chunk = chunk[~key_series.isin(seen)]
            if chunk.empty:
                continue

            if "user_defined_tags" in chunk.columns:
                chunk["user_defined_tags"] = chunk["user_defined_tags"].fillna("").apply(parse_list_field).apply(lambda l: join_list_field(l))

            if "supported_os" in chunk.columns:
                chunk["supported_os"] = chunk["supported_os"].fillna("").apply(parse_list_field).apply(lambda l: join_list_field(l))

            # parse release_date to ISO
            def _fmt(v):
                dt = parse_date_safe(v)
                return dt.date().isoformat() if dt else ""

            chunk["release_date"] = chunk.get("release_date", "").apply(_fmt)
            chunk = chunk[chunk["release_date"].apply(lambda s: within_window(parse_date_safe(s), start, end))]
            if chunk.empty:
                continue

            ensure_dir_for_file(OUT_PART)
            # keep estimated_downloads and reviews_like_rate if present for sales/ranking analysis
            out_cols = [c for c in ["game_name", "release_date", "developer", "user_defined_tags", "supported_os", "price", "estimated_downloads", "reviews_like_rate"] if c in chunk.columns]
            chunk.to_csv(OUT_PART, mode="a", index=False, header=not header_written, columns=out_cols)
            header_written = True

            seen.update((chunk.get("game_name", "").fillna("") + "||" + chunk.get("release_date", "").fillna("")).tolist())
            total_written += len(chunk)
            logger.info("Wrote %d rows (total_written=%d)", len(chunk), total_written)
        except Exception:
            logger.error("Error processing chunk: %s", traceback.format_exc())
            raise

    # finalize
    if os.path.exists(OUT_PART):
        df_final = pd.read_csv(OUT_PART, dtype=str)
        dedup_cols = [c for c in ["game_name", "release_date"] if c in df_final.columns]
        if dedup_cols:
            df_final = df_final.drop_duplicates(subset=dedup_cols)
        ensure_dir_for_file(OUT)
        df_final.to_csv(OUT, index=False)
        logger.info("Finalized steam cleaned CSV to %s (%d rows)", OUT, len(df_final))
        try:
            os.remove(OUT_PART)
        except Exception:
            logger.warning("Could not remove partial file %s", OUT_PART)


def main() -> None:
    logger = setup_logger()
    try:
        process(logger)
    except Exception:
        logger.error("Cleaning failed: %s", traceback.format_exc())
        print("Cleaning failed: see", LOG_PATH)


if __name__ == "__main__":
    main()
