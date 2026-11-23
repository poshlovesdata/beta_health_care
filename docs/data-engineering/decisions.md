---
layout: default
title: Decisions & Rationale
parent: Data Engineering
nav_order: 3
---

# Decisions & Rationale

This page captures the key decisions made throughout the data engineering process, and why.

## Simulator: Opt-in on Cron, Manual Control Available
- Decision: Skip simulation on daily scheduled runs by default; allow manual triggering via inputs.
- Why: Reduce CI costs and runtime while keeping the ability to refresh data when needed.
- Notes: `workflow_dispatch` inputs `run_simulation` and `run_loader` control behavior.

## Baseline Outputs Committed
- Decision: Commit baseline CSVs under `data/outputs/` to ensure loader can run reliably on schedule.
- Why: Prevent CI failures when simulation is skipped; guarantee data availability for loader and downstream apps.
- Impact: Loader steps run unconditionally and succeed if files exist; keep outputs lightweight or use Git LFS for large files.

## Scale Parameters (N_FACILITIES = 3000)
- Decision: Use `N_FACILITIES=3000` with `DAYS_HISTORY=30`, and moderate counts for `SERVICES` and `MEDICINES`.
- Why: Balance realism with performance to keep CI under time limits.
- Guidance: Adjust referrals and stock scaling proportionally; be mindful of memory footprint.

## Email Notifications from CI
- Decision: Send success/failure emails on workflow completion.
- Why: Fast feedback loop for operations without needing to check CI logs manually.
- Considerations: SMTP secrets stored in GitHub; keep recipients configurable.

## Render Deployment Hooks for Downstream Apps
- Decision: Trigger Render redeploy for Manager Dashboard and WonderCare Bot after successful pipeline runs.
- Why: Ensure dashboards reflect the latest data without manual intervention.
- Alternatives: Consume API directly and poll for changes; trade-offs in freshness and cost.

## Security & Secrets Management
- Decision: Store `DATABASE_URL`, SMTP creds, and deploy hooks as GitHub Secrets.
- Why: Protect sensitive values while enabling automation.
- Practice: Minimal secret sprawl; rotate credentials periodically.

## Testing & Validation
- Decision: Validate loader runs against committed CSVs and API health checks post-deploy.
- Why: Catch integration issues early; improve reliability.
- Next: Add lightweight data sanity checks (row counts, schema checks) in CI.