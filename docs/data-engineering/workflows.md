---
layout: default
title: CI/CD Workflows
parent: Data Engineering
nav_order: 4
---

# CI/CD Workflows

This page documents the GitHub Actions workflows and how they tie the pipeline together.

## Daily Simulation & Loader (`.github/workflows/daily-simulation.yml`)
- Triggers: Daily cron and manual dispatch (`workflow_dispatch`).
- Inputs: `run_simulation` (bool), `run_loader` (bool).
- Behavior:
  - Scheduled: simulation skipped by default; loader runs against committed baseline outputs.
  - Manual: set `run_simulation=true` to regenerate outputs; `run_loader=true` to reload DB.
- Notifications: Email on success/failure with summary.

## WonderCare Integration (`.github/workflows/wondercare-integration.yml`)
- Purpose: Trigger Render redeploys for downstream Streamlit apps after successful pipeline runs.
- Triggers: On completion of daily workflow or manual dispatch.
- Secrets: `RENDER_DEPLOY_HOOK_MANAGER`, `RENDER_DEPLOY_HOOK_BOT`.

## Docs Deploy (`.github/workflows/deploy-docs.yml`)
- Purpose: Build and publish GitHub Pages from `docs/` using Jekyll.
- Triggers: Push to `main` or manual dispatch.
- Permissions: `pages:write`, `id-token:write` for deployment.
- Build: `actions/jekyll-build@v1` with theme `jekyll-theme-cayman`.

## Operational Guidance
- To refresh datasets: run daily workflow with `run_simulation=true`, then `run_loader=true`.
- To redeploy apps: use WonderCare integration manual dispatch.
- To update docs: edit files under `docs/` and push to `main`.