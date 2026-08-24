---
id: T-301
title: "Admin UI: CRUD for experience, education, skills, projects"
repo: cv-admin-react
status: todo
owner:
branch: feat/cv-sections-crud
pr:
depends_on: [T-101, T-102, T-103, T-104]
---

## Goal

Editing UI for the four CV sections against the domain API, per [docs/api-contract.md](../../docs/api-contract.md). This is the largest task in the milestone — if it drags, split by section into follow-up task files rather than growing the PR.

> UI + tests can be built against the contract with mocked `fetch` before the API tasks merge.

## ⚠️ This repo's CI is dead — read before relying on a green build (added 2026-08-24)

**`cv-admin-react` is the one repo on DroneCI, and its automation is currently broken in two independent ways.** Neither is this task's to fix, but this task's Definition of Done says "CI green", and as things stand that criterion cannot be met by pushing.

1. **The Drone webhook still points at the raw EIP** (`http://13.39.59.12/hook`), and [T-019](T-019-ci-host-on-demand.md)'s ruling 5 records its last delivery as **unused**. 
2. **Drone is not wired to the doorbell.** T-019's on-demand automation starts the CI host from a GitHub webhook that only `cv-domain-service` and `cv-database` were re-pointed at. A push to `cv-admin-react` therefore **neither builds nor wakes the box** — it is silent, not red.

**Consequence for whoever claims this task:** budget for the CI host being *stopped* when you push, and do not read "no checks reported" as "CI passed". Start the box by hand (or push to one of the two wired repos first), or raise the webhook re-point at H1 as a prerequisite and let the driver decide whether it belongs here or in its own task.

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

- [ ] Each section: list, create, edit, delete against the contract endpoints.
- [ ] Skills: catalog picker + proficiency select (4 enum values) + unassign.
- [ ] Tests per layer: fake repository through the port for stores, mocked `global.fetch` for adapters/pages (RTL: render list, submit create, delete); reset the module-level wired store in `afterEach`.
- [ ] `npm test`, `npm run typecheck`, and `npm run lint` pass.

## Definition of done

PR open against `master` from `feat/cv-sections-crud`, CI green, task updated.
