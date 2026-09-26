---
id: T-402
title: "Public site (React): render full CV sections"
repo: cv-public-react
status: done
owner: tech-product-owner
branch: feat/render-cv-sections
pr: https://github.com/erfeamor/cv-public-react/pull/8
depends_on: [T-201, T-405, T-409]   # T-409 added 2026-09-23, same reasoning as T-405: this task's AC renders `endDate: null` as "Present", and T-409 is what makes an ABSENT endDate distinguishable from that — rendering first would ship the wrong-"Present" defect T-409 describes. Original note on T-405: T-405 corrects the section types this task renders; building against the uncorrected ones means fixing these components too (T-405 provenance)
risk: normal
security_review: false   # render-only change; A1 re-checks against the real diff
checkpoint:
  stage: done   # merged 02ef73c (squash of cv-public-react#8), 2026-09-27 — H2 accepted by the human; QA PASS 2026-09-26: 150/150 mapped; slot-0 build had 4 headings in BFF order, "Present" x4; javascript: repoUrl as text, https one a link with rel; Skills gone when emptied; headless Chromium 0 console errors; torn down
  repo: cv-public-react
  branch: feat/render-cv-sections
  worktree: none   # removed after merge
  commit: 02ef73c   # squash merge on master (branch head was abe648c)
  pr: https://github.com/erfeamor/cv-public-react/pull/8
  developer: fullstack-developer
  reviewers: [code-review, frontend-architect]
  risk: normal
  security_review: false
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: 0
  updated: 2026-09-26T20:30:00+02:00
  budget:
    turns: 260   # --since 2026-09-25T12:49:25.700Z
    total_tokens: 45872664
    subagent_tokens: 0
    spawns: 0   # QA test plan and developer are both reused instances from the 2026-09-26 wave (SendMessage)
    status: ok
    checked: 2026-09-26T20:30:00+02:00
---

## Goal

Extend cv-public-react beyond the person head to render experience, education, skills, and projects from the BFF aggregate `GET /bff/api/v1/people/:id/cv`, following the repo's hexagonal + ISR conventions.

> **Path corrected 2026-08-17** — same correction as [T-401](T-401-public-cv-sections.md). This task said `/api/v1/people/:id/cv` until now; T-013 (2026-08-13) moved the BFF's public surface behind the `/bff` prefix and T-202 implemented it, so `/api/v1` is gone from `cv-bff-node`. The prefix is not stripped at the edge. Only `BFF_URL`'s base changes here — the fetch itself already lives in the adapter. The app already fetches the full aggregate and types it; today only `PersonHeader` is rendered. This is the React/ISR counterpart of T-401 (cv-public-vanilla).

> **Note (2026-08-12) — not a blocking dependency, but read before claiming.** The BFF this app fetches from is **not deployed to AWS** (**T-014** deploys it; **T-013** → **T-202** settle its public path and anonymous-read semantics first). Local work is unaffected — `BFF_URL` defaults to `localhost:3000` in `src/composition/container.ts:23` — but the Vercel deployment has no reachable BFF to point at, so "done" here means *renders locally / in preview against a local BFF*, not *renders in production*. Pointing Vercel's `BFF_URL` at the deployed edge path is **[T-404](T-404-public-react-point-at-deployed-bff.md)** (re-pointed 2026-08-17 — this said "tracked at T-501", which never picked it up).

> Section components + tests can be built against the contract immediately (the `Cv` type + a fixture); only the live check needs T-201 (the BFF aggregate) deployed.

## Pointers

- The domain already types every section (`Experience`, `Education`, `Skill`, `Project`, and the full `Cv` in `src/domain/cv.ts`) — **no domain changes needed**.
- Per the repo CLAUDE.md "Adding a section" recipe: add one **pure presentational component per section** in `src/presentation/components/` (mirror `PersonHeader.tsx`), compose them in `app/page.tsx` below `PersonHeader`, and put any ordering / empty-section filtering in the `loadCv` use case (`src/application/`) — keep components dumb.
- Server Components by default (no `'use client'`); React escapes interpolated text for free (unlike cv-public-vanilla's manual `escapeHtml`).
- `endDate: null` renders as "Present" (pick one word, test it). An empty section array renders **nothing** (no empty heading) — same convention as T-401.
- Keep the graceful `role="alert"` failure path in `app/page.tsx` intact; still a **single** `getCv()` call, ISR (`revalidate = 60`) unchanged.

## Acceptance criteria

- [x] A component per section (experience, education, skills, projects) rendering the contract fields; RTL test each: happy path, empty array (section omitted, no heading), and null `endDate` → "Present".
- [x] `app/page.tsx` composes all four sections below the person head from the one `getCv()` call.
- [x] ~~Any ordering / empty-section logic lives in `loadCv` with its own test.~~ **Corrected 2026-08-13 by T-006:** *empty-section* logic still lives in `loadCv` with its own test — but **ordering must not**. The contract's § Ordering makes the domain service the single source of truth and the BFF a pass-through, so sorting in `loadCv` would create a second answer that disagrees with the admin UI and cv-public-vanilla. Render each section in the order received; no `.sort()` in this repo. This task is the reason the rule matters most: ISR **caches** whatever order is rendered, so a frontend sort freezes a divergent order into a served page until the next revalidation.
- [x] `npm test`, `npm run typecheck`, and `npm run lint` pass; `npm run build` succeeds (page still prerenders static/ISR).

## Definition of done

PR open against `master` from `feat/render-cv-sections`; the Vercel build gate (`lint && typecheck && test && build`, per `vercel.json`) green; task file updated to `in_review` with the PR URL.

## Test plan — quality-assurance, 2026-09-26 (stage 0)

Jest + RTL; new cases **must fail on master first**.
- [x] Per section component (`ExperienceSection`, `EducationSection`, `SkillsSection`, `ProjectsSection`): heading plus all contract fields, **in received order** (use an out-of-order fixture); empty array → nothing, heading absent; `endDate: null` → "Present"; undated project → no date line; null/`''` optionals omitted, no literal "null"; `<ul role="list">`.
- [x] Skills: flat, received order, proficiency label from an exhaustive `Record<Proficiency, string>` (a fifth literal becomes a compile error).
- [x] `repoUrl`: link only for `http:`/`https:` via `new URL`, using T-401's adversarial matrix (mixed case, leading whitespace, tab/newline, NUL, `data:`, `vbscript:`, `//host`, bare domain). No `<a>`/`href` otherwise. React 18 does **not** sanitize `href`; it only warns on `javascript:`.
- [x] No `dangerouslySetInnerHTML` in `src/presentation/components/`; no `.sort(` in `src/`.
- [x] `app/page.tsx`: all four sections below `PersonHeader` from **one** `getCv()`; `CvFetchError`/network → alert and `CvPayloadError` → propagates (T-409 regression).
- [x] Empty-section mechanism tested where H1 places it.
- Gates: `npm test`, `typecheck`, `lint`, `build` (still static/ISR).
- Live: `BFF_URL=http://localhost:3010 npm run build` against isolated slot 0. The prerendered HTML has the four headings, "Present" on the seeded current role, order as served, and no `javascript:`/`data:` href.

## H1 decisions — human, 2026-09-26

- **The empty-section rule lives in the components.** Each section returns `null` for an empty array, and each component's tests cover it. `loadCv` stays a pure passthrough. This **amends the AC**: the struck line's surviving half ("*empty-section* logic still lives in `loadCv`") is superseded. The check is a one-line `length === 0`, it is local to the renderer as in T-401's `renderSection`, and a second owner in `loadCv` would give two test suites claim to the same rule (QA, stage 0).
- **Parity with T-401** (cv-public-vanilla, merged 2026-09-26): headings, "Present", "Mon YYYY" from a fixed English month list, no date line for an undated project, a flat skills list with a label from an exhaustive `Record<Proficiency, string>`, null/`''` optionals omitted, `<ul role="list">`.
- **AC added:** [ ] `repoUrl` becomes a link only for `http:`/`https:` (via `new URL`); any other value renders as plain text. React 18 does not sanitize `href`.
- The developer is **T-401's developer instance, reused**: it wrote the parity decisions being mirrored. That is no new spawn.
