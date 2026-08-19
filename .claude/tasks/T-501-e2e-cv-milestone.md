---
id: T-501
title: End-to-end verification of the complete CV flow
repo: cv-project (meta)
status: todo
owner:
branch: chore/m2-e2e-verification
pr:
depends_on: [T-101, T-102, T-103, T-104, T-105, T-151, T-201, T-301, T-401, T-402, T-014, T-403, T-404]
---

## Goal

Prove milestone M2 works as a system, not just as green unit tests, then close out the roadmap entry.

> **Added 2026-08-12 — this cannot be verified in AWS today.** `cv-bff-node` is not deployed (no ECR repo, no container, no edge route) and `cv-public-vanilla` has never been published (`s3://cv-project-frontend-dev/` holds only `admin/`). The whole public path is absent from the account; only the admin, which bypasses the BFF by design, is live. **T-014** (deploy the BFF) and **T-403** (deploy the public site) are therefore hard dependencies of this task, along with the contract and code changes they rest on (T-013 → T-202). If E2E here is scoped to the local compose stack instead, say so explicitly in the close-out — do not report the milestone as verified end-to-end when the public path exists only on localhost.

> **Two dependencies added 2026-08-17.** **T-105** — without it Experience is the one section the aggregate serves in unordered rows, which is precisely the defect this task would discover last and most expensively (T-105's own dev-loop note predicts it). **T-404** — pointing cv-public-react's Vercel `BFF_URL` at the deployed edge path was delegated *to this task* by both T-402 and T-403, but nothing here ever picked it up; it is now its own board line rather than an implicit step.

## Steps

1. Fresh stack: `docker compose -f docker-compose.dev.yml down -v && docker compose -f docker-compose.dev.yml up --build -d`.
2. `curl http://localhost:3000/bff/api/v1/people/1/cv` — assert all four sections present with seeded data, no `id`/`email` fields anywhere in the payload. **Path corrected 2026-08-17**: this read `/api/v1/people/1/cv` until now, which T-202 removed from the BFF entirely on 2026-08-13 — the milestone's own verification command would have 404'd.
3. Exercise one full CRUD cycle per section through the domain API (`:8080`) and confirm the change appears in the BFF payload.
4. Run the frontends (`npm run dev`) and eyeball: admin edits a section → public page shows it after reload. Covers `cv-admin-react` plus **both** public sites — `cv-public-vanilla` (T-401) and `cv-public-react` (T-402, ISR); confirm all four sections render on each.
5. Prometheus (`:9090/targets`) still shows both services up (regression check).

## Deliverables

- [ ] Meta-repo PR: roadmap in `README.md` + `README.es.md` ticks the domain-model item; `.claude/tasks/` board updated to `done` for the whole milestone (the batched board-sync commit rides on this PR).
- [ ] Any defect found does **not** get fixed in this task — file it as a new task and mark this one `blocked` until resolved.

## Definition of done

PR merged, stack verified from scratch on a clean volume.
