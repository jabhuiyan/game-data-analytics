"""Utility helpers for cleaning datasets"""
from __future__ import annotations

import ast
import os
from datetime import datetime, date
from typing import Any, Iterable, List, Optional

import pandas as pd
from dateutil import parser as dparser


def ensure_dir_for_file(path: str) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


def parse_list_field(val: Any) -> List[str]:
    """Normalize a field that may be a list, a stringified list, or a delimited string.

    Returns a list of stripped strings.
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if x is not None]
    if isinstance(val, str):
        s = val.strip()
        # try list literal
        if s.startswith("[") and s.endswith("]"):
            try:
                arr = ast.literal_eval(s)
                return [str(x).strip() for x in arr if x is not None]
            except Exception:
                pass
        # common separators
        for sep in ["|", ",", ";"]:
            if sep in s:
                return [x.strip() for x in s.split(sep) if x.strip()]
        if s == "":
            return []
        return [s]
    # fallback
    return [str(val)]


def join_list_field(lst: Iterable[str], sep: str = "|") -> str:
    return sep.join([str(x).strip() for x in lst if x is not None and str(x).strip()])


def parse_date_safe(val: Any) -> Optional[datetime]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return dparser.parse(str(val))
    except Exception:
        return None


def within_window(dt: Optional[datetime], start: date, end: date) -> bool:
    if dt is None:
        return False
    return start <= dt.date() <= end
