"""Cleaning script for Metacritic data with interruption-proofing and logging.

Writes `data/processed/metacritic_cleaned.csv`. Resumes from partial output
`*.inprogress` and logs to `logs/clean_metacritic.log` on errors.
"""
from __future__ import annotations

import logging
import os
import traceback
from datetime import date

import pandas as pd

from clean_utils import ensure_dir_for_file, join_list_field, parse_date_safe, parse_list_field, within_window


IN_CLEAN = "data/metacritic/metacritic_dataset_clean.csv"
IN_RAW = "data/metacritic/metacritic_dataset_raw.csv"
OUT = "data/processed/metacritic_cleaned.csv"
OUT_PART = OUT + ".inprogress"
LOG_PATH = "logs/clean_metacritic.log"


def setup_logger() -> logging.Logger:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    logger = logging.getLogger("clean_metacritic")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(LOG_PATH)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    fh.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(fh)
    return logger


def read_input_iter():
    path = IN_CLEAN if os.path.exists(IN_CLEAN) else IN_RAW
    if not os.path.exists(path):
        raise FileNotFoundError("No metacritic data found in data/metacritic/")
    return pd.read_csv(path, dtype=str, chunksize=500)


def process(logger: logging.Logger) -> None:
    # load seen keys if resuming
    seen = set()
    if os.path.exists(OUT_PART):
        try:
            df_seen = pd.read_csv(OUT_PART, dtype=str)
            seen = set((df_seen.get("name", "").fillna("") + "||" + df_seen.get("platform", "").fillna("") + "||" + df_seen.get("release_date", "").fillna("")).tolist())
            logger.info("Resuming metacritic cleaning; %d rows already present", len(seen))
        except Exception:
            logger.warning("Could not read existing partial output; will reprocess everything")
            seen = set()

    total_written = 0
    header_written = os.path.exists(OUT_PART)
    start = date(2024, 11, 11)
    end = date(2025, 11, 11)

    for chunk in read_input_iter():
        try:
            chunk = chunk.astype(object).where(pd.notnull(chunk), None)
            # build key
            key_series = chunk.get("name", "").fillna("") + "||" + chunk.get("platform", "").fillna("") + "||" + chunk.get("release_date", "").fillna("")
            chunk = chunk[~key_series.isin(seen)]
            if chunk.empty:
                continue

            for col in ["publisher", "developer"]:
                if col in chunk.columns:
                    chunk[col] = chunk[col].fillna("").apply(parse_list_field).apply(lambda l: join_list_field(l))

            if "genre" in chunk.columns:
                chunk["genre"] = chunk["genre"].fillna("").apply(parse_list_field).apply(lambda l: join_list_field(l))

            # parse release_date to ISO and filter
            def _fmt(v):
                dt = parse_date_safe(v)
                return dt.date().isoformat() if dt else ""

            chunk["release_date"] = chunk.get("release_date", "").apply(_fmt)
            chunk = chunk[chunk["release_date"].apply(lambda s: within_window(parse_date_safe(s), start, end))]
            if chunk.empty:
                continue

            # standardize columns
            for c in ["platform", "genre"]:
                if c in chunk.columns:
                    chunk[c] = chunk[c].astype(str).str.strip()

            cols = [c for c in ["name", "platform", "release_date", "metascore", "user_score", "developer", "publisher", "genre"] if c in chunk.columns]
            ensure_dir_for_file(OUT_PART)
            chunk.to_csv(OUT_PART, mode="a", index=False, header=not header_written, columns=cols)
            header_written = True

            # update seen and counters
            seen.update((chunk.get("name", "").fillna("") + "||" + chunk.get("platform", "").fillna("") + "||" + chunk.get("release_date", "").fillna("")).tolist())
            total_written += len(chunk)
            logger.info("Wrote %d rows (total_written=%d)", len(chunk), total_written)
        except Exception:
            logger.error("Error processing chunk: %s", traceback.format_exc())
            raise

    # finalize
    if os.path.exists(OUT_PART):
        df_final = pd.read_csv(OUT_PART, dtype=str)
        dedup_cols = [c for c in ["name", "platform", "release_date"] if c in df_final.columns]
        if dedup_cols:
            df_final = df_final.drop_duplicates(subset=dedup_cols)
        ensure_dir_for_file(OUT)
        df_final.to_csv(OUT, index=False)
        logger.info("Finalized metacritic cleaned CSV to %s (%d rows)", OUT, len(df_final))
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
