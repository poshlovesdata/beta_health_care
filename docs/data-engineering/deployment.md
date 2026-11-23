---
layout: default
title: Deployment (Render)
parent: Data Engineering
nav_order: 5
---

# Deployment (Render)

This page explains how the FastAPI service and downstream apps are deployed on Render.

## FastAPI Service
- Config file: `render.yaml`
- Env vars: `DATABASE_URL` (Postgres connection string)
- Health: `/health` endpoint served by FastAPI

## Downstream Apps (WonderCare)
- Manager Dashboard and WonderCare Bot deployed as separate Render services.
- Refresh Strategy: Trigger deploy hooks from CI after pipeline completion.
- Secrets: `RENDER_DEPLOY_HOOK_MANAGER`, `RENDER_DEPLOY_HOOK_BOT` in GitHub.

## Database
- Managed Postgres instance referenced by `DATABASE_URL`.
- Loader writes CSVs into tables on schedule or manual runs.

## Operational Tips
- Keep render instances modest to control costs.
- Use `autoDeploy: false` and deploy hooks to control refresh cadence.
- Monitor logs and add simple health checks post-deploy.