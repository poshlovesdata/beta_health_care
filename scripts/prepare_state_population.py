#!/usr/bin/env python3
"""
Fetch and prepare Nigeria state-level population CSV for the simulator.

Usage:
  python scripts/prepare_state_population.py --url <direct_csv_url> \
      [--raw-out data/raw/nga_admpop_adm1_2022.csv] \
      [--out data/processed/population/state_population_2022.csv]

Notes:
  - The script expects an HDX (Humanitarian Data Exchange) CSV that contains
    Administrative Level 1 (state) population figures for Nigeria circa 2022.
  - If the resource is sex/age disaggregated with multiple numeric columns,
    the script will sum numeric columns to produce a per‑state total.
  - State names are normalized (e.g., removing "State" suffix; mapping FCT Abuja → FCT)
    to match the simulator's `REGIONS` list.
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

try:
    import requests
except ImportError:
    requests = None


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_POP_DIR = DATA_DIR / "processed" / "population"
PROCESSED_POP_DIR.mkdir(parents=True, exist_ok=True)


NAME_CANDIDATES = [
    "state",
    "adm1_name",
    "adm1_en",
    "adm1name",
    "admin1_name",
    "ADM1_NAME",
]
POP_CANDIDATES = [
    "population",
    "totl_pop",
    "total_pop",
    "tot_pop",
    "pop",
]

NORMALIZE_NAME_MAP = {
    "fct abuja": "FCT",
    "abuja": "FCT",
    "abuja fct": "FCT",
    "fct": "FCT",
}


def download_csv(url: str, out_path: Path):
    if requests is None:
        raise RuntimeError("requests not installed. Run: pip install requests")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    out_path.write_bytes(resp.content)


def detect_columns(df: pd.DataFrame):
    cols_lower = {c.lower().strip(): c for c in df.columns}
    name_col = next((cols_lower[c] for c in cols_lower if c in NAME_CANDIDATES), None)
    pop_col = next((cols_lower[c] for c in cols_lower if c in POP_CANDIDATES), None)
    return name_col, pop_col


def normalize_state_name(name: str) -> str:
    n = (name or "").strip()
    n_low = n.lower().replace("state", "").strip()
    if n_low in NORMALIZE_NAME_MAP:
        return NORMALIZE_NAME_MAP[n_low]
    # Title-case but keep acronyms
    return n_low.title()


def build_state_population(df: pd.DataFrame) -> pd.DataFrame:
    name_col, pop_col = detect_columns(df)
    if not name_col:
        # Fallback: first object col
        obj_cols = [c for c in df.columns if df[c].dtype == object]
        name_col = obj_cols[0] if obj_cols else df.columns[0]

    if not pop_col:
        # Sum all numeric columns to derive total
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if not num_cols:
            raise ValueError("No numeric columns found to compute population totals")
        df["__pop_total__"] = df[num_cols].fillna(0).sum(axis=1)
        pop_col = "__pop_total__"

    df_out = (
        df[[name_col, pop_col]]
        .rename(columns={name_col: "state", pop_col: "population"})
        .assign(state=lambda d: d["state"].map(normalize_state_name))
        .groupby("state", as_index=False)["population"].sum()
        .sort_values("state")
    )
    # Integerize
    df_out["population"] = df_out["population"].astype(int)
    return df_out


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fetch and prepare state population CSV")
    parser.add_argument("--url", required=True, help="Direct CSV URL for Nigeria adm1 population (HDX)")
    parser.add_argument("--raw-out", default=str(RAW_DIR / "nga_admpop_adm1_2022.csv"), help="Path to save raw CSV")
    parser.add_argument("--out", default=str(PROCESSED_POP_DIR / "state_population_2022.csv"), help="Path to save prepared CSV")
    args = parser.parse_args(argv)

    raw_path = Path(args.raw_out)
    out_path = Path(args.out)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading: {args.url}")
    download_csv(args.url, raw_path)
    print(f"Saved raw CSV to: {raw_path}")

    df_raw = pd.read_csv(raw_path)
    df_state = build_state_population(df_raw)
    df_state.to_csv(out_path, index=False)
    print(f"Wrote prepared state population CSV to: {out_path}")


if __name__ == "__main__":
    sys.exit(main())