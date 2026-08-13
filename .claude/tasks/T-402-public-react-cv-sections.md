---
id: T-402
title: "Public site (React): render full CV sections"
repo: cv-public-react
status: todo
owner:
branch: feat/render-cv-sections
pr:
depends_on: [T-201]
---

## Goal

Extend cv-public-react beyond the person head to render experience, education, skills, and projects from the BFF aggregate `GET /api/v1/people/:id/cv`, following the repo's hexagonal + ISR conventions. The app already fetches the full aggregate and types it; today only `PersonHeader` is rendered. This is the React/ISR counterpart of T-401 (cv-public-vanilla).

> **Note (2026-08-12) — not a blocking dependency, but read before claiming.** The BFF this app fetches from is **not deployed to AWS** (**T-014** deploys it; **T-013** → **T-202** settle its public path and anonymous-read semantics first). Local work is unaffected — `BFF_URL` defaults to `localhost:3000` in `src/composition/container.ts:23` — but the Vercel deployment has no reachable BFF to point at, so "done" here means *renders locally / in preview against a local BFF*, not *renders in production*. Pointing Vercel's `BFF_URL` at the deployed edge path is a project-setting change tracked at T-501, not a code change in this repo.

> Section components + tests can be built against the contract immediately (the `Cv` type + a fixture); only the live check needs T-201 (the BFF aggregate) deployed.

## Pointers

- The domain already types every section (`Experience`, `Education`, `Skill`, `Project`, and the full `Cv` in `src/domain/cv.ts`) — **no domain changes needed**.
- Per the repo CLAUDE.md "Adding a section" recipe: add one **pure presentational component per section** in `src/presentation/components/` (mirror `PersonHeader.tsx`), compose them in `app/page.tsx` below `PersonHeader`, and put any ordering / empty-section filtering in the `loadCv` use case (`src/application/`) — keep components dumb.
- Server Components by default (no `'use client'`); React escapes interpolated text for free (unlike cv-public-vanilla's manual `escapeHtml`).
- `endDate: null` renders as "Present" (pick one word, test it). An empty section array renders **nothing** (no empty heading) — same convention as T-401.
- Keep the graceful `role="alert"` failure path in `app/page.tsx` intact; still a **single** `getCv()` call, ISR (`revalidate = 60`) unchanged.

## Acceptance criteria

- [ ] A component per section (experience, education, skills, projects) rendering the contract fields; RTL test each: happy path, empty array (section omitted, no heading), and null `endDate` → "Present".
- [ ] `app/page.tsx` composes all four sections below the person head from the one `getCv()` call.
- [ ] ~~Any ordering / empty-section logic lives in `loadCv` with its own test.~~ **Corrected 2026-08-13 by T-006:** *empty-section* logic still lives in `loadCv` with its own test — but **ordering must not**. The contract's § Ordering makes the domain service the single source of truth and the BFF a pass-through, so sorting in `loadCv` would create a second answer that disagrees with the admin UI and cv-public-vanilla. Render each section in the order received; no `.sort()` in this repo. This task is the reason the rule matters most: ISR **caches** whatever order is rendered, so a frontend sort freezes a divergent order into a served page until the next revalidation.
- [ ] `npm test`, `npm run typecheck`, and `npm run lint` pass; `npm run build` succeeds (page still prerenders static/ISR).

## Definition of done

PR open against `master` from `feat/render-cv-sections`; the Vercel build gate (`lint && typecheck && test && build`, per `vercel.json`) green; task file updated to `in_review` with the PR URL.
