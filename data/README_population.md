Population Data for Nigeria (State & LGA-Level)

Overview

- Purpose: Provide state-level and LGA-level population figures to weight facility allocation in the simulator.
- Files produced (processed):
  - `data/processed/population/state_population_2022.csv` with columns: `state,population`
  - `data/processed/population/lga_population_2022.csv` with columns: `state,lga,population`

Sources

- Nigeria – Subnational Population Statistics (HDX): 2022 projections derived from the 2006 census, sex/age disaggregated.
- Nigeria – Subnational Population Statistics (HDX, adm2/LGA): LGA-level population estimates for 2022 projections.
- NBS – Demographic statistics publications: corroborate state ranks and trends (e.g., Kano/Lagos highest, Bayelsa lowest).

Acquisition

- Recommended: Download the HDX adm1/adm2 population CSVs and prepare via helper scripts.
- Commands:
  - State: `python scripts/prepare_state_population.py --url <direct_csv_url_adm1>`
  - LGA: `python scripts/prepare_lga_population.py --url <direct_csv_url_adm2>` or `--in data/raw/lga_pop_data.csv`
- Output files:
  - Raw (adm1): `data/raw/nga_admpop_adm1_2022.csv`
  - Prepared (adm1): `data/processed/population/state_population_2022.csv`
  - Raw (adm2): `data/raw/nga_admpop_adm2_2022.csv`
  - Prepared (adm2): `data/processed/population/lga_population_2022.csv`

Preparation & Normalization

- State prep script: detects the state name column (e.g., `adm1_name`) and population column.
- LGA prep script: detects `adm2_name` (LGA) along with state and population, sums numeric columns if needed.
- Name normalization:
  - State: remove suffix "State"; map `FCT Abuja`, `Abuja FCT`, `Abuja` → `FCT`
  - LGA: remove suffix "LGA" and trailing qualifiers in parentheses
- Aggregation:
  - State: group by normalized state name and sum population
  - LGA: group by normalized `(state, lga)` and sum population

Integration into Simulation

- `simulate_phc.py` loads `data/processed/population/state_population_2022.csv` and `data/processed/population/lga_population_2022.csv` if present.
- Allocation method: Largest‑remainder quotas by state; within each state, facility counts are split across LGAs proportionally to their population (falls back to even split if LGA populations missing).
- Fallback: If the files are missing or columns cannot be detected, the simulator allocates facilities evenly across LGAs.
- Transparency: Each facility row includes `state_population` and `lga_population` for downstream analytics.
