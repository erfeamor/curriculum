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

- Extend `src/api/client.js` with `experiencesApi`, `educationsApi`, `skillsApi`, `projectsApi` following the `peopleApi` shape (token passed through, same error handling).
- Routes per section nested under the person, e.g. `/people/:id/experiences`, following the existing `App.jsx` routing style. A person "detail" page linking to its sections is the natural hub.
- Skills UI is different from the other three: pick from the global catalog (+create new), set proficiency from the enum, remove assignment.
- Forms follow `PersonFormPage.jsx` conventions (controlled inputs, labels wrapping inputs — RTL queries rely on this).

## Acceptance criteria

- [ ] Each section: list, create, edit, delete against the contract endpoints.
- [ ] Skills: catalog picker + proficiency select (4 enum values) + unassign.
- [ ] RTL tests per section page (mocked fetch): render list, submit create, delete.
- [ ] `npm test` and `npm run lint` pass.

## Definition of done

PR open against `master` from `feat/cv-sections-crud`, CI green, task updated.
