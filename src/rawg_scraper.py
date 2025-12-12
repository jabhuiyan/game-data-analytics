"""RAWG scraper

This script fetches games from the RAWG API for a date window and writes
results to data/RAWG/rawg_data.csv (or JSON). It validates that fetched
games fall within the requested window.

Usage:
  python src/rawg_scraper.py --start 2024-11-11 --end 2025-11-11 --out data/RAWG/rawg_data.csv

Supports using an API key via RAWG_API_KEY env var or --api-key. If no key
is provided the script will still attempt requests but may be rate-limited.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import time
from datetime import date, datetime
from typing import Dict, Iterable, List, Optional

import requests
from dateutil import parser as dparser
from tqdm import tqdm

RAWG_BASE = "https://api.rawg.io/api"

logger = logging.getLogger("rawg_scraper")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def parse_iso(d: Optional[str]) -> Optional[datetime]:
    if not d:
        return None
    try:
        return dparser.parse(d)
    except Exception:
        return None


def in_window(dt: Optional[datetime], start: date, end: date) -> bool:
    if dt is None:
        return False
    return start <= dt.date() <= end


def fetch_games_api(start: str, end: str, api_key: Optional[str], page_size: int = 40) -> Iterable[Dict]:
    """Yield raw game dicts from RAWG list endpoint and fetch details for each game.

    The function paginates the list endpoint and then requests the detail
    endpoint for each game to fetch description and ESRB.
    """
    params = {"dates": f"{start},{end}", "page_size": page_size}
    if api_key:
        params["key"] = api_key

    url = f"{RAWG_BASE}/games"
    session = requests.Session()
    page = 1
    while True:
        params["page"] = page
        resp = session.get(url, params=params, timeout=30)
        if resp.status_code != 200:
            logger.error("RAWG list request failed %s: %s", resp.status_code, resp.text[:200])
            break
        data = resp.json()
        results = data.get("results", [])
        if not results:
            break

        for r in results:
            # fetch details by slug (more reliable) to get description/esrb
            slug = r.get("slug")
            if not slug:
                continue
            detail_url = f"{RAWG_BASE}/games/{slug}"
            detail_params = {}
            if api_key:
                detail_params["key"] = api_key
            try:
                detail = session.get(detail_url, params=detail_params, timeout=20).json()
            except Exception as e:
                logger.warning("Failed to fetch details for %s (%s)", slug, e)
                detail = {}

            # combine list-level fields and detail fields
            # Safely extract list-like nested fields, some responses use null
            genres_list = [g.get("name") for g in (r.get("genres") or []) if g and g.get("name")] or [g.get("name") for g in (detail.get("genres") or []) if g and g.get("name")]
            tags_list = [t.get("name") for t in (r.get("tags") or []) if t and t.get("name")] or [t.get("name") for t in (detail.get("tags") or []) if t and t.get("name")]
            platforms_list = [p.get("platform", {}).get("name") for p in (r.get("platforms") or []) if p and p.get("platform")] or [p.get("platform", {}).get("name") for p in (detail.get("platforms") or []) if p and p.get("platform")]

            combined = {
                "name": r.get("name"),
                "release_date": r.get("released") or detail.get("released"),
                "genres": genres_list,
                "tags": tags_list,
                "ratings": r.get("rating") or detail.get("rating"),
                "platforms": platforms_list,
                "esrb": (detail.get("esrb_rating") or {}).get("name") if detail.get("esrb_rating") else None,
                "metacritic": r.get("metacritic") or detail.get("metacritic"),
                "description": detail.get("description_raw") or detail.get("description") or "",
                "rawg_slug": slug,
                "rawg_id": r.get("id") or detail.get("id"),
            }
            yield combined

        # pagination
        if not data.get("next"):
            break
        page += 1
        time.sleep(0.5)


def save_to_csv(rows: Iterable[Dict], out_path: str, fieldnames: List[str]) -> None:
    ensure_dir(os.path.dirname(out_path))
    with open(out_path, "w", newline='', encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            # ensure lists are joined
            row = dict(r)
            for k, v in row.items():
                if isinstance(v, list):
                    row[k] = "|".join([str(x) for x in v])
            writer.writerow(row)


def save_to_json(rows: Iterable[Dict], out_path: str) -> None:
    ensure_dir(os.path.dirname(out_path))
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(list(rows), fh, ensure_ascii=False, indent=2)


def main(argv: Optional[List[str]] = None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--start", default="2024-11-11", help="Start date (YYYY-MM-DD)")
    p.add_argument("--end", default="2025-11-11", help="End date (YYYY-MM-DD)")
    p.add_argument("--api-key", default=os.environ.get("RAWG_API_KEY"), help="RAWG API key or set RAWG_API_KEY env var")
    p.add_argument("--out", default="data/RAWG/rawg_data.csv", help="Output path (csv or .json)")
    p.add_argument("--page-size", type=int, default=40)
    args = p.parse_args(argv)

    start_dt = dparser.parse(args.start).date()
    end_dt = dparser.parse(args.end).date()

    logger.info("Fetching RAWG games between %s and %s", start_dt.isoformat(), end_dt.isoformat())
    fetched = []
    for g in tqdm(fetch_games_api(args.start, args.end, args.api_key, page_size=args.page_size)):
        g_release = parse_iso(g.get("release_date"))
        if not in_window(g_release, start_dt, end_dt):
            # Skip games outside the window
            continue
        fetched.append(g)

    if args.out.lower().endswith(".json"):
        save_to_json(fetched, args.out)
    else:
        # choose columns
        fields = [
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
        ]
        save_to_csv(fetched, args.out, fields)

    logger.info("Saved %d RAWG records to %s", len(fetched), args.out)


if __name__ == "__main__":
    main()
