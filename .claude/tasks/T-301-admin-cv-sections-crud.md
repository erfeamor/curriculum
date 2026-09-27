---
id: T-301
title: "Admin UI: CRUD for experience, education, skills, projects"
repo: cv-admin-react
status: done
owner: tech-product-owner
branch: feat/cv-sections-crud
pr: https://github.com/erfeamor/cv-admin-react/pull/13
depends_on: [T-101, T-102, T-103, T-104]
risk: normal
security_review: false   # UI over existing authenticated endpoints; A1 re-checks (auth/ paths would force it)
checkpoint:
  stage: done   # merged 1426f93 (squash of cv-admin-react#13), 2026-09-27 — H2 accepted by the human on Drone PR build 34 (push build 33 stranded by the reaper stop).
  repo: cv-admin-react
  branch: feat/cv-sections-crud
  worktree: none   # removed after merge
  commit: 1426f93   # squash merge on master (branch head was 65c8650)
  pr: https://github.com/erfeamor/cv-admin-react/pull/13
  developer: fullstack-developer
  reviewers: [code-review, frontend-architect]
  risk: normal
  security_review: false
  review_round: 3
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: 0
  updated: 2026-09-27T10:00:00+02:00
  budget:
    turns: 319   # --since 2026-09-25T12:49:25.700Z
    total_tokens: 58797319
    subagent_tokens: 0
    spawns: 3   # quality-assurance (shared) + fullstack-developer + frontend-architect (at the cap)
    status: ok
    checked: 2026-09-27T10:00:00+02:00
---

## Goal

Editing UI for the four CV sections against the domain API, per [docs/api-contract.md](../../docs/api-contract.md). This is the largest task in the milestone — if it drags, split by section into follow-up task files rather than growing the PR.

> UI + tests can be built against the contract with mocked `fetch` before the API tasks merge.

## ⚠️ This repo's CI is dead — read before relying on a green build (added 2026-08-24)

**`cv-admin-react` is the one repo on DroneCI, and its automation is currently broken in two independent ways.** Neither is this task's to fix, but this task's Definition of Done says "CI green", and as things stand that criterion cannot be met by pushing.

1. **The Drone webhook still points at the raw EIP** (`http://13.39.59.12/hook`), and [T-019](T-019-ci-host-on-demand.md)'s ruling 5 records its last delivery as **unused**. 
2. **Drone is not wired to the doorbell.** T-019's on-demand automation starts the CI host from a GitHub webhook that only `cv-domain-service` and `cv-database` were re-pointed at. A push to `cv-admin-react` therefore **neither builds nor wakes the box** — it is silent, not red.

**Owner since 2026-09-25: [T-034](T-034-release-ci-host-idle-eip.md)**, which now carries the Drone doorbell wiring and a cold-start AC for `cv-admin-react`. If T-034 has not landed when this task opens its PR, the workaround below still applies. **Also land [T-108](T-108-untransacted-update-read-modify-write.md) first where possible:** this UI is what makes concurrent edits realistic.

**Consequence for whoever claims this task:** budget for the CI host being *stopped* when you push, and do not read "no checks reported" as "CI passed". Start the box by hand (or push to one of the two wired repos first), or raise the webhook re-point at H1 as a prerequisite and let the driver decide whether it belongs here or in its own task.

**Drone smoke check, 2026-09-26 (driver, on the human's request):** a no-op commit (`2c6c45c`) pushed to a throwaway branch while the CI host was already up built **green** as Drone build #32 (`http://13.39.59.12/erfeamor/cv-admin-react/32`): install, lint, typecheck, test and build. The webhook's last delivery went from "unused" to **200**. The branch was deleted afterwards. So problem 1 above is **not** a failure today: the webhook still reaches Drone, because the EIP is still attached, and it will until T-034 releases it. Only problem 2 remains: a push to this repo does not wake a stopped host. The workaround above is therefore sufficient, and this task stays in the lane's Now group rather than waiting for T-034. The last green Drone build before this one was 2026-08-03.

**Provenance:** T-019 ruling 5 recorded this and said it was "T-301's problem when it arrives". That note was written into the board's history file rather than into this file, so the task it warns has never carried the warning. Found 2026-08-24 in a board review; recorded here because this is the file the implementer actually reads.

## Pointers

- **cv-admin-react is TypeScript + hexagonal** (`domain ← application ← composition → infrastructure`); there is no `src/api/client.js`. Follow the "Adding a section resource" recipe in the repo's `CLAUDE.md` — for each of the four sections:
  - `src/domain/` — entity + input type and reuse the `CrudRepository<TEntity, TInput>` port in `ports.ts` (mirror `person.ts`).
  - `src/infrastructure/http/<section>HttpRepository.ts` — adapter implementing the port over `httpClient.ts` (token injection, `HttpError`, 204 → null), mirroring `personHttpRepository.ts`.
  - `src/application/` — a store from a factory like `createPeopleStore(repository)`.
  - `src/store.ts` — the composition root: the only place adapters are wired into stores.
  - `src/presentation/components/` + `pages/` — a controlled form + route pages, wired into `src/App.tsx`.
- Routes per section nested under the person, e.g. `/people/:id/experiences`, following the `App.tsx` routing style. A person "detail" page linking to its sections is the natural hub.
- Skills UI is different from the other three: pick from the global catalog (+create new), set proficiency from the enum, remove assignment.
- Forms follow `PersonForm.tsx` conventions (controlled `value`/`onChange`/`onSubmit` over a domain input type, `<label>` wrapping inputs — RTL queries rely on this).

## Acceptance criteria

- [x] Each section: list, create, edit, delete against the contract endpoints.
- [x] Skills: catalog picker + proficiency select (4 enum values) + unassign.
- [x] Tests per layer: fake repository through the port for stores, mocked `global.fetch` for adapters/pages (RTL: render list, submit create, delete); reset the module-level wired store in `afterEach`.
- [x] `npm test`, `npm run typecheck`, and `npm run lint` pass.

## Definition of done

PR open against `master` from `feat/cv-sections-crud`, CI green, task updated.

## Test plan — quality-assurance, 2026-09-27 (stage 0)

Everything is new on master, so every case **must fail first**. Tests use Jest + RTL, with mocked `global.fetch` for adapters and pages and a fake repository through the port for stores. Section stores are reset in `afterEach`.
- [x] **Experience, education, projects (each):**
  - The domain input type has no `id`.
  - Adapter: GET list, POST 201, PUT 200, DELETE 204 → `null`. A 404 (the T-108 race) and a 400 (validation) surface as `HttpError` carrying status and body.
  - An optional field left blank is sent as `null`, never `''` (assert on the captured request body).
- [x] **`endDate` "current":** the UX per H1 round-trips to `endDate: null` on submit and pre-fills as current when editing a row whose `endDate` is null.
- [x] **Stores:** create, edit and delete update the list; a repository error sets `error` and leaves the list unchanged.
- [x] **Pages:**
  - List in **server order** (an out-of-order mock; no client sort).
  - Create and delete.
  - A 400 renders an inline error.
  - A 404 renders an error and leaves no stale row.
- [x] **Skills:**
  - Catalog picker in the order served. Creating a skill adds it; a duplicate → **409** with its own message.
  - Proficiency select with exactly the 4 enum values.
  - Assign is a PUT upsert: re-assigning updates in place (one entry per `skillId`).
  - Unassign is a DELETE (204); a DELETE of an unassigned skill → 404.
  - Person-skill list in the order served.
- [x] **Cross-cutting:**
  - The token is injected on every new adapter call.
  - The person hub links to the four section routes, and the nested routes render.
  - The People CRUD tests pass unmodified.
- [x] **Live, slot 0:**
  - Admin app on `VITE_DOMAIN_SERVICE_URL=http://localhost:8090`, dev server on `:5173` (already in the domain service's CORS allowlist; confirm).
  - Click through CRUD for each section, a real 409 on a duplicate skill name, and the PUT-vs-DELETE race if reproducible.
- **Gates:** `npm test`, `typecheck`, `lint`, `build`. **Drone:** start the CI host by hand before pushing.

## H1 decisions — human, 2026-09-27

- **One task, one PR** for all four sections. The human declined a split into three (hub + experience; education + projects; skills) or four.
- **"Current" is an explicit checkbox** on the experience, education and project forms. Checked, the end-date input is disabled and `endDate` is sent as `null`. Editing a row whose `endDate` is null pre-checks it. A blank end date with the box unchecked is a validation error, not "current", so a forgotten field can't claim "ongoing" (the write-side twin of T-409).
- Developer: `fullstack-developer`, fresh. Reviewers: `/code-review` + `frontend-architect`. **Drone:** the CI host is started by hand before the push (see the CI note above).

## PO correction at review round 1 — 2026-09-27

**The H1 "Current" rule is narrowed for projects.** `/code-review` (high) showed that it forced a finished, undated project to be saved as "current". The contract makes a project's `startDate` **and** `endDate` nullable. Both public sites (T-401, T-402) render an undated project with **no date line**. So for projects, "unchecked Current + blank end date = error" applies only when a start date is given. A project with neither date saves both as `null`, is not pre-checked as Current on edit, and shows no period in the list.

The human's H1 intent (never fabricate "ongoing") is preserved; this only removes a case where the rule itself fabricated it. Experience and education keep the H1 rule unchanged.

Round 1 also accepted a client-side check that `endDate` is not earlier than `startDate`. The server-side twin is filed as [T-115](T-115-section-period-cross-field-validation.md).
