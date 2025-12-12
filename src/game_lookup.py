#!/usr/bin/env python3
"""Simple CLI to lookup a game's ratings and sales across sources.

Usage:
  python src/game_lookup.py
  # then type a full or partial game name when prompted

The script searches cleaned datasets under data/processed and reports ratings/sales.
"""
from __future__ import annotations

import os
import sys
from difflib import get_close_matches

import pandas as pd

DATA_DIR = "data/processed"
RAWG = os.path.join(DATA_DIR, "rawg_cleaned.csv")
META = os.path.join(DATA_DIR, "metacritic_cleaned.csv")
STEAM = os.path.join(DATA_DIR, "steam_cleaned.csv")


def load_df(path):
    if os.path.exists(path):
        return pd.read_csv(path, dtype=str)
    return None


def find_game_exact(df, col, name):
    if df is None or col not in df.columns:
        return None
    matches = df[df[col].str.strip().str.lower() == name.strip().lower()]
    if not matches.empty:
        return matches.iloc[0].to_dict()
    return None


def find_game_best(df, col, name):
    if df is None or col not in df.columns:
        return None
    # exact match already checked; try close matches on names
    names = df[col].fillna("").tolist()
    close = get_close_matches(name, names, n=3, cutoff=0.7)
    if close:
        cand = df[df[col] == close[0]].iloc[0]
        return cand.to_dict()
    return None


def lookup(name: str):
    results = {}
    rawg_df = load_df(RAWG)
    meta_df = load_df(META)
    steam_df = load_df(STEAM)

    # RAWG: columns -> name, ratings, metacritic
    r = find_game_exact(rawg_df, 'name', name) if rawg_df is not None else None
    if r is None:
        r = find_game_best(rawg_df, 'name', name) if rawg_df is not None else None
    results['RAWG'] = r

    # Metacritic: name, metascore, user_score
    m = find_game_exact(meta_df, 'name', name) if meta_df is not None else None
    if m is None:
        m = find_game_best(meta_df, 'name', name) if meta_df is not None else None
    results['Metacritic'] = m

    # Steam: game_name, estimated_downloads, reviews_like_rate, price
    s = find_game_exact(steam_df, 'game_name', name) if steam_df is not None else None
    if s is None:
        s = find_game_best(steam_df, 'game_name', name) if steam_df is not None else None
    results['Steam'] = s

    return results


def pretty_print(results):
    for src, row in results.items():
        print(f"\n== {src} ==")
        if row is None:
            print("No match found in this source.")
            continue
        if src == 'RAWG':
            print(f"Name: {row.get('name')}")
            print(f"RAWG rating: {row.get('ratings')}")
            print(f"Metacritic (rawg column): {row.get('metacritic')}")
            print(f"Platforms: {row.get('platforms')}")
        elif src == 'Metacritic':
            print(f"Name: {row.get('name')}")
            print(f"Metascore: {row.get('metascore')}")
            print(f"User score: {row.get('user_score')}")
            print(f"Platform: {row.get('platform')}")
        elif src == 'Steam':
            print(f"Name: {row.get('game_name')}")
            print(f"Estimated downloads: {row.get('estimated_downloads')}")
            print(f"Reviews like rate: {row.get('reviews_like_rate')}")
            print(f"Price: {row.get('price')}")


def main():
    if len(sys.argv) > 1:
        name = ' '.join(sys.argv[1:])
    else:
        name = input('Enter full or partial game name: ').strip()
    if not name:
        print('No name provided, exiting.')
        return
    res = lookup(name)
    pretty_print(res)


if __name__ == '__main__':
    main()
