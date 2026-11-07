---
id: T-212
title: "Smoke test on erfeamor.com (and the arm64-only decision)"
repo: cv-bff-node
status: todo
owner: 
branch: chore/smoke-erfeamor-com
pr:
depends_on: [T-061]
risk: low
security_review: false
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

The deploy smoke test hard-codes `https://dvdlxl0zqepqi.cloudfront.net` (`ci.yml:187`, `README.md:51`).

## Scope

- Move the smoke URL to `https://erfeamor.com`.
- **Decide at H1** (same answer as T-117): drop the amd64 build leg. Arm runners are free for public repos, so the only saving is cents of ECR storage. If adopted, update `cv-infra/CLAUDE.md:91` and `registry.tf`'s `ecr_children_per_index`.

## Acceptance criteria

- [ ] The master deploy's smoke test passes against erfeamor.com.
