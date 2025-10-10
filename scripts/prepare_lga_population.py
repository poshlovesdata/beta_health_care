#!/usr/bin/env python3
"""
Fetch and prepare Nigeria LGA-level (adm2) population CSV for the simulator.

Usage:
  # Option A: Download from URL (HDX direct CSV)
  python scripts/prepare_lga_population.py --url <direct_csv_url> \
      [--raw-out data/raw/nga_admpop_adm2_2022.csv] \
      [--out data/processed/population/lga_population_2022.csv]

  # Option B: Use an existing local CSV (already downloaded)
  python scripts/prepare_lga_population.py --in data/raw/lga_pop_data.csv \
      [--out data/processed/population/lga_population_2022.csv]

Notes:
  - Expects an HDX CSV containing Administrative Level 2 (LGA) population
    figures for Nigeria circa 2022.
  - If the resource is sex/age disaggregated with multiple numeric columns,
    the script will sum numeric columns to produce per‑LGA totals.
  - State and LGA names are normalized to match the simulator's `REGIONS` list.
"""

import argparse
from pathlib import Path
import sys
import os

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


STATE_NAME_CANDIDATES = [
    "state",
    "adm1_name",
    "adm1_en",
    "adm1name",
    "admin1_name",
    "ADM1_NAME",
]
LGA_NAME_CANDIDATES = [
    "lga",
    "adm2_name",
    "adm2_en",
    "adm2name",
    "admin2_name",
    "ADM2_NAME",
]
POP_CANDIDATES = [
    "population",
    "totl_pop",
    "total_pop",
    "tot_pop",
    "pop",
    "t_tl",  # HDX adm2 total column in some releases
]

NORMALIZE_STATE_MAP = {
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
    state_col = next((cols_lower[c] for c in cols_lower if c in STATE_NAME_CANDIDATES), None)
    lga_col = next((cols_lower[c] for c in cols_lower if c in LGA_NAME_CANDIDATES), None)
    pop_col = next((cols_lower[c] for c in cols_lower if c in POP_CANDIDATES), None)
    return state_col, lga_col, pop_col


def coerce_numeric_like_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convert string columns with thousands separators into numeric.

    Many HDX CSVs store numbers like "57,686" as strings. This helper removes
    commas and casts such columns to numeric so downstream aggregation works.
    """
    df = df.copy()
    for c in df.columns:
        if df[c].dtype == object:
            # Try removing commas and casting to numeric; keep if mostly successful
            cleaned = df[c].astype(str).str.replace(",", "", regex=False)
            numeric = pd.to_numeric(cleaned, errors="coerce")
            # If at least 70% of non-null values convert to numbers, adopt
            non_null = cleaned.notna().sum()
            numeric_count = numeric.notna().sum()
            if non_null > 0 and numeric_count / non_null >= 0.7:
                df[c] = numeric
    return df


def normalize_state_name(name: str) -> str:
    n = (name or "").strip()
    n_low = n.lower().replace("state", "").strip()
    if n_low in NORMALIZE_STATE_MAP:
        return NORMALIZE_STATE_MAP[n_low]
    return n_low.title()


def normalize_lga_name(name: str) -> str:
    n = (name or "").strip()
    n_low = n.lower().replace("lga", "").strip()
    # Remove any trailing admin qualifiers in parentheses
    if "(" in n_low and ")" in n_low:
        try:
            n_low = n_low[: n_low.index("(")].strip()
        except Exception:
            pass
    return n_low.title()


def build_lga_population(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure numeric-like columns are parsed correctly (e.g., "57,686")
    df = coerce_numeric_like_columns(df)
    state_col, lga_col, pop_col = detect_columns(df)

    if not state_col:
        obj_cols = [c for c in df.columns if df[c].dtype == object]
        state_col = obj_cols[0] if obj_cols else df.columns[0]

    if not lga_col:
        obj_cols = [c for c in df.columns if df[c].dtype == object]
        # choose the next object col differing from state_col
        candidates = [c for c in obj_cols if c != state_col]
        lga_col = candidates[0] if candidates else df.columns[1]

    if not pop_col:
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if not num_cols:
            raise ValueError("No numeric columns found to compute population totals")
        df["__pop_total__"] = df[num_cols].fillna(0).sum(axis=1)
        pop_col = "__pop_total__"

    df_out = (
        df[[state_col, lga_col, pop_col]]
        .rename(columns={state_col: "state", lga_col: "lga", pop_col: "population"})
        .assign(state=lambda d: d["state"].map(normalize_state_name))
        .assign(lga=lambda d: d["lga"].map(normalize_lga_name))
        .groupby(["state", "lga"], as_index=False)["population"].sum()
        .sort_values(["state", "lga"])
    )
    df_out["population"] = df_out["population"].astype(int)
    return df_out


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fetch and prepare LGA population CSV")
    parser.add_argument("--url", required=False, help="Direct CSV URL for Nigeria adm2 population (HDX)")
    parser.add_argument("--in", dest="input_path", required=False, help="Local CSV path for Nigeria adm2 population")
    parser.add_argument("--raw-out", default=str(RAW_DIR / "nga_admpop_adm2_2022.csv"), help="Path to save raw CSV")
    parser.add_argument("--out", default=str(PROCESSED_POP_DIR / "lga_population_2022.csv"), help="Path to save prepared CSV")
    args = parser.parse_args(argv)

    # Determine source: local input or download URL
    use_local = bool(args.input_path)
    if not use_local and not args.url:
        raise SystemExit("Provide either --in <local_csv> or --url <direct_csv_url>")

    raw_path = Path(args.input_path) if use_local else Path(args.raw_out)
    out_path = Path(args.out)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if use_local:
        print(f"Using local CSV: {raw_path}")
    else:
        print(f"Downloading: {args.url}")
        download_csv(args.url, raw_path)
        print(f"Saved raw CSV to: {raw_path}")

    df_raw = pd.read_csv(raw_path)
    df_lga = build_lga_population(df_raw)
    df_lga.to_csv(out_path, index=False)
    print(f"Wrote prepared LGA population CSV to: {out_path}")


if __name__ == "__main__":
    sys.exit(main())