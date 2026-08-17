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

The landing page consumes `GET /bff/api/v1/people/:id/cv` (one request instead of one-per-section) and renders experience, education, skills, and projects below the existing header card.

> **Path corrected 2026-08-17.** This task said `GET /api/v1/people/:id/cv` until now. T-013 moved the BFF's entire public surface behind the `/bff` edge prefix on 2026-08-13 and T-202 implemented it, so `/api/v1` no longer exists in `cv-bff-node` at all — in local dev as well as in AWS. T-013's own review caught this drift in T-201 and fixed it there; this file and T-402 were missed at the time. The prefix is **not** stripped at the edge, so the path above is the literal string to fetch in both environments.

> **Note (2026-08-12) — not a blocking dependency, but read before claiming.** This repo is **not deployed to AWS** and its BFF base URL falls back to `localhost:3000` in a built bundle; both are fixed by **T-403**, and the BFF this task calls is not deployed either (**T-014**). None of that blocks writing or unit-testing this rendering work, which is why `depends_on` is unchanged — but "done" here means *renders locally*, not *renders in AWS*. T-403 touches `src/main.js:3` and the workflow in this same repo; if both are in flight, sequence them rather than running them in one wave.

> Render functions + tests can be built against the contract payload immediately; only the live check needs T-201.

## Pointers

- Follow the `src/cvCard.js` pattern religiously: **pure, DOM-free functions returning HTML strings**, one per section (`renderExperience`, `renderEducation`, …), each escaping user content with the existing `escapeHtml` approach (export it or move it to a shared module).
- `src/main.js` switches from `/people/:id` to `/people/:id/cv` and composes the section renderers.
- `endDate: null` renders as "Present"/"Actualidad" — pick one, test it.
- No frameworks, no innerHTML of unescaped data — the XSS-escape test pattern in `cvCard.test.js` applies to every new renderer.

## Acceptance criteria

- [ ] Section renderers are pure functions with Vitest coverage: happy path, empty array (section omitted entirely, no empty headings), XSS escape, null `endDate`.
- [ ] `main.js` renders all sections from a single fetch of the aggregate payload.
- [ ] **Render in the order received (added 2026-08-13 by T-006):** no client-side sorting of any section. The contract's § Ordering makes the domain service the single source of truth and the BFF a pass-through; a `.sort()` here would silently disagree with the admin UI and the React site.
- [ ] `npm test` and `npm run lint` pass; `npm run build` succeeds.

## Definition of done

PR open against `master` from `feat/render-cv-sections`, CI green, task updated.
