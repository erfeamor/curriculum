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
