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

> **Steps 1–5 are all LOCAL, and on their own they cannot satisfy this task — added 2026-08-24.** Every dependency this task gained on 2026-08-12 and 2026-08-17 (T-014, T-403, T-404) exists to put the public path *in AWS*, yet no step below ever leaves localhost. As written, the milestone could be reported verified with a green local compose stack and **not one request having traversed CloudFront → BFF → domain service → MySQL**. The 2026-08-12 note forbids *claiming* AWS verification without it, but forbidding a claim is not the same as requiring the check — so the gap was procedural, not structural. **Step 6 closes it and is not optional.**

1. Fresh stack: `docker compose -f docker-compose.dev.yml down -v && docker compose -f docker-compose.dev.yml up --build -d`.
   - ⚠️ **`down -v` drops every named volume in the project, not just MySQL's** — including `cv-dev-grafana-data`, and `cv-observability/grafana/provisioning/dashboards/` ships `dashboards.yml` with **no dashboard JSON**, so a UI-built dashboard has no repo backup. It also destroys anything authored through `cv-admin-react` on the local stack. Established empirically at [T-016](T-016-dev-prod-mysql-parity.md)'s review, after this step was written. A from-scratch volume genuinely is what this step wants — so keep `-v`, but **check with the human first if this machine's local stack holds anything authored**, rather than discovering it afterwards.
2. `curl http://localhost:3000/bff/api/v1/people/1/cv` — assert all four sections present with seeded data, no `id`/`email` fields anywhere in the payload. **Path corrected 2026-08-17**: this read `/api/v1/people/1/cv` until now, which T-202 removed from the BFF entirely on 2026-08-13 — the milestone's own verification command would have 404'd.
3. Exercise one full CRUD cycle per section through the domain API (`:8080`) and confirm the change appears in the BFF payload.
4. Run the frontends (`npm run dev`) and eyeball: admin edits a section → public page shows it after reload. Covers `cv-admin-react` plus **both** public sites — `cv-public-vanilla` (T-401) and `cv-public-react` (T-402, ISR); confirm all four sections render on each.
5. Prometheus (`:9090/targets`) still shows both services up (regression check).
6. **THE AWS PATH — the step this task's dependencies exist for (added 2026-08-24).** Repeat the two reads that matter against the **deployed** system, not localhost:
   - `curl https://<distribution>/bff/api/v1/people/1/cv` through **CloudFront**, not against the origin — assert all four sections, seeded data, and no `id`/`personId`/`skillId`/`email` anywhere. Anonymous, with **no** `Authorization` header: T-013 ratified these routes as public, so a 401 here is a failure of the milestone, and a 200 obtained *with* a token proves nothing about the public path.
   - Load **both** public sites at their production URLs — `cv-public-vanilla` (CloudFront) and `cv-public-react` (Vercel, ISR via T-404's `BFF_URL`) — and confirm all four sections render with the same data. For the ISR site, confirm it after a revalidation, since a stale cached page can render correctly from data that predates the deploy.
   - Record the distribution domain and both site URLs in the close-out. **If any of this cannot be run, the milestone is `blocked`, not "verified locally"** — that is the distinction the 2026-08-12 note asked for and this step makes executable.

## Deliverables

- [ ] Meta-repo PR: roadmap in `README.md` + `README.es.md` ticks the domain-model item; `.claude/tasks/` board updated to `done` for the whole milestone (the batched board-sync commit rides on this PR).
- [ ] Any defect found does **not** get fixed in this task — file it as a new task and mark this one `blocked` until resolved.

## Definition of done

PR merged, stack verified from scratch on a clean volume.
