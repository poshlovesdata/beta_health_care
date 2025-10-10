# BetaHealthCare Simulation Logic Documentation

This document explains the key logic decisions made in the BetaHealthCare data simulation code (`simulate_phc.py`), with references to the underlying SDI health survey data that informed these decisions.

## Table of Contents
1. [Facility Distribution Logic](#facility-distribution-logic)
2. [Infrastructure Simulation Logic](#infrastructure-simulation-logic)
3. [Equipment Availability Logic](#equipment-availability-logic)
4. [Medicine Availability Logic](#medicine-availability-logic)
5. [Caseload and Utilization Logic](#caseload-and-utilization-logic)
6. [Service Availability Logic](#service-availability-logic)
7. [Live Status Simulation Logic](#live-status-simulation-logic)

## Facility Distribution Logic

### Population-Weighted State Allocation
**Logic Decision:** Facilities are allocated across states proportionally to their populations, then distributed evenly across the LGAs within each state.

**Data Reference:** State population figures sourced from HDX (Nigeria – Subnational Population Statistics, 2022 projection from the 2006 census) and NBS demographic publications.

**Implementation:**
```python
# In simulate_phc.py
allocations = allocate_by_population(n_facilities)

def allocate_by_population(n_facilities):
    pop_map = load_state_population()  # reads data/processed/population/state_population_2022.csv
    # If missing, fall back to equal per-LGA allocation
    # Otherwise, compute state quotas via largest remainders and split across LGAs
```

**Fallbacks and Normalization:**
- If state population CSV is absent or undetectable, allocation falls back to even per‑LGA.
- When LGA population is available in `data/processed/population/lga_population_2022.csv`, facilities within each state are distributed across LGAs proportionally to LGA populations; otherwise, an even split across LGAs is used.
- State names normalized (e.g., remove "State" suffix; map FCT Abuja → FCT) to match `REGIONS`.

### Rural vs Urban Distribution
**Logic Decision:** The simulation uses a 60% rural, 40% urban split for facilities.

**Data Reference:** According to the SDI Nigeria 2013 survey, 60% of facilities were rural and 40% were urban. This is implemented in the code as:
```python
RURAL_SHARE = 0.60
```

**Implementation:** The simulation blends the national target with LGA-specific characteristics:
```python
rural_prob = 0.5 * RURAL_SHARE + 0.5 * l["rural_share"]
rural_urban = "rural" if np.random.rand() < rural_prob else "urban"
```

### Ownership Distribution
**Logic Decision:** The simulation uses a 92% public, 6% private, 2% NGO ownership split.

**Data Reference:** The SDI Nigeria 2013 survey showed that 92% of facilities were public and 8% were private/NGO. This is implemented as:
```python
OWNERSHIP_SPLIT = {
    "public": 0.92,
    "private": 0.06,
    "ngo": 0.02,
}
```

### Facility Type Distribution
**Logic Decision:** The simulation uses 17% hospitals, 61% health centers, and 22% health posts.

**Data Reference:** The SDI Nigeria 2013 survey showed this distribution of facility types. This is implemented as:
```python
FACILITY_TYPE_SPLIT = {
    "hospital": 0.17,
    "health_center": 0.61,  # includes "clinic"
    "health_post": 0.22,
}
```

## Infrastructure Simulation Logic

### Overall Infrastructure Availability
**Logic Decision:** Infrastructure availability (electricity, water, toilet) varies significantly by:
- Rural vs urban location (urban facilities have higher availability)
- Ownership type (private/NGO facilities have higher availability)
- Facility type (hospitals > health centers > health posts)

**Data Reference:** The SDI data showed that:
- In Nigeria, overall infrastructure availability was 28.5%
- Urban facilities had 44.7% availability vs 19.6% for rural
- Private facilities had 65.2% availability vs 20.3% for public
- Hospitals had 61.6%, health centers 25.8%, and health posts 5.5%

**Implementation:**
```python
def segment_infra_composite_prob(rural_urban, ownership, facility_type):
    # Nigeria SDI infrastructure "all three present" fractions:
    # All: 28.5; Public 20.3; Private 65.2; Rural 19.6; Urban 44.7; Hospital 61.6; Health center 25.8; Post 5.5
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
```

### Infrastructure Index Calculation

The **infrastructure_index** is a composite score (0-1) that summarizes overall infrastructure readiness:

```python
# Calculate infrastructure index as mean of three components
infra_index = np.mean([has_water, has_toilet, has_power])
```

**Formula**: `infrastructure_index = (has_improved_water + has_improved_toilet + has_electricity) / 3`

Where each component is either 1 (available) or 0 (not available).

**Example Values**:
- `0.33` = Only 1 out of 3 components available (e.g., has toilet but no water or electricity)
- `0.67` = 2 out of 3 components available (e.g., has water and toilet but no electricity)  
- `1.0` = All 3 components available (complete infrastructure)

### Two-Stage Simulation Process:

**Stage 1: Complete Infrastructure Check**
```python
composite_p = segment_infra_composite_prob(rural_urban, ownership, facility_type)
is_ready = np.random.rand() < composite_p

if is_ready:
    has_water = True
    has_toilet = True  
    has_power = True
```

**Stage 2: Individual Component Simulation (if not complete)**
```python
else:
    lik = component_likelihoods_for_nonready(rural_urban)
    has_power = bool(np.random.rand() < lik["electricity"])
    has_water = bool(np.random.rand() < lik["water"])
    has_toilet = bool(np.random.rand() < lik["toilet"])

def component_likelihoods_for_nonready(rural_urban):
    # Individual component probabilities when infrastructure is incomplete
    if rural_urban == "urban":
        return dict(electricity=0.55, water=0.65, toilet=0.45)
    else:  # rural
        return dict(electricity=0.30, water=0.55, toilet=0.35)
```

### Component-Specific Infrastructure
**Logic Decision:** When facilities lack full infrastructure, electricity is more likely to be missing than water or toilets, especially in rural areas.

**Data Reference:** The SDI data showed that electricity was a common constraint across countries, while water and toilet availability varied more by country.

The infrastructure index is used throughout the simulation to influence patient caseload, referral patterns, and service availability - facilities with higher infrastructure scores tend to see more patients and provide more reliable services.

## Equipment Availability Logic

**Logic Decision:** Equipment completeness (thermometer, stethoscope, sphygmomanometer, scale) varies by:
- Ownership (private/NGO higher than public)
- Facility type (hospitals > health centers > health posts)

**Data Reference:** The SDI Nigeria data showed:
- Overall equipment completeness: 51.7%
- Public: 45.8%, Private: 78.1%
- Hospitals: 77.9%, Health centers: 54.3%, Health posts: 19.0%

**Implementation:**
```python
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
```

**Logic Decision:** When equipment is incomplete, facilities are more likely to be missing just one item (70%) than multiple items (30%).

**Data Reference:** The SDI insight that "many facilities are missing just one of the four basic devices; fixing one item can move a facility from 60% to ~80–90% complete."

**Implementation:**
```python
# If not complete, miss 1 item (70%) or 2+ items (30%)
missing_k = 0 if complete else (1 if np.random.rand() < 0.7 else np.random.randint(2, 4))
```

## Medicine Availability Logic

**Logic Decision:** Medicine availability varies by:
- Ownership (private/NGO higher than public)
- Facility type (hospitals > health centers > health posts)

**Data Reference:** The SDI Nigeria data showed:
- Public: 45.8%, Private: 78.1%
- Hospitals: 77.9%, Health centers: 54.3%, Health posts: 19.0%

**Implementation:**
```python
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
```

## Caseload and Utilization Logic

**Logic Decision:** Caseload (outpatients per provider per day) varies by:
- Facility type (hospitals > health centers > health posts)
- Rural vs urban (urban slightly higher)
- Ownership (private slightly higher)

**Data Reference:** The SDI Nigeria data showed:
- Average: 2.8 outpatients per provider per day
- 86% of facilities under 5 patients/provider/day
- Hospitals: ~4.1, Health centers: ~2.7, Health posts: ~2.0
- Rural: ~2.6, Urban: ~3.2

**Implementation:**
```python
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
```

## Service Availability Logic

**Logic Decision:** Service availability is influenced by:
- Facility type (hospitals offer more services)
- Equipment and infrastructure availability
- Medicine availability for related services

**Data Reference:** The SDI insight that lower-level facilities (health posts) have lower readiness for services due to equipment and medicine constraints.

**Implementation:** Services are assigned based on facility characteristics, with higher-level facilities more likely to offer complex services like lab services and minor surgery.

## Medicine Catalog Logic

**Logic Decision:** A standardized catalog of essential medicines is created based on WHO Essential Medicines List and common PHC needs in Nigeria.

**Data Reference:** SDI surveys track medicine availability but don't provide a standardized catalog. The simulation creates a realistic medicine list based on common PHC needs.

**Implementation:**
```python
MEDICINES = [
    ("ACT-ART", "Artemisinin-based combo therapy", "malaria", "tab", "tabs", True),
    ("AMX-500", "Amoxicillin 500mg", "antibiotic", "cap", "caps", True),
    ("ORS-ZNC", "ORS + Zinc co-pack", "diarrhea", "sachet", "packs", True),
    # ... 8 essential medicines total
]
```

## Facility Hours Logic

**Logic Decision:** Operating hours vary by facility type, with hospitals often 24/7, health centers having standard business hours, and health posts having limited hours.

**Data Reference:** SDI doesn't systematically capture operating hours, but the simulation reflects realistic operational patterns for different facility types.

**Implementation:**
```python
def generate_facility_hours(fac_df):
    # Hospitals: 85% are 24/7, others 8am-8pm weekdays
    # Health Centers: 8am-4pm weekdays, 8am-1pm Saturday, 25% open Sunday
    # Health Posts: 9am-3pm weekdays, 40% open Saturday morning
```

## Facility Referrals Logic

**Logic Decision:** Referrals are generated from facilities with high stockouts/equipment gaps to higher-level facilities in the same LGA.

**Data Reference:** SDI data shows readiness gaps that would necessitate referrals. The simulation creates referrals based on facility readiness scores.

**Implementation:**
```python
def generate_referrals(fac_df, daily_df):
    # Facilities with stockouts + equipment gaps ≥ 3 generate referrals
    # Referrals go to hospitals first, then health centers in same LGA
    reason_codes = ["stockout", "equipment", "specialist_needed", "capacity"]
```

## LGA Daily Signals Logic

**Logic Decision:** Syndromic surveillance signals are aggregated at LGA level to simulate disease surveillance patterns.

**Data Reference:** While SDI doesn't capture syndromic data, the simulation creates realistic disease patterns based on typical PHC caseloads.

**Implementation:**
```python
def generate_lga_signals(fac_df, daily_df):
    # Fever: 40-60% of outpatients
    # Diarrhea: 10-25% of outpatients  
    # Respiratory: 20-40% of outpatients
```

## Live Status Simulation Logic

**Logic Decision:** Power availability affects service delivery and is simulated as a dynamic factor.

**Data Reference:** The SDI insight that "Electricity is a common constraint; water/toilets vary by country" and "PHC Hub should track power availability for vaccine cold-chain, night services, and diagnostics."

**Implementation:**
```python
def choose_power_source(rural_urban):
    # Reflect frequent electricity issues; rural uses solar/generator more
    if rural_urban == "urban":
        return np.random.choice(["grid", "generator", "solar", "none"], p=[0.6, 0.25, 0.10, 0.05])
    else:
        return np.random.choice(["grid", "generator", "solar", "none"], p=[0.35, 0.30, 0.25, 0.10])
```

**Logic Decision:** Network connectivity is correlated with power availability.

**Implementation:**
```python
def network_status(power_on):
    if not power_on:
        return np.random.choice(["ok", "slow", "down"], p=[0.2, 0.4, 0.4])
    return np.random.choice(["ok", "slow", "down"], p=[0.7, 0.25, 0.05])
```

This documentation provides a comprehensive explanation of how the simulation logic in `simulate_phc.py` directly implements the insights from the SDI health surveys, particularly focusing on the Nigeria 2013 data.