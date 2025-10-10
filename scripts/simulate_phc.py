#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BetaHealthCare Data Simulator

Generates CSV datasets aligned to SDI insights and the proposed schema:
- facilities_master
- facility_infrastructure
- facility_equipment
- medicine_catalog
- facility_medicine_stock
- facility_hours
- facility_services
- facility_live_status
- facility_daily_metrics (last 30 days)
- facility_referrals
- lga_daily_signals (last 30 days)

Assumptions reflect SDI Nigeria patterns:
- Rural: ~60%, Urban: ~40%
- Ownership: Public ~92%, Private/NGO ~8%
- Facility types: Hospitals ~17%, Health centers ~61%, Health posts ~22%
- Infrastructure readiness and equipment completeness skew higher in urban/private and hospitals
- Medicine availability: higher in hospitals/private; lowest at posts
- Caseload (outpatients per provider per day): Nigeria average ~2.8, 86% of facilities <5

Requires: pandas, numpy
pip install pandas numpy
"""

import os
import math
import uuid
import random
from datetime import datetime, timedelta, time as dtime

import numpy as np
import pandas as pd
from pathlib import Path

# -------------------
# Config
# -------------------
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = DATA_DIR / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

TODAY = datetime.utcnow().date()
DAYS_HISTORY = 30
COUNTRY = "Nigeria"
SDI_YEAR_NG = 2013

# States, LGAs, rough centroids (lat, lng), and language hints
# Note: Coordinates are approximate; used only for realistic proximity simulation.
REGIONS = [
    {
        "state": "Lagos",
        "lgas": [
            {"name": "Ikorodu", "lat": 6.614, "lng": 3.508, "rural_share": 0.30, "langs": ["en", "yo"]},
            {"name": "Alimosho", "lat": 6.600, "lng": 3.270, "rural_share": 0.15, "langs": ["en", "yo"]},
            {"name": "Surulere", "lat": 6.500, "lng": 3.350, "rural_share": 0.10, "langs": ["en", "yo"]},
        ],
    },
    {
        "state": "Kano",
        "lgas": [
            {"name": "Nasarawa", "lat": 12.000, "lng": 8.520, "rural_share": 0.65, "langs": ["en", "ha"]},
            {"name": "Gwale", "lat": 11.990, "lng": 8.530, "rural_share": 0.50, "langs": ["en", "ha"]},
        ],
    },
    {
        "state": "Katsina",
        "lgas": [
            {"name": "Kafur", "lat": 11.492, "lng": 7.686, "rural_share": 0.70, "langs": ["en", "ha"]},
            {"name": "Dutsin-Ma", "lat": 12.456, "lng": 7.497, "rural_share": 0.65, "langs": ["en", "ha"]},
        ],
    },
    {
        "state": "Kaduna",
        "lgas": [
            {"name": "Chikun", "lat": 10.513, "lng": 7.438, "rural_share": 0.55, "langs": ["en", "ha"]},
            {"name": "Zaria", "lat": 11.073, "lng": 7.705, "rural_share": 0.45, "langs": ["en", "ha"]},
        ],
    },
    {
        "state": "Rivers",
        "lgas": [
            {"name": "Port Harcourt", "lat": 4.815, "lng": 7.049, "rural_share": 0.30, "langs": ["en"]},
            {"name": "Obio-Akpor", "lat": 4.884, "lng": 6.995, "rural_share": 0.30, "langs": ["en"]},
        ],
    },
    {
        "state": "FCT",
        "lgas": [
            {"name": "AMAC", "lat": 9.064, "lng": 7.489, "rural_share": 0.35, "langs": ["en", "ha"]},
            {"name": "Bwari", "lat": 9.279, "lng": 7.383, "rural_share": 0.55, "langs": ["en", "ha"]},
        ],
    },
    {
        "state": "Oyo",
        "lgas": [
            {"name": "Ibadan North", "lat": 7.438, "lng": 3.900, "rural_share": 0.35, "langs": ["en", "yo"]},
            {"name": "Ogbomosho North", "lat": 8.133, "lng": 4.243, "rural_share": 0.55, "langs": ["en", "yo"]},
        ],
    },
    {
        "state": "Ogun",
        "lgas": [
            {"name": "Abeokuta South", "lat": 7.147, "lng": 3.349, "rural_share": 0.40, "langs": ["en", "yo"]},
            {"name": "Ifo", "lat": 6.818, "lng": 3.197, "rural_share": 0.55, "langs": ["en", "yo"]},
        ],
    },
    {
        "state": "Osun",
        "lgas": [
            {"name": "Osogbo", "lat": 7.770, "lng": 4.560, "rural_share": 0.50, "langs": ["en", "yo"]},
            {"name": "Ife Central", "lat": 7.500, "lng": 4.566, "rural_share": 0.55, "langs": ["en", "yo"]},
        ],
    },
    {
        "state": "Ondo",
        "lgas": [
            {"name": "Akure South", "lat": 7.250, "lng": 5.195, "rural_share": 0.45, "langs": ["en", "yo"]},
            {"name": "Owo", "lat": 7.198, "lng": 5.586, "rural_share": 0.60, "langs": ["en", "yo"]},
        ],
    },
    {
        "state": "Ekiti",
        "lgas": [
            {"name": "Ado Ekiti", "lat": 7.623, "lng": 5.220, "rural_share": 0.40, "langs": ["en", "yo"]},
            {"name": "Ikole", "lat": 7.792, "lng": 5.513, "rural_share": 0.60, "langs": ["en", "yo"]},
        ],
    },
    {
        "state": "Edo",
        "lgas": [
            {"name": "Oredo", "lat": 6.338, "lng": 5.625, "rural_share": 0.35, "langs": ["en"]},
            {"name": "Etsako West", "lat": 7.060, "lng": 6.264, "rural_share": 0.65, "langs": ["en"]},
        ],
    },
    {
        "state": "Delta",
        "lgas": [
            {"name": "Warri South", "lat": 5.517, "lng": 5.750, "rural_share": 0.40, "langs": ["en"]},
            {"name": "Ughelli North", "lat": 5.516, "lng": 6.006, "rural_share": 0.55, "langs": ["en"]},
        ],
    },
    {
        "state": "Akwa Ibom",
        "lgas": [
            {"name": "Uyo", "lat": 5.038, "lng": 7.912, "rural_share": 0.35, "langs": ["en"]},
            {"name": "Eket", "lat": 4.641, "lng": 7.939, "rural_share": 0.55, "langs": ["en"]},
        ],
    },
    {
        "state": "Cross River",
        "lgas": [
            {"name": "Calabar Municipal", "lat": 4.951, "lng": 8.322, "rural_share": 0.35, "langs": ["en"]},
            {"name": "Ikom", "lat": 5.976, "lng": 8.715, "rural_share": 0.65, "langs": ["en"]},
        ],
    },
    {
        "state": "Anambra",
        "lgas": [
            {"name": "Awka South", "lat": 6.210, "lng": 7.070, "rural_share": 0.35, "langs": ["en", "ig"]},
            {"name": "Onitsha North", "lat": 6.153, "lng": 6.785, "rural_share": 0.25, "langs": ["en", "ig"]},
        ],
    },
    {
        "state": "Enugu",
        "lgas": [
            {"name": "Enugu North", "lat": 6.457, "lng": 7.510, "rural_share": 0.35, "langs": ["en", "ig"]},
            {"name": "Nsukka", "lat": 6.856, "lng": 7.395, "rural_share": 0.60, "langs": ["en", "ig"]},
        ],
    },
    {
        "state": "Abia",
        "lgas": [
            {"name": "Aba South", "lat": 5.112, "lng": 7.372, "rural_share": 0.30, "langs": ["en", "ig"]},
            {"name": "Umuahia North", "lat": 5.534, "lng": 7.490, "rural_share": 0.50, "langs": ["en", "ig"]},
        ],
    },
    {
        "state": "Kwara",
        "lgas": [
            {"name": "Ilorin West", "lat": 8.500, "lng": 4.550, "rural_share": 0.40, "langs": ["en", "yo"]},
            {"name": "Offa", "lat": 8.149, "lng": 4.718, "rural_share": 0.60, "langs": ["en", "yo"]},
        ],
    },
    {
        "state": "Kogi",
        "lgas": [
            {"name": "Lokoja", "lat": 7.801, "lng": 6.744, "rural_share": 0.45, "langs": ["en"]},
            {"name": "Idah", "lat": 7.113, "lng": 6.739, "rural_share": 0.65, "langs": ["en"]},
        ],
    },
    {
        "state": "Benue",
        "lgas": [
            {"name": "Makurdi", "lat": 7.733, "lng": 8.533, "rural_share": 0.50, "langs": ["en"]},
            {"name": "Gboko", "lat": 7.322, "lng": 9.000, "rural_share": 0.65, "langs": ["en"]},
        ],
    },
    {
        "state": "Niger",
        "lgas": [
            {"name": "Chanchaga", "lat": 9.613, "lng": 6.557, "rural_share": 0.55, "langs": ["en", "ha"]},
            {"name": "Bida", "lat": 9.082, "lng": 6.017, "rural_share": 0.65, "langs": ["en", "ha"]},
        ],
    },
    {
        "state": "Plateau",
        "lgas": [
            {"name": "Jos North", "lat": 9.925, "lng": 8.890, "rural_share": 0.35, "langs": ["en", "ha"]},
            {"name": "Shendam", "lat": 8.883, "lng": 9.533, "rural_share": 0.65, "langs": ["en", "ha"]},
        ],
    },
    {
        "state": "Borno",
        "lgas": [
            {"name": "Maiduguri", "lat": 11.833, "lng": 13.150, "rural_share": 0.35, "langs": ["en", "ha"]},
            {"name": "Jere", "lat": 11.780, "lng": 13.250, "rural_share": 0.60, "langs": ["en", "ha"]},
        ],
    },
    {
        "state": "Yobe",
        "lgas": [
            {"name": "Damaturu", "lat": 11.747, "lng": 11.960, "rural_share": 0.50, "langs": ["en", "ha"]},
            {"name": "Potiskum", "lat": 11.711, "lng": 11.069, "rural_share": 0.65, "langs": ["en", "ha"]},
        ],
    },
    {
        "state": "Adamawa",
        "lgas": [
            {"name": "Yola North", "lat": 9.282, "lng": 12.458, "rural_share": 0.45, "langs": ["en", "ha"]},
            {"name": "Mubi North", "lat": 10.267, "lng": 13.267, "rural_share": 0.65, "langs": ["en", "ha"]},
        ],
    },
    {
        "state": "Taraba",
        "lgas": [
            {"name": "Jalingo", "lat": 8.893, "lng": 11.360, "rural_share": 0.50, "langs": ["en", "ha"]},
            {"name": "Wukari", "lat": 7.870, "lng": 9.781, "rural_share": 0.70, "langs": ["en", "ha"]},
        ],
    },
    {
        "state": "Bauchi",
        "lgas": [
            {"name": "Bauchi", "lat": 10.310, "lng": 9.842, "rural_share": 0.45, "langs": ["en", "ha"]},
            {"name": "Katagum", "lat": 11.590, "lng": 10.340, "rural_share": 0.65, "langs": ["en", "ha"]},
        ],
    },
    {
        "state": "Gombe",
        "lgas": [
            {"name": "Gombe", "lat": 10.290, "lng": 11.170, "rural_share": 0.45, "langs": ["en", "ha"]},
            {"name": "Kaltungo", "lat": 9.816, "lng": 11.315, "rural_share": 0.65, "langs": ["en", "ha"]},
        ],
    },
    {
        "state": "Sokoto",
        "lgas": [
            {"name": "Sokoto North", "lat": 13.062, "lng": 5.232, "rural_share": 0.40, "langs": ["en", "ha"]},
            {"name": "Sokoto South", "lat": 13.037, "lng": 5.224, "rural_share": 0.50, "langs": ["en", "ha"]},
        ],
    },
    {
        "state": "Kebbi",
        "lgas": [
            {"name": "Birnin Kebbi", "lat": 12.456, "lng": 4.200, "rural_share": 0.55, "langs": ["en", "ha"]},
            {"name": "Argungu", "lat": 12.950, "lng": 4.517, "rural_share": 0.70, "langs": ["en", "ha"]},
        ],
    },
    {
        "state": "Jigawa",
        "lgas": [
            {"name": "Dutse", "lat": 11.742, "lng": 9.340, "rural_share": 0.60, "langs": ["en", "ha"]},
            {"name": "Hadejia", "lat": 12.455, "lng": 10.045, "rural_share": 0.70, "langs": ["en", "ha"]},
        ],
    },
    {
        "state": "Zamfara",
        "lgas": [
            {"name": "Gusau", "lat": 12.163, "lng": 6.663, "rural_share": 0.60, "langs": ["en", "ha"]},
            {"name": "Talata Mafara", "lat": 12.566, "lng": 6.058, "rural_share": 0.70, "langs": ["en", "ha"]},
        ],
    },
]

# Facility volumes 
N_FACILITIES = 3000

# Nigeria-level target splits from SDI (approximate)
RURAL_SHARE = 0.60
PUBLIC_SHARE = 0.92  # Private/NGO total ~8%
FACILITY_TYPE_SPLIT = {
    "hospital": 0.17,
    "health_center": 0.61,  # includes "clinic"
    "health_post": 0.22,
}

OWNERSHIP_SPLIT = {
    "public": 0.92,
    "private": 0.06,
    "ngo": 0.02,
}

# Medicine catalog (key PHC items)
MEDICINES = [
    ("ACT-ART", "Artemisinin-based combo therapy", "malaria", "tab", "tabs", True),
    ("AMX-500", "Amoxicillin 500mg", "antibiotic", "cap", "caps", True),
    ("ORS-ZNC", "ORS + Zinc co-pack", "diarrhea", "sachet", "packs", True),
    ("RDT-MAL", "Malaria RDT kit", "diagnostic", "test", "tests", True),
    ("OXE-10IU", "Oxytocin 10 IU", "maternal", "inj", "vials", True),
    ("DMPA-150", "Depot Medroxyprogesterone", "family_planning", "inj", "vials", True),
    ("PCM-500", "Paracetamol 500mg", "analgesic", "tab", "tabs", True),
    ("HIV-RT", "Rapid HIV Test", "diagnostic", "test", "tests", True),
]
MED_MIN_THRESHOLDS = {
    "ACT-ART": 100,
    "AMX-500": 80,
    "ORS-ZNC": 40,
    "RDT-MAL": 50,
    "OXE-10IU": 20,
    "DMPA-150": 20,
    "PCM-500": 150,
    "HIV-RT": 30,
}

# Service catalog
SERVICES = [
    ("malaria_rdt", "Malaria Rapid Test"),
    ("immunization", "Routine Immunization"),
    ("anc", "Antenatal Care"),
    ("delivery", "Normal Delivery"),
    ("hiv_test", "HIV Testing and Counseling"),
    ("family_planning", "Family Planning"),
    ("tb_screen", "TB Symptom Screening"),
    ("minor_surgery", "Minor Surgery/Procedures"),
    ("lab_basic", "Basic Lab Services"),
]

# -------------------
# Helpers
# -------------------
def slug3(txt: str) -> str:
    t = "".join([c for c in txt.upper() if c.isalnum()])
    return (t[:3] if len(t) >= 3 else (t + "XXX")[:3])

def choose_with_probs(items, probs):
    return np.random.choice(items, p=np.array(probs)/np.sum(probs))

def jitter_coord(val: float, scale: float = 0.08) -> float:
    return float(val + np.random.normal(0, scale))

def pick_languages(base_langs):
    # Always include 'en'; include LGA language(s); small chance to add both ha+yo
    langs = set(["en"])
    for lg in base_langs:
        if np.random.rand() < 0.9:
            langs.add(lg)
    if np.random.rand() < 0.05:
        langs.add("yo")
        langs.add("ha")
    return ",".join(sorted(langs))

def segment_probs_equipment_complete(ownership, facility_type):
    # Nigeria SDI equipment completeness (approx):
    # All: 51.7; Public: 45.8; Private: 78.1; Hospital 77.9; Health center 54.3; Post 19.0
    base = 0.517
    if ownership == "public":
        base = 0.458
    else:
        base = 0.781
    if facility_type == "hospital":
        base = 0.779
    elif facility_type == "health_center":
        base = 0.543
    elif facility_type == "health_post":
        base = 0.190
    return max(0.05, min(base, 0.98))

def segment_target_medicine_fraction(ownership, facility_type):
    # Nigeria SDI medicine availability fractions:
    # Public 45.8; Private 78.1; Hospital 77.9; Health center 54.3; Post 19.0
    if facility_type == "hospital":
        return 0.779
    elif facility_type == "health_center":
        return 0.543 if ownership == "public" else 0.65
    elif facility_type == "health_post":
        return 0.190
    # fallback by ownership
    return 0.458 if ownership == "public" else 0.781

def segment_infra_composite_prob(rural_urban, ownership, facility_type):
    # Nigeria SDI infrastructure "all three present" fractions:
    # All: 28.5; Public 20.3; Private 65.2; Rural 19.6; Urban 44.7; Hospital 61.6; Health center 25.8; Post 5.5
    # Combine influences (not exact math; picks the min of relevant anchors to reflect constraints)
    base = 0.285
    base = min(base, 0.447 if rural_urban == "urban" else 0.196)
    base = min(base, 0.652 if ownership != "public" else 0.203)
    if facility_type == "hospital":
        base = max(base, 0.616)  # hospitals better
    elif facility_type == "health_center":
        base = min(base, 0.258)
    elif facility_type == "health_post":
        base = min(base, 0.055)
    return max(0.03, min(base, 0.95))

def component_likelihoods_for_nonready(rural_urban):
    # If not fully ready, components more likely missing electricity in Nigeria
    # Urban better than rural
    if rural_urban == "urban":
        return dict(electricity=0.55, water=0.65, toilet=0.45)
    else:
        return dict(electricity=0.30, water=0.55, toilet=0.35)

def caseload_params(facility_type, rural_urban, ownership):
    # Nigeria outpatients per provider per day:
    # Hospitals: ~4.1; Centers: ~2.7; Posts: ~2.0; Rural ~2.6, Urban ~3.2; Private slightly higher
    base = 2.8
    if facility_type == "hospital":
        base = 4.1
    elif facility_type == "health_center":
        base = 2.7
    elif facility_type == "health_post":
        base = 2.0
    if rural_urban == "urban":
        base *= 1.15
    else:
        base *= 0.95
    if ownership != "public":
        base *= 1.10
    return max(0.8, base)

def providers_range(facility_type):
    if facility_type == "hospital":
        return (5, 15)
    elif facility_type == "health_center":
        return (2, 6)
    else:
        return (1, 2)

def build_facility_id(state, lga, idx):
    return f"NGA-{slug3(state)}-{slug3(lga)}-{idx:04d}"

def choose_power_source(rural_urban):
    # Reflect frequent electricity issues; rural uses solar/generator more
    if rural_urban == "urban":
        return np.random.choice(["grid", "generator", "solar", "none"], p=[0.6, 0.25, 0.10, 0.05])
    else:
        return np.random.choice(["grid", "generator", "solar", "none"], p=[0.35, 0.30, 0.25, 0.10])

def network_status(power_on):
    if not power_on:
        return np.random.choice(["ok", "slow", "down"], p=[0.2, 0.4, 0.4])
    return np.random.choice(["ok", "slow", "down"], p=[0.7, 0.25, 0.05])

def in_business_hours(open_time: dtime, close_time: dtime, now_local: datetime):
    t = now_local.time()
    if open_time <= close_time:
        return open_time <= t <= close_time
    # Overnight schedule
    return t >= open_time or t <= close_time

# -------------------
# Population loading and allocation helpers
# -------------------
def load_state_population(filepath: str = os.path.join(DATA_DIR, "processed", "population", "state_population_2022.csv")) -> dict:
    """Load state-level population mapping from CSV.

    Supported formats:
    - Simple CSV: columns [state, population]
    - HDX COD-PS adm1 CSV variants containing ADM1 name and total population

    Returns a dict {state_name: population} for states present in REGIONS.
    """
    if not os.path.exists(filepath):
        return {}
    df = pd.read_csv(filepath)
    # Normalize column names
    cols = {c.lower().strip(): c for c in df.columns}
    name_col_candidates = ["state", "adm1_name", "adm1_en", "adm1name", "admin1_name"]
    pop_col_candidates = ["population", "totl_pop", "total_pop", "tot_pop", "pop"]
    name_col = next((cols[c] for c in cols if c in name_col_candidates), None)
    pop_col = next((cols[c] for c in cols if c in pop_col_candidates), None)
    if not name_col or not pop_col:
        # try detecting a total column by numeric majority
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        pop_col = pop_col or (num_cols[0] if num_cols else None)
        # fallback name column by first object col
        obj_cols = [c for c in df.columns if df[c].dtype == object]
        name_col = name_col or (obj_cols[0] if obj_cols else None)
    if not name_col or not pop_col:
        return {}
    # Build mapping and restrict to states present in REGIONS
    regions_states = {r["state"].strip().lower(): r["state"] for r in REGIONS}
    mapping = {}
    for _, row in df.iterrows():
        raw_name = str(row[name_col]).strip()
        key = raw_name.lower().replace("state", "").strip()
        if key in regions_states:
            try:
                val = int(float(row[pop_col]))
            except Exception:
                continue
            mapping[regions_states[key]] = val
    return mapping

def load_lga_population(filepath: str = os.path.join(DATA_DIR, "processed", "population", "lga_population_2022.csv")) -> dict:
    """Load LGA-level population mapping from CSV.

    Expected format: columns [state, lga, population]. Names normalized to match REGIONS.
    Returns a dict {(state_name, lga_name): population} only for LGAs present in REGIONS.
    """
    if not os.path.exists(filepath):
        return {}
    df = pd.read_csv(filepath)
    cols = {c.lower().strip(): c for c in df.columns}
    state_col = next((cols[c] for c in cols if c in ["state", "adm1_name", "adm1_en", "adm1name", "admin1_name"]), None)
    lga_col = next((cols[c] for c in cols if c in ["lga", "adm2_name", "adm2_en", "adm2name", "admin2_name"]), None)
    pop_col = next((cols[c] for c in cols if c in ["population", "totl_pop", "total_pop", "tot_pop", "pop"]), None)
    if not state_col or not lga_col or not pop_col:
        # try basic fallbacks
        obj_cols = [c for c in df.columns if df[c].dtype == object]
        if not state_col and obj_cols:
            state_col = obj_cols[0]
        if not lga_col and len(obj_cols) > 1:
            lga_col = obj_cols[1]
        if not pop_col:
            num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            pop_col = num_cols[0] if num_cols else None
    if not state_col or not lga_col or not pop_col:
        return {}

    # Build set of valid (state, lga) pairs from REGIONS
    valid_pairs = {(r["state"].strip().lower(), l["name"].strip().lower()): (r["state"], l["name"]) for r in REGIONS for l in r["lgas"]}

    def norm_state(s: str) -> str:
        return str(s).strip().lower().replace("state", "").strip()

    def norm_lga(x: str) -> str:
        x = str(x).strip().lower().replace("lga", "").strip()
        if "(" in x and ")" in x:
            try:
                x = x[: x.index("(")].strip()
            except Exception:
                pass
        return x

    mapping = {}
    for _, row in df.iterrows():
        s_key = norm_state(row[state_col])
        l_key = norm_lga(row[lga_col])
        if (s_key, l_key) in valid_pairs:
            try:
                val = int(float(row[pop_col]))
            except Exception:
                continue
            s_name, l_name = valid_pairs[(s_key, l_key)]
            mapping[(s_name, l_name)] = val
    return mapping

def allocate_by_population(n_facilities: int) -> list:
    """Compute per-LGA allocations using state population weights.

    Returns a list of tuples (lga_info_dict, allocation_count).
    """
    # Flatten LGAs per state
    state_to_lgas = {}
    for r in REGIONS:
        state_to_lgas.setdefault(r["state"], []).extend([{ "state": r["state"], **l } for l in r["lgas"]])

    pop_map = load_state_population()
    # If population not available, fall back to equal per-LGA allocation
    if not pop_map:
        all_lgas = [l for lst in state_to_lgas.values() for l in lst]
        lga_count = len(all_lgas)
        base = n_facilities // lga_count
        remainder = n_facilities % lga_count
        allocs = [base + (1 if i < remainder else 0) for i in range(lga_count)]
        return list(zip(all_lgas, allocs))

    # Restrict population to the states present in REGIONS
    states_in_regions = list(state_to_lgas.keys())
    filtered_pop = {s: pop_map[s] for s in states_in_regions if s in pop_map}
    # If some states missing, assign average to them
    if len(filtered_pop) < len(states_in_regions):
        avg_pop = int(sum(filtered_pop.values()) / max(1, len(filtered_pop))) if filtered_pop else 1
        for s in states_in_regions:
            if s not in filtered_pop:
                filtered_pop[s] = avg_pop

    total_pop = sum(filtered_pop.values())
    # Compute exact quotas
    quotas = {s: (filtered_pop[s] / total_pop) * n_facilities for s in states_in_regions}
    # Integer allocations with largest remainder
    floor_allocs = {s: int(math.floor(q)) for s, q in quotas.items()}
    assigned = sum(floor_allocs.values())
    remainder = n_facilities - assigned
    # Distribute remainder by fractional part
    remainders_sorted = sorted(states_in_regions, key=lambda s: quotas[s] - floor_allocs[s], reverse=True)
    for i in range(remainder):
        floor_allocs[remainders_sorted[i]] += 1

    # Split state allocations across LGAs, using LGA population weights if available
    lga_pop_map = load_lga_population()
    lga_allocs = []
    for s in states_in_regions:
        lgas = state_to_lgas[s]
        count = floor_allocs[s]
        if not lgas or count <= 0:
            continue
        if lga_pop_map:
            pops = [max(0, int(lga_pop_map.get((s, l["name"]), 0))) for l in lgas]
            total = sum(pops)
            if total > 0:
                base = count * (np.array(pops, dtype=float) / float(total))
                quotas = np.floor(base).astype(int)
                assigned_lga = int(quotas.sum())
                rem = count - assigned_lga
                if rem > 0:
                    remainders = base - quotas
                    order = np.argsort(-remainders)
                    for j in order[:rem]:
                        quotas[j] += 1
                for i, l in enumerate(lgas):
                    lga_allocs.append((l, int(quotas[i])))
            else:
                # Even split if no LGA pops for this state
                base = count // len(lgas)
                rem = count % len(lgas)
                for i, l in enumerate(lgas):
                    lga_allocs.append((l, base + (1 if i < rem else 0)))
        else:
            # Even split if no LGA population file
            base = count // len(lgas)
            rem = count % len(lgas)
            for i, l in enumerate(lgas):
                lga_allocs.append((l, base + (1 if i < rem else 0)))
    return lga_allocs

# -------------------
# 1) facilities_master
# -------------------
def generate_facilities(n_facilities: int) -> pd.DataFrame:
    # Allocate facilities per state using population weights; then per LGA (weighted if available)
    allocations = allocate_by_population(n_facilities)

    rows = []
    idx = 1
    pop_map = load_state_population()
    lga_pop_map = load_lga_population()
    for l, alloc in allocations:
        state = l["state"]
        lga = l["name"]
        state_pop = int(pop_map.get(state, 0))
        for _ in range(alloc):
            # Rural/Urban per LGA rural_share blended with national target
            rural_prob = 0.5 * RURAL_SHARE + 0.5 * l["rural_share"]
            rural_urban = "rural" if np.random.rand() < rural_prob else "urban"

            # Ownership split
            ownership = np.random.choice(list(OWNERSHIP_SPLIT.keys()), p=list(OWNERSHIP_SPLIT.values()))

            # Facility type split (constant across)
            facility_type = np.random.choice(list(FACILITY_TYPE_SPLIT.keys()), p=list(FACILITY_TYPE_SPLIT.values()))

            fid = build_facility_id(state, lga, idx)
            idx += 1

            rows.append({
                "facility_id": fid,
                "name": f"{lga} {facility_type.replace('_', ' ').title()} {np.random.randint(1, 300)}",
                "country": COUNTRY,
                "state": state,
                "lga": lga,
                "ward": f"Ward {np.random.randint(1, 12)}",
                "ownership": ownership,
                "facility_type": facility_type,
                "rural_urban": rural_urban,
                "latitude": jitter_coord(l["lat"], 0.08),
                "longitude": jitter_coord(l["lng"], 0.08),
                "phone": f"+234-800-{np.random.randint(100, 999)}-{np.random.randint(1000, 9999)}",
                "languages": pick_languages(l["langs"]),
                "sdi_sampled": bool(np.random.rand() < 0.45),
                "sdi_year": SDI_YEAR_NG,
                "state_population": state_pop,
                "lga_population": int(lga_pop_map.get((state, lga), 0)),
            })

    return pd.DataFrame(rows)

# -------------------
# 2) facility_infrastructure
# -------------------
def generate_infrastructure(fac_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in fac_df.iterrows():
        composite_p = segment_infra_composite_prob(r.rural_urban, r.ownership, r.facility_type)
        is_ready = np.random.rand() < composite_p

        if is_ready:
            has_water = True
            has_toilet = True
            has_power = True
        else:
            lik = component_likelihoods_for_nonready(r.rural_urban)
            # Independent-ish components; electricity most constrained
            has_power = bool(np.random.rand() < lik["electricity"])
            has_water = bool(np.random.rand() < lik["water"])
            has_toilet = bool(np.random.rand() < lik["toilet"])

        power_source = choose_power_source(r.rural_urban) if has_power else "none"
        infra_index = np.mean([has_water, has_toilet, has_power])

        rows.append({
            "facility_id": r.facility_id,
            "has_improved_water": has_water,
            "has_improved_toilet": has_toilet,
            "has_electricity": has_power,
            "power_source": power_source,
            "infrastructure_index": round(float(infra_index), 2),
            "last_verified_at": datetime.utcnow().isoformat(),
            "source": np.random.choice(["SDI", "self_report", "supervisor_audit", "IoT"], p=[0.3, 0.3, 0.35, 0.05]),
        })
    return pd.DataFrame(rows)

# -------------------
# 3) facility_equipment
# -------------------
def generate_equipment(fac_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in fac_df.iterrows():
        p_complete = segment_probs_equipment_complete(r.ownership, r.facility_type)
        complete = np.random.rand() < p_complete
        # If not complete, miss 1 item (70%) or 2+ items (30%)
        missing_k = 0 if complete else (1 if np.random.rand() < 0.7 else np.random.randint(2, 4))
        items = ["thermometer", "stethoscope", "sphygmomanometer", "scale"]
        np.random.shuffle(items)
        missing = set(items[:missing_k])

        rows.append({
            "facility_id": r.facility_id,
            "has_thermometer": "thermometer" not in missing,
            "has_stethoscope": "stethoscope" not in missing,
            "has_sphygmomanometer": "sphygmomanometer" not in missing,
            "has_scale": "scale" not in missing,
            "equipment_complete": complete,
            "last_verified_at": datetime.utcnow().isoformat(),
            "source": np.random.choice(["SDI", "audit", "self_report"], p=[0.35, 0.4, 0.25]),
        })
    return pd.DataFrame(rows)

# -------------------
# 4) medicine_catalog
# -------------------
def generate_medicine_catalog() -> pd.DataFrame:
    rows = []
    for code, name, cat, form, unit, essential in MEDICINES:
        rows.append({
            "medicine_code": code,
            "name": name,
            "category": cat,
            "form": form,
            "unit": unit,
            "is_key_essential": essential,
        })
    return pd.DataFrame(rows)

# -------------------
# 5) facility_medicine_stock
# -------------------
def generate_medicine_stock(fac_df: pd.DataFrame, med_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in fac_df.iterrows():
        target_frac = segment_target_medicine_fraction(r.ownership, r.facility_type)
        n_meds = len(med_df)
        n_available = int(round(target_frac * n_meds))
        available_codes = set(np.random.choice(med_df["medicine_code"].values, size=n_available, replace=False))
        for _, m in med_df.iterrows():
            code = m.medicine_code
            min_thresh = MED_MIN_THRESHOLDS.get(code, 50)
            if code in available_codes:
                # Stock draws higher for hospitals/private; lower for posts
                mult = 1.0
                if r.facility_type == "hospital":
                    mult *= 1.8
                elif r.facility_type == "health_post":
                    mult *= 0.6
                if r.ownership != "public":
                    mult *= 1.3
                base = max(1, int(np.random.normal(min_thresh * 1.5 * mult, min_thresh * 0.4)))
                stock = max(0, int(np.random.poisson(base)))
                status = "in_stock" if stock >= min_thresh else "low"
                exp_days = np.random.randint(60, 540)
                expiry = (TODAY + timedelta(days=exp_days)).isoformat()
            else:
                stock = 0
                status = "stockout"
                expiry = "1970-01-01"
            rows.append({
                "facility_id": r.facility_id,
                "medicine_code": code,
                "stock_level_units": stock,
                "stock_status": status,
                "min_threshold": min_thresh,
                "expiry_date_next": expiry,
                "last_stock_count_at": datetime.utcnow().isoformat(),
                "source": np.random.choice(["SDI", "LMIS", "self_report", "audit"], p=[0.2, 0.5, 0.2, 0.1]),
            })
    return pd.DataFrame(rows)

# -------------------
# 6) facility_hours
# -------------------
def generate_facility_hours(fac_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    dow = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for _, r in fac_df.iterrows():
        if r.facility_type == "hospital":
            # Many hospitals 24/7
            is_24h = bool(np.random.rand() < 0.85)
            for d in dow:
                rows.append({
                    "facility_id": r.facility_id,
                    "day_of_week": d,
                    "open_time": "00:00" if is_24h else ("08:00" if d in dow[:5] else "09:00"),
                    "close_time": "23:59" if is_24h else ("20:00" if d in dow[:5] else "16:00"),
                    "is_24h": is_24h,
                })
        elif r.facility_type == "health_center":
            for d in dow:
                if d in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
                    rows.append({"facility_id": r.facility_id, "day_of_week": d, "open_time": "08:00", "close_time": "16:00", "is_24h": False})
                elif d == "Sat":
                    rows.append({"facility_id": r.facility_id, "day_of_week": d, "open_time": "08:00", "close_time": "13:00", "is_24h": False})
                else:
                    # Some centers open Sundays
                    if np.random.rand() < 0.25:
                        rows.append({"facility_id": r.facility_id, "day_of_week": d, "open_time": "10:00", "close_time": "14:00", "is_24h": False})
                    else:
                        rows.append({"facility_id": r.facility_id, "day_of_week": d, "open_time": "00:00", "close_time": "00:00", "is_24h": False})
        else:
            # Health posts: shorter hours
            for d in dow:
                if d in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
                    rows.append({"facility_id": r.facility_id, "day_of_week": d, "open_time": "09:00", "close_time": "15:00", "is_24h": False})
                elif d == "Sat":
                    if np.random.rand() < 0.4:
                        rows.append({"facility_id": r.facility_id, "day_of_week": d, "open_time": "09:00", "close_time": "12:00", "is_24h": False})
                    else:
                        rows.append({"facility_id": r.facility_id, "day_of_week": d, "open_time": "00:00", "close_time": "00:00", "is_24h": False})
                else:
                    rows.append({"facility_id": r.facility_id, "day_of_week": d, "open_time": "00:00", "close_time": "00:00", "is_24h": False})
    return pd.DataFrame(rows)

# -------------------
# 7) facility_services
# -------------------
def generate_services(fac_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in fac_df.iterrows():
        for code, name in SERVICES:
            active = False
            if r.facility_type == "hospital":
                active = True
            elif r.facility_type == "health_center":
                # Centers provide many services except some minor surgery (probabilistic)
                active = code in ["malaria_rdt", "immunization", "anc", "delivery", "hiv_test", "family_planning", "tb_screen", "lab_basic"] or (code == "minor_surgery" and np.random.rand() < 0.4)
            else:
                # Posts: basic services
                active = code in ["malaria_rdt", "immunization", "anc", "tb_screen", "lab_basic"] and np.random.rand() < 0.9
                if code == "delivery":
                    active = np.random.rand() < 0.15
                if code == "hiv_test":
                    active = np.random.rand() < 0.6
                if code == "family_planning":
                    active = np.random.rand() < 0.7
                if code == "minor_surgery":
                    active = False
            rows.append({
                "facility_id": r.facility_id,
                "service_code": code,
                "service_name": name,
                "active": bool(active),
            })
    return pd.DataFrame(rows)

# -------------------
# 8) facility_live_status
# -------------------
def generate_live_status(fac_df: pd.DataFrame, hours_df: pd.DataFrame, infra_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    now = datetime.utcnow()
    dow = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    today_d = dow[now.weekday()]
    infra_map = infra_df.set_index("facility_id").to_dict(orient="index")

    # Helper: get today's schedule
    grouped_hours = {fid: grp for fid, grp in hours_df.groupby("facility_id")}
    for _, r in fac_df.iterrows():
        sched = grouped_hours[r.facility_id]
        sched_today = sched[sched.day_of_week == today_d].iloc[0]
        is_24h = bool(sched_today.is_24h)
        if is_24h:
            open_now = True
        else:
            ot = datetime.strptime(sched_today.open_time, "%H:%M").time()
            ct = datetime.strptime(sched_today.close_time, "%H:%M").time()
            if ot == dtime(0, 0) and ct == dtime(0, 0):
                open_now = False
            else:
                open_now = in_business_hours(ot, ct, now)

        # Power-on probability higher if has electricity + not "none"
        infra = infra_map.get(r.facility_id, {})
        has_elec = infra.get("has_electricity", False)
        power_source = infra.get("power_source", "none")
        if not has_elec or power_source == "none":
            power_on = bool(np.random.rand() < 0.10)
        else:
            # Grid more stable than generator/solar
            p = 0.85 if power_source == "grid" else (0.65 if power_source == "generator" else 0.70)
            power_on = bool(np.random.rand() < p)

        # Queue dynamics: hospitals/centers more likely to have queue during day
        base_queue = 0
        if open_now:
            if r.facility_type == "hospital":
                base_queue = np.random.poisson(6)
            elif r.facility_type == "health_center":
                base_queue = np.random.poisson(3)
            else:
                base_queue = np.random.poisson(1)
        queue = int(base_queue)
        avg_wait = int(max(0, np.random.normal(5 * queue, 7))) if queue > 0 else 0

        rows.append({
            "facility_id": r.facility_id,
            "status_timestamp": now.isoformat(),
            "is_open": open_now,
            "queue_length": queue,
            "avg_wait_minutes": avg_wait,
            "power_on": power_on,
            "network_status": network_status(power_on),
            "staff_on_duty": int(np.random.randint(*providers_range(r.facility_type))),
            "notes": "" if open_now else "Closed per schedule",
        })
    return pd.DataFrame(rows)

# -------------------
# 9) facility_daily_metrics (30-day history)
# -------------------
def generate_daily_metrics(fac_df: pd.DataFrame, equip_df: pd.DataFrame, stock_df: pd.DataFrame, hours_df: pd.DataFrame) -> pd.DataFrame:
    equip_map = equip_df.set_index("facility_id").to_dict(orient="index")
    # Key stock per facility: count current stockouts among essential meds
    essential_stock = stock_df.merge(
        pd.DataFrame({"medicine_code": [m[0] for m in MEDICINES], "is_key": True}),
        on="medicine_code", how="left"
    )
    stock_map = essential_stock.groupby("facility_id").apply(
        lambda d: int((d["stock_status"] == "stockout").sum())
    ).to_dict()

    rows = []
    for _, r in fac_df.iterrows():
        base_ppd = caseload_params(r.facility_type, r.rural_urban, r.ownership)
        # Providers on duty baseline
        pmin, pmax = providers_range(r.facility_type)
        # Precompute missing equipment count
        e = equip_map.get(r.facility_id, {})
        missing_equipment = 4 - int(e.get("has_thermometer", False)) - int(e.get("has_stethoscope", False)) - int(e.get("has_sphygmomanometer", False)) - int(e.get("has_scale", False))
        stockouts = stock_map.get(r.facility_id, 0)

        for d in range(DAYS_HISTORY):
            day = TODAY - timedelta(days=(DAYS_HISTORY - 1 - d))
            dow = day.weekday()  # Mon=0..Sun=6
            weekend = (dow >= 5)

            # Providers vary day to day
            providers_on = int(np.random.randint(pmin, pmax + 1))
            # Weekend effect
            mean_ppd = base_ppd * (0.6 if weekend else 1.0)
            # If many stockouts/missing equipment, reduce throughput
            mean_ppd *= (1.0 - 0.05 * stockouts) * (1.0 - 0.07 * missing_equipment)
            mean_ppd = max(0.6, mean_ppd)

            outpatients = int(np.random.poisson(mean_ppd * providers_on))
            downtime = 0
            # Random downtime influenced by rural and power
            if r.rural_urban == "rural" and np.random.rand() < 0.25:
                downtime = int(np.random.gamma(2, 15))  # minutes

            # Referrals out likely if low readiness
            referrals_out = 0
            if (stockouts >= 3 or missing_equipment >= 2) and np.random.rand() < 0.2:
                referrals_out = np.random.poisson(1)

            rows.append({
                "date": day.isoformat(),
                "facility_id": r.facility_id,
                "outpatients_seen": outpatients,
                "providers_on_duty": providers_on,
                "outpatients_per_provider": round(outpatients / providers_on, 2) if providers_on > 0 else 0.0,
                "stockout_count": stockouts,
                "equipment_missing_count": missing_equipment,
                "downtime_minutes": downtime,
                "referrals_out_count": referrals_out,
            })
    return pd.DataFrame(rows)

# -------------------
# 10) facility_referrals
# -------------------
def generate_referrals(fac_df: pd.DataFrame, daily_df: pd.DataFrame) -> pd.DataFrame:
    # From facilities with repeated high stockouts/equipment gaps to nearest higher-level in same LGA
    rows = []
    # Average over last week
    last_week = daily_df[daily_df["date"] >= (TODAY - timedelta(days=7)).isoformat()]
    agg = last_week.groupby("facility_id").agg(
        stockouts=("stockout_count", "mean"),
        eq_missing=("equipment_missing_count", "mean"),
        referrals=("referrals_out_count", "sum")
    ).reset_index()

    fac_map = fac_df.set_index("facility_id").to_dict(orient="index")
    # Prepare lookup by area
    by_state_lga = {}
    for _, r in fac_df.iterrows():
        by_state_lga.setdefault((r.state, r.lga), []).append(r)

    for _, a in agg.iterrows():
        if a.referrals == 0 and (a.stockouts + a.eq_missing) < 3:
            continue
        f = fac_map[a.facility_id]
        # Choose destination: hospital if available, else health_center, in same LGA
        candidates = by_state_lga.get((f["state"], f["lga"]), [])
        dests = [x for x in candidates if x["facility_type"] in ["hospital", "health_center"] and x["facility_id"] != a.facility_id]
        if not dests:
            continue
        # Pick closest by random for now
        dest = random.choice(dests)
        rows.append({
            "referral_id": str(uuid.uuid4()),
            "from_facility_id": a.facility_id,
            "to_facility_id": dest["facility_id"],
            "date_time": (datetime.utcnow() - timedelta(days=np.random.randint(0, 7), hours=np.random.randint(0, 24))).isoformat(),
            "reason_code": np.random.choice(["stockout", "equipment", "specialist_needed", "capacity"], p=[0.4, 0.35, 0.15, 0.10]),
            "reason_desc": "Automated referral due to low readiness/capacity",
            "patient_count": int(max(1, np.random.poisson(1))),
            "status": np.random.choice(["completed", "pending", "canceled"], p=[0.7, 0.25, 0.05]),
        })
    return pd.DataFrame(rows)

# -------------------
# 11) lga_daily_signals
# -------------------
def generate_lga_signals(fac_df: pd.DataFrame, daily_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    # Aggregate outpatients by LGA/date to derive simple syndromic signals
    merged = daily_df.merge(fac_df[["facility_id", "country", "state", "lga", "rural_urban"]], on="facility_id", how="left")
    grp = merged.groupby(["date", "country", "state", "lga"]).agg(
        outpatients=("outpatients_seen", "sum"),
        rural_share=("rural_urban", lambda s: (s == "rural").mean())
    ).reset_index()

    for _, r in grp.iterrows():
        # Syndromic shares: fever 40–60% of outpatients, diarrhea 10–25%, resp 20–40%; influenced by rainfall/temp
        rainfall = max(0.0, np.random.gamma(1.5, 3.0) * (0.6 + 0.8 * r.rural_share))  # more rain rural
        temp = np.random.normal(29.0, 2.5)
        base = max(0, int(r.outpatients))
        fever = int(np.random.binomial(base, np.random.uniform(0.4, 0.6)))
        diarrhea = int(np.random.binomial(base, np.random.uniform(0.1, 0.25)))
        resp = int(np.random.binomial(base, np.random.uniform(0.2, 0.4)))
        cholera_alert = bool((diarrhea > 40) and (rainfall > 10))

        rows.append({
            "date": r.date,
            "country": r.country,
            "state": r.state,
            "lga": r.lga,
            "fever_cases": fever,
            "diarrhea_cases": diarrhea,
            "resp_cases": resp,
            "rainfall_mm": round(float(rainfall), 1),
            "temperature_c": round(float(temp), 1),
            "cholera_alert": cholera_alert,
        })
    return pd.DataFrame(rows)

# -------------------
# Orchestration
# -------------------
def main():
    print("Generating facilities...")
    facilities = generate_facilities(N_FACILITIES)

    print("Generating infrastructure...")
    infra = generate_infrastructure(facilities)

    print("Generating equipment...")
    equip = generate_equipment(facilities)

    print("Generating medicine catalog...")
    meds = generate_medicine_catalog()

    print("Generating medicine stock...")
    stock = generate_medicine_stock(facilities, meds)

    print("Generating facility hours...")
    hours = generate_facility_hours(facilities)

    print("Generating services...")
    services = generate_services(facilities)

    print("Generating live status...")
    live = generate_live_status(facilities, hours, infra)

    print(f"Generating daily metrics ({DAYS_HISTORY} days)...")
    daily = generate_daily_metrics(facilities, equip, stock, hours)

    print("Generating referrals...")
    refs = generate_referrals(facilities, daily)

    print("Generating LGA daily signals...")
    lga = generate_lga_signals(facilities, daily)

    # Write CSVs
    print("Writing CSVs to:", OUT_DIR)
    facilities.to_csv(os.path.join(OUT_DIR, "facilities_master.csv"), index=False)
    infra.to_csv(os.path.join(OUT_DIR, "facility_infrastructure.csv"), index=False)
    equip.to_csv(os.path.join(OUT_DIR, "facility_equipment.csv"), index=False)
    meds.to_csv(os.path.join(OUT_DIR, "medicine_catalog.csv"), index=False)
    stock.to_csv(os.path.join(OUT_DIR, "facility_medicine_stock.csv"), index=False)
    hours.to_csv(os.path.join(OUT_DIR, "facility_hours.csv"), index=False)
    services.to_csv(os.path.join(OUT_DIR, "facility_services.csv"), index=False)
    live.to_csv(os.path.join(OUT_DIR, "facility_live_status.csv"), index=False)
    daily.to_csv(os.path.join(OUT_DIR, "facility_daily_metrics.csv"), index=False)
    refs.to_csv(os.path.join(OUT_DIR, "facility_referrals.csv"), index=False)
    lga.to_csv(os.path.join(OUT_DIR, "lga_daily_signals.csv"), index=False)

    # Quick console summary
    print("Done.")
    print(f"- Facilities: {len(facilities)}")
    print(f"- Live status rows: {len(live)}")
    print(f"- Daily metrics rows: {len(daily)}")
    print(f"- Referrals rows: {len(refs)}")
    print(f"- LGA signals rows: {len(lga)}")

if __name__ == "__main__":
    main()