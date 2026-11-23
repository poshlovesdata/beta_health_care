---
layout: default
title: Overview
parent: Data Engineering
nav_order: 1
---

# Overview

BetaHealthCare is a PHC data platform that simulates and models PHC operations, then exposes the data via a FastAPI service and Metabase. The data pipeline produces realistic datasets, loads them into Postgres, and serves them for analytics, dashboards, and applications.

## Problem Statement

## Solution Approach

- Data Gathering: We used inisghts generated from SDI HEALTH SURVEYS to simulate our data. Here are the decisions we made to simulate the data to match real world [decisions.md]
- Data Ingestion: Python (SQLAlchemy)
- Data Storage: Postgresql (Aiven Cloud)
- Data Serving: FastAPI
- Data Visualisation: Metabase
- Hosting & Depoyment: Render
- Orchestration: Github Actions

## Goals

- Provide realistic, reproducible datasets for PHC planning and monitoring.
- Enable downstream apps to consume fresh data.
- Keep cloud deployments simple and reliable (Render + GitHub Actions).

## Components

- Simulator (`scripts/simulate_phc.py`): generates facility master, equipment, stock, services, hours, live status, daily metrics, referrals, and LGA signals.
- Loader (`scripts/db_loader_pg.py`): imports CSV outputs into Postgres tables.
- API (`api/main.py`): exposes endpoints for querying datasets.
- CI (`.github/workflows/daily-simulation.yml`): daily run + manual controls; email notifications.
- Deployment (`render.yaml`): Render web service config for FastAPI.
- Integration (`.github/workflows/wondercare-integration.yml`): deploy WonderCare services after pipeline completion.

## Data Outputs

Written to `data/outputs/`:

- `facilities_master.csv`, `facility_infrastructure.csv`, `facility_equipment.csv`
- `medicine_catalog.csv`, `facility_medicine_stock.csv`
- `facility_hours.csv`, `facility_services.csv`, `facility_live_status.csv`
- `facility_daily_metrics.csv`, `facility_referrals.csv`, `lga_daily_signals.csv`

## Environments

- Local development: Python 3.10, `.env` with `DATABASE_URL`, optional pgAdmin.
- Cloud: Render web service with `DATABASE_URL` env var.
- CI: GitHub Actions with secrets for DB and SMTP.
