---
id: T-401
title: "Public site: render full CV from the aggregate endpoint"
repo: cv-public-vanilla
status: todo
owner:
branch: feat/render-cv-sections
pr:
depends_on: [T-201]
---

## Goal

The landing page consumes `GET /api/v1/people/:id/cv` (one request instead of one-per-section) and renders experience, education, skills, and projects below the existing header card.

> Render functions + tests can be built against the contract payload immediately; only the live check needs T-201.

## Pointers

- Follow the `src/cvCard.js` pattern religiously: **pure, DOM-free functions returning HTML strings**, one per section (`renderExperience`, `renderEducation`, …), each escaping user content with the existing `escapeHtml` approach (export it or move it to a shared module).
- `src/main.js` switches from `/people/:id` to `/people/:id/cv` and composes the section renderers.
- `endDate: null` renders as "Present"/"Actualidad" — pick one, test it.
- No frameworks, no innerHTML of unescaped data — the XSS-escape test pattern in `cvCard.test.js` applies to every new renderer.

## Acceptance criteria

- [ ] Section renderers are pure functions with Vitest coverage: happy path, empty array (section omitted entirely, no empty headings), XSS escape, null `endDate`.
- [ ] `main.js` renders all sections from a single fetch of the aggregate payload.
- [ ] `npm test` and `npm run lint` pass; `npm run build` succeeds.

## Definition of done

PR open against `master` from `feat/render-cv-sections`, CI green, task updated.
