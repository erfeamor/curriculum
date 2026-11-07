---
id: T-069
title: "M3 close: hygiene, budgets, re-measure, docs, tag M3"
repo: cv-infra + cv-project (meta)
status: todo
owner: 
branch: chore/m3-close
pr:
depends_on: [T-064, T-066, T-068]
risk: normal
security_review: false
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

Close M3 on measured numbers. Depend on T-068 only if T-067 said go; otherwise drop that dependency.

## Scope

- Lifecycle expiry for noncurrent object versions in the artifacts bucket.
- `gross_usage` budget from $30 to about 2× the measured rate. Retire `credit_runway` (`budgets.tf:207-250`) after 2027-07-12, or now with a note.
- **One week after the last host change:** measure in Cost Explorer (`RECORD_TYPE=Usage`; the zone fee posts on the 1st) and `aws freetier get-account-plan-state`.
- **Refresh the docs:**
  - the cost models in `cv-infra/CLAUDE.md` (including the stale `:72` and `:125`) and the meta CLAUDE.md
  - `docs/architecture.md` (diagram, routes, CI)
  - both READMEs
- Tag `M3` with `scripts/release-manifest.sh` and `release-tag.sh`.

## Acceptance criteria

- [ ] The measured rate is about $0.28/day (go) or $0.40/day (no-go) (T-065 dropped Spot, 2026-11-07); budgets retuned; `M3` tagged in all 9 repos.
