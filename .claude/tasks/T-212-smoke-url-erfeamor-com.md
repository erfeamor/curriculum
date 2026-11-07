---
id: T-212
title: "Smoke test on erfeamor.com (and the arm64-only decision)"
repo: cv-bff-node
status: done
owner: claude
branch: chore/smoke-erfeamor-com
pr: cv-bff-node#15
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

- [x] The master deploy's smoke test passes against erfeamor.com.

## H1 decision 2026-11-07

Smoke URL only. The arm64-only item is **declined**: it saves cents of ECR storage and needs matching changes in cv-infra (`CLAUDE.md`, `registry.tf`), more risk than value. Revisit only if T-117 wants it.

## DONE 2026-11-07

cv-bff-node#15 merged; the master pipeline (deploy + smoke test against `https://erfeamor.com/bff/api/v1/people/1/cv`) is green. The arm64-only item was declined at H1.
