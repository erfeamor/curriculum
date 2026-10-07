---
id: T-501
title: End-to-end verification of the complete CV flow
repo: cv-project (meta)
status: in_progress
owner: tech-product-owner
branch: chore/m2-e2e-verification
pr:
depends_on: [T-101, T-102, T-103, T-104, T-105, T-151, T-201, T-301, T-401, T-402, T-014, T-043, T-403, T-404, T-503]
risk: normal   # verification + docs; no code, but it gates the milestone
security_review: false
checkpoint:
  stage: implement   # H1 2026-10-07: verification (local from scratch + AWS), then T-015's doc claims
  repo: cv-project (meta)
  branch: chore/m2-e2e-verification
  worktree: none
  commit:
  pr:
  developer: tech-product-owner   # driver-run verification + docs (no developer spawn)
  reviewers: [code-review]
  risk: normal
  security_review: false
  review_round: 2
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: local dev stack (docker-compose.dev.yml) + live AWS
  updated: 2026-10-07T12:00:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 0
    spawns: 0
    status: ok   # human-reported /usage under ~40%
    checked: 2026-10-07T12:00:00+02:00
---

## H1 — decided by the human, 2026-10-07

1. **Doc scope: T-015's claims only.** Fix the roadmap/backlog lines that state the wrong thing and the request-flow's deployed-vs-target wording, each verified against the account. The `t4g`/OIDC/doorbell refresh and the Mermaid diagram stay in [T-502](T-502-final-docs-architecture-diagram.md).
2. **Local stack from scratch with `down -v`**: nothing authored locally to keep (Grafana's UI dashboards included).
3. **Step 4 by HTTP:** the driver runs the three frontends locally and checks the served pages and the admin-edit → BFF round trip with curl; the human has eyeballed production (admin + React) and checks the vanilla root. No QA spawn.
4. **Budget:** `/usage` under ~40%: the whole task this window.

> **Production content is now [T-503](T-503-production-cv-content.md)** (filed 2026-10-06, a dependency; **done 2026-10-06: the human's own CV is live, person 1**): found 2026-10-04 at T-404's live check, production's only person is T-018's durability probe ("T018 Survival Probe"), and both public sites render it. T-503 is the human entering the real CV through `/admin/` and removing the probe rows; step 6 below verifies against that content.

> **Board review 2026-09-28**: this task's PR **also carries [T-015](T-015-docs-reflect-deployed-bff.md)'s doc corrections** *(absorbed formally 2026-10-01: its criteria are in Deliverables below)* (same files, same live verification). Tick T-015's criteria in the same PR and close both together.

## Goal

Prove milestone M2 works as a system, not just as green unit tests, then close out the roadmap entry.

> ~~**Added 2026-08-12 — this cannot be verified in AWS today.** `cv-bff-node` is not deployed (no ECR repo, no container, no edge route) and `cv-public-vanilla` has never been published (`s3://cv-project-frontend-dev/` holds only `admin/`). The whole public path is absent from the account; only the admin, which bypasses the BFF by design, is live. **T-014** (deploy the BFF) and **T-403** (deploy the public site) are therefore hard dependencies of this task, along with the contract and code changes they rest on (T-013 → T-202). If E2E here is scoped to the local compose stack instead, say so explicitly in the close-out — do not report the milestone as verified end-to-end when the public path exists only on localhost.~~ **Resolved 2026-10-04:** the public path is live end to end (T-014 + T-043: the BFF behind CloudFront `/bff/*`; T-403: the vanilla site at the distribution root; T-404: cv-public-react on Vercel). Step 6 is runnable.

> **Two dependencies added 2026-08-17.** ~~**T-105** — without it Experience is the one section the aggregate serves in unordered rows, which is precisely the defect this task would discover last and most expensively (T-105's own dev-loop note predicts it).~~ **T-105 is `done` — merged 2026-08-26** (`1b9b398`, [#9](https://github.com/erfeamor/cv-domain-service/pull/9)), so this dependency is SATISFIED and all four sections now arrive ordered. It stays in `depends_on` as the satisfied edge it is. Note for step 4 of this task: the ordering it guarantees is *upstream* — the contract makes the domain service the single source of truth and every consumer a pass-through, so if a section renders out of order at this milestone, look for a `.sort()` in a frontend or the BFF, not for a regression in the domain API. **T-404** — pointing cv-public-react's Vercel `BFF_URL` at the deployed edge path was delegated *to this task* by both T-402 and T-403, but nothing here ever picked it up; it is now its own board line rather than an implicit step.

## Steps

> **Steps 1–5 are all LOCAL, and on their own they cannot satisfy this task — added 2026-08-24.** Every dependency this task gained on 2026-08-12 and 2026-08-17 (T-014, T-403, T-404) exists to put the public path *in AWS*, yet no step below ever leaves localhost. As written, the milestone could be reported verified with a green local compose stack and **not one request having traversed CloudFront → BFF → domain service → MySQL**. The 2026-08-12 note forbids *claiming* AWS verification without it, but forbidding a claim is not the same as requiring the check — so the gap was procedural, not structural. **Step 6 closes it and is not optional.**

1. Fresh stack: `docker compose -f docker-compose.dev.yml down -v && docker compose -f docker-compose.dev.yml up --build -d`.
   - ⚠️ **`down -v` drops every named volume in the project, not just MySQL's** — including `cv-dev-grafana-data`, and `cv-observability/grafana/provisioning/dashboards/` ships `dashboards.yml` with **no dashboard JSON**, so a UI-built dashboard has no repo backup. It also destroys anything authored through `cv-admin-react` on the local stack. Established empirically at [T-016](T-016-dev-prod-mysql-parity.md)'s review, after this step was written. A from-scratch volume genuinely is what this step wants — so keep `-v`, but **check with the human first if this machine's local stack holds anything authored**, rather than discovering it afterwards.
2. `curl http://localhost:3000/bff/api/v1/people/1/cv` — assert all four sections present with seeded data, no `id`/`email` fields anywhere in the payload. **Path corrected 2026-08-17**: this read `/api/v1/people/1/cv` until now, which T-202 removed from the BFF entirely on 2026-08-13 — the milestone's own verification command would have 404'd.
3. Exercise one full CRUD cycle per section through the domain API (`:8080`) and confirm the change appears in the BFF payload.
4. Run the frontends (`npm run dev`) and eyeball: admin edits a section → public page shows it after reload. Covers `cv-admin-react` plus **both** public sites — `cv-public-vanilla` (T-401) and `cv-public-react` (T-402, ISR); confirm all four sections render on each.
5. Prometheus (`:9090/targets`) still shows both services up (regression check).
6. **THE AWS PATH — the step this task's dependencies exist for (added 2026-08-24).** Repeat the two reads that matter against the **deployed** system, not localhost:
   - `curl https://<distribution>/bff/api/v1/people/1/cv` through **CloudFront**, not against the origin — assert all four sections with the production CV ([T-503](T-503-production-cv-content.md)), and no `id`/`personId`/`skillId`/`email` anywhere. Anonymous, with **no** `Authorization` header: T-013 ratified these routes as public, so a 401 here is a failure of the milestone, and a 200 obtained *with* a token proves nothing about the public path.
   - Load **both** public sites at their production URLs — `cv-public-vanilla` (CloudFront) and `cv-public-react` (Vercel, ISR via T-404's `BFF_URL`) — and confirm all four sections render with the same data. For the ISR site, confirm it after a revalidation, since a stale cached page can render correctly from data that predates the deploy.
   - Record the distribution domain and both site URLs in the close-out. **If any of this cannot be run, the milestone is `blocked`, not "verified locally"** — that is the distinction the 2026-08-12 note asked for and this step makes executable.

## Verification — 2026-10-07 (driver; every sibling repo on master)

Repos at: cv-database `0e7a566`, cv-domain-service `b0a32e6`, cv-bff-node `1037ea6`, cv-admin-react `22ea9a4`, cv-public-vanilla `609342d`, cv-public-react `2c785cb`, cv-observability `3e73e45`, cv-infra `b9f8b8d`.

1. **From scratch:** `down -v` (both volumes removed), `up --build -d`. Flyway: "Successfully applied 2 migrations … now at version v2" + the `afterMigrate` dev seeds; the BFF answered `/cv` 200 ~8 s after start.
2. **Local payload:** `localhost:3000/bff/api/v1/people/1/cv` 200, seeded "Jane Doe", experiences 3 / education 2 / skills 5 / projects 4; **no `id`, `personId`, `skillId`, `email` or `version` key anywhere** (walked recursively).
3. **CRUD per section** (domain API :8080, auth off locally; script in the session scratchpad): for experiences, educations and projects, POST 201 `version 0` → visible in the BFF → PUT 200 `version 1` → visible → **stale PUT 409** → DELETE 204 → gone from the BFF. Skills: catalog POST 201, duplicate name 409, assignment PUT 200 and upsert 200, visible with the new proficiency, DELETE 204, gone. Person: PUT 200 `version +1`, visible, stale PUT 409, restored. **34/34 on the contract's routes.** (Three extra probes of `GET /{id}` after a delete returned 405: the contract defines no single-item GET for sections, so the probe, not the service, was wrong. A `T501 Skill` row stays in the *local* catalog: the contract has no catalog DELETE.)
4. **Frontends locally:** admin `:5173/admin/` 200 (vite), vanilla `:4173` 200 (the BFF's CORS allows exactly `http://localhost:4173`), React `next dev :4300` 200 with all four section headings. An edit through the domain API (the admin's write path) appeared in the BFF payload served to the vanilla origin at once; on the React site **after the 60 s ISR window**: the first request served the stale page, the next one the edit (ISR as designed). The restore propagated the same way. *(The React repo's local `.env` points `BFF_URL` at `:3010`, a QA leftover; overridden on the command line, the file left alone.)*
5. **Prometheus:** `cv-bff-node` and `cv-domain-service` targets `up`; Grafana health 200.
6. **AWS, anonymous, through CloudFront `https://dvdlxl0zqepqi.cloudfront.net`:** `/bff/api/v1/people/1/cv` **200**, the production CV ([T-503](T-503-production-cv-content.md)): experiences 7 (newest first), education 3, skills 30, projects 2; no `id`/`personId`/`skillId`/`email`/`version`/`phone`, no `T018`. `/bff/api/v1/people/1` 200; `/bff/api/v1/people` 401; `/api/v1/people/1` 401; unknown person 404; bad id 400; `/metrics` 403. **Sites:** vanilla at the distribution root 200, admin `/admin/` 200, cv-public-react `https://cv-public-react.vercel.app/` 200 with the production CV (its ISR revalidation was observed live at T-503, 2026-10-06). The human eyeballed the admin and the React site on 2026-10-06.

**Milestone M2 verified end to end, locally from a clean volume and in AWS.** No defect found.

## Docs (T-015's claims, verified against the account)

- `README.md` + `README.es.md` roadmap: the Java API (all five resources + optimistic locking), the BFF (deployed, service token), the admin (person + four sections, `/admin/`), the vanilla landing (CloudFront root), Next.js (full CV, ISR from the deployed BFF, Vercel), observability (local-only metrics, T-052), the AWS line (app host with the domain service and the BFF, S3+CloudFront for admin + vanilla, on-demand CI host), CI/CD (GitHub Actions ×5, automated deploys and migrations).
- Backlog: removed three delivered items (automated backend deploys, MySQL backups, the remaining entities); logging now points at T-052; added T-050.
- `docs/architecture.md`: a dated **deployed state** note under the request flow; the observability bullet marked target design vs deployed state.
- **Review round 1** (`/code-review` medium on a45bd63, scope matched the branch): 9 findings, 7 accepted. Fixed: the CI/CD table now has CI and deploy per repo (it listed 3 GitHub Actions repos against the roadmap's ×5, and said nothing about how the admin and vanilla deploy: Drone → S3 `admin/`, GitHub Actions → S3 root, both verified in their pipeline files); the "Cloud Infrastructure (AWS Free Tier)" services list (Paid plan, `t4g.micro` app host running both services, `t3.small` CI host, Vercel, the services' CloudWatch log groups present but unused, Atlas not deployed) in EN and ES; `architecture.md`'s Infra bullet (it omitted the BFF) and its log-group wording; T-502's drift list narrowed to what's left. **Past H1's split, deliberately:** the instance types were corrected here (live: `t4g.micro` / `t3.small`), because the new deployed-state note made the old bullet contradict the same file. Rejected: the diagram's React → CloudFront arrow is accurate (Vercel's servers call CloudFront, as the note says); the observability item stays ticked (local metrics are configured, and the text now scopes it). The ticked "board updated to done" deliverable lands with the H2 close-out commit on this PR.
- **Review round 2** (`/code-review` medium on 9ef53c5 only; scope matched): 6 findings, all accepted and fixed. "No deploy credential lives on the CI host" was false: the admin's Drone deploy uses the `drone-deploy` IAM user's static key, kept in Drone on the CI host (`cv-infra/ssm.tf`), now named as the exception. cv-database's row now says it migrates only when a push changes `sql/migrations/**`, and the ES header no longer says "every push". cv-observability's CI only validates its configs. The BFF row now says multi-arch. The log wording is narrowed: the CI doorbell and reaper Lambdas *do* log to CloudWatch. Two design-spec Free Tier mentions (§ Logs Atlas, § Auth Cognito) were added to T-502's list instead. The fix diff was read inline by the driver and is clean.

## Deliverables

- [x] Meta-repo PR: roadmap in `README.md` + `README.es.md` ticks the domain-model item; `.claude/tasks/` board updated to `done` for the whole milestone (the batched board-sync commit rides on this PR).
- [x] **From [T-015](T-015-docs-reflect-deployed-bff.md) (absorbed 2026-10-01; its "Why" table lists the claims):** every claim it lists matches the live account at the time of the PR; anything deferred out of the T-013…T-403 chain is named in the backlog with its task ID; `docs/architecture.md` distinguishes target design from deployed state; no new claim is added that was not verified against the account.
- [x] Any defect found does **not** get fixed in this task — file it as a new task and mark this one `blocked` until resolved.

## Definition of done

PR merged, stack verified from scratch on a clean volume.
