# BetaHealthCare

BetaHealthCare is a Primary Health Care (PHC) data platform that simulates and models PHC operations, including facility allocation, service delivery, and resource management.

Link to drive: [documentation](http://drive.google.com/drive/u/0/folders/1NaIPYqP3Tz9o6F5ACTL5sgQcKuZEsuMx)

## Quick Start

- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- Prepare population data (required for realistic allocations):

  ```bash
  # State populations (reads from data/raw/nga_admpop_adm1_2022.csv)
  python scripts/prepare_state_population.py

  # LGA populations (reads from data/raw/lga_pop_data.csv)
  python scripts/prepare_lga_population.py
  ```

  Outputs are written to `data/processed/population/`.

- Generate simulated datasets:

  ```bash
  python scripts/simulate_phc.py
  ```

  CSVs are written to `data/outputs/`.

- Start pgAdmin (optional, for managing your cloud Postgres):

  ```bash
  docker compose up -d
  ```

- Load CSVs into Postgres:

  ```bash
  python scripts/db_loader_pg.py
  ```

- Run the API server:
  ```bash
  # Ensure DATABASE_URL is set in your environment or .env
  uvicorn api.main:app --reload --port 8000
  ```

## Project Structure

```
phc_hub/
├── api/                 # FastAPI app
│   └── main.py
├── scripts/             # CLI scripts
│   ├── simulate_phc.py          # Generate simulated datasets
│   ├── db_loader_pg.py          # Load datasets into Postgres
│   ├── prepare_state_population.py
│   └── prepare_lga_population.py
├── data/
│   ├── raw/             # Source population files
│   ├── processed/
│   │   └── population/  # Prepared population CSVs
│   └── outputs/         # Simulator outputs (CSVs)
├── API_README.md        # API-specific setup and usage
├── DATA_DICTIONARY.md   # Schema and field descriptions
├── simulation_logic.md  # Modeling choices and assumptions
└── docker-compose.yml   # Postgres/pgAdmin services
```

## Data Outputs

The simulator writes the following CSVs to `data/outputs/`:

- `facilities_master.csv`
- `facility_infrastructure.csv`
- `facility_equipment.csv`
- `medicine_catalog.csv`
- `facility_medicine_stock.csv`
- `facility_hours.csv`
- `facility_services.csv`
- `facility_live_status.csv`
- `facility_daily_metrics.csv` (last 30 days)
- `facility_referrals.csv`
- `lga_daily_signals.csv` (last 30 days)

## API Overview

- Start the server: `uvicorn api.main:app --reload --port 8000`
- Base URL: `http://localhost:8000`
- Public URL: `https://beta-health-care.onrender.com`
- Hosted Docs: `https://beta-health-care.onrender.com/docs`
- Key endpoints:
  - `GET /` — API info and endpoint list
  - `GET /facilities?state=&lga=&facility_type=&ownership=&limit=&offset=`
  - `GET /facilities/{facility_id}`
  - `GET /lga-signals?state=&lga=&date_from=&date_to=&limit=&offset=`

See `API_README.md` for database setup details.

## Configuration

- Copy environment template and adjust as needed:
  ```bash
  cp .env.example .env
  ```
- Set `DATABASE_URL` in `.env` to your cloud Postgres connection string.
- pgAdmin is available at `http://localhost:5050` (from Docker Compose) with credentials from `docker-compose.yml`.

## Render Deployment

- Ensure `render.yaml` exists and includes:
  - `env: python`, `healthCheckPath: /`, and start command `uvicorn api.main:app --host 0.0.0.0 --port $PORT`.
  - `PYTHON_VERSION` set to `3.11.9` (via environment variable) and `pip` upgraded in `buildCommand`.
- In Render dashboard → your service → Environment, add `DATABASE_URL` with your cloud Postgres connection string.
- If startup fails with `ValueError: DATABASE_URL environment variable is not set`, verify the env var is present and correct in Render.
- Confirm your database allows inbound connections from Render.

## Scripts

- `scripts/prepare_state_population.py` — builds `state_population_2022.csv`
- `scripts/prepare_lga_population.py` — builds `lga_population_2022.csv`
- `scripts/simulate_phc.py` — generates all simulated datasets
- `scripts/db_loader_pg.py` — loads all datasets into Postgres

## CI Workflow

- Location: `/.github/workflows/daily-simulation.yml`
- Trigger: daily at `0 0 * * *` (UTC) and manual `workflow_dispatch`
- Steps: checkout repo, set up Python 3.10, install `requirements.txt`, load CSVs into Postgres
- Loader gating: runs only if `data/outputs` exists; otherwise logs a skip to avoid failure.
- Notifications: sends an email on success or failure
- Required Secrets (Settings → Secrets and variables → Actions):
  - `DATABASE_URL` — cloud Postgres connection string
  - `SMTP_SERVER`, `SMTP_PORT` — SMTP host and port
  - `SMTP_USERNAME`, `SMTP_PASSWORD` — SMTP credentials (use app password if needed)
  - `NOTIFY_EMAIL_FROM`, `NOTIFY_EMAIL_TO` — sender and recipient email addresses

### Manual simulation runs
- The daily workflow skips the simulator by default to keep data stable.
- To run the simulator manually, go to Actions → “BetaHealthCare Daily Simulation” → Run workflow and set:
  - `run_simulation` to `true` (optional)
  - `run_loader` to `true` if you also want to reload Postgres
  - Recommended: commit baseline CSVs to `data/outputs/` so daily loads always work. Use `run_simulation` when you intend to regenerate datasets.

## Troubleshooting

- If `data/outputs/` is empty, run the simulator: `python scripts/simulate_phc.py`.
 - If you prefer consistent daily loads, commit baseline CSVs under `data/outputs/` and regenerate via manual simulator runs when needed.
- If Postgres isn’t reachable, verify your cloud DB host/port/firewall and credentials. Use pgAdmin (`docker compose up -d`) to test connectivity.
- Verify `DATABASE_URL` matches your environment or `.env`.

## About

BetaHealthCare is designed to help teams prototype PHC data workflows quickly, with realistic datasets, clear documentation, and a simple API for queries and dashboards.
