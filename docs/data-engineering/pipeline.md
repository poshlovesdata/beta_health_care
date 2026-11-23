---
layout: default
title: Architecture & Data Flow
parent: Data Engineering
nav_order: 2
---

# Architecture & Data Flow

This page describes the end-to-end pipeline from data generation to serving.

## High-Level Flow
1. Prepare population data (`scripts/prepare_state_population.py`, `scripts/prepare_lga_population.py`).
2. Generate simulated datasets (`scripts/simulate_phc.py`) → CSVs in `data/outputs/`.
3. Load CSVs into Postgres (`scripts/db_loader_pg.py`).
4. Serve data via FastAPI (`api/main.py`).
5. Deploy on Render (`render.yaml`).
6. Automate with GitHub Actions (`.github/workflows/daily-simulation.yml`).
7. Integrate downstream apps (WonderCare) via deploy hooks (`.github/workflows/wondercare-integration.yml`).

## GitHub Actions Workflows
- Daily Simulation & Loader: runs on schedule and manual dispatch. Sends email notifications. Manual inputs allow opting into simulation and loader.
- WonderCare Integration: triggers redeploy of Streamlit apps (Manager & Bot) after successful pipeline runs.
- Docs Deploy: builds and publishes GitHub Pages from `docs/`.

## Data Tables (Conceptual)
- Facilities, Infrastructure, Equipment — static/semi-static attributes.
- Services, Hours — provision capability and schedule.
- Live Status — dynamic operational signals (power, connectivity, readiness).
- Daily Metrics — throughput, staffing, downtime.
- Referrals — inter-facility movements due to readiness/capacity.
- LGA Signals — aggregated syndromic surveillance at the LGA level.

## Environment & Secrets
- Local: `.env` with `DATABASE_URL`.
- CI: GitHub Actions secrets (`DATABASE_URL`, SMTP creds, deploy hooks).
- Cloud: Render service with `DATABASE_URL` env var.