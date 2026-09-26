---
id: T-401
title: "Public site: render full CV from the aggregate endpoint"
repo: cv-public-vanilla
status: done
owner: tech-product-owner
branch: feat/render-cv-sections
pr: https://github.com/erfeamor/cv-public-vanilla/pull/4
depends_on: [T-201, T-408]   # T-408 added 2026-09-23 — FILE-LEVEL, the T-153→T-152 kind: both edit `src/main.js:10`. T-408 also adds the first test of `main.js`, which this task then extends instead of writing blind. T-201 is satisfied.
risk: normal
security_review: false   # render-only change in a static site; A1 re-checks against the real diff
checkpoint:
  stage: done   # merged 76b216e (squash of cv-public-vanilla#4), 2026-09-26 — H2 accepted by the human. QA: PASS 2026-09-26: 53/53 mapped; headless Chromium vs slot-1 BFF rendered 4 sections, javascript: repoUrl as text, Skills omitted when emptied; stack torn down. Pre-existing tooling finding: the dev compose BFF CORS allowlist is fixed at :4173, so qa-env-override.py port shifts do not reach it
  repo: cv-public-vanilla
  branch: feat/render-cv-sections
  worktree: none   # removed after merge
  commit: 76b216e   # squash merge on master (branch head was 5e9310a)
  pr: https://github.com/erfeamor/cv-public-vanilla/pull/4
  developer: fullstack-developer
  reviewers: [code-review, frontend-architect]
  risk: normal
  security_review: false
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: 1
  updated: 2026-09-26T19:45:00+02:00
  budget:
    turns: 80   # --since 2026-09-25T12:49:25.700Z
    total_tokens: 21869911
    subagent_tokens: 0
    spawns: 2   # quality-assurance (shared) + fullstack-developer; the frontend-architect instance was reused from T-409 via SendMessage
    status: ok
    checked: 2026-09-26T18:58:00+02:00
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

- [x] Section renderers are pure functions with Vitest coverage: happy path, empty array (section omitted entirely, no empty headings), XSS escape, null `endDate`.
- [x] `main.js` renders all sections from a single fetch of the aggregate payload.
- [x] **Render in the order received (added 2026-08-13 by T-006):** no client-side sorting of any section. The contract's § Ordering makes the domain service the single source of truth and the BFF a pass-through; a `.sort()` here would silently disagree with the admin UI and the React site.
- [x] `npm test` and `npm run lint` pass; `npm run build` succeeds.

## Definition of done

PR open against `master` from `feat/render-cv-sections`, CI green, task updated.

## Test plan — quality-assurance, 2026-09-26 (stage 0)

Vitest, DOM-free; new renderers **must fail on master first**.
- [x] Per renderer (`renderExperience`, `renderEducation`, `renderSkills`, `renderProjects`): happy path (fields in received order); empty array → `''`, heading absent; `endDate: null` → "Present"; XSS — every user string (`company`, `role`, `location`, `description`, `institution`, `degree`, `fieldOfStudy`, `name`, `category`, `repoUrl`) with `<script>`/`"` payloads is escaped.
- [x] `repoUrl` scheme: `javascript:alert(1)` must never become a clickable `href` — only `http`/`https` render as a link, anything else as escaped text (entity-escaping alone does not neutralize a scheme).
- [x] `escapeHtml` lives in one shared module imported by `cvCard.js` and every renderer.
- [x] `main.js`: exactly one `fetch`, to `${BFF_URL}/bff/api/v1/people/${PERSON_ID}/cv` (the T-408 URL test is **updated**, not left beside a new one); header card + four sections rendered from one mocked aggregate; unsorted input rendered in input order (no `.sort()`); non-2xx / reject → alert still renders.
- [x] Live: `npm run build`; built page against an isolated compose stack's BFF shows sections, omits an empty one, "Present" for a null `endDate`, order as served.
- Gates: `npm test`, `npm run lint`, `npm run build`.

## H1 decisions — human, 2026-09-26

- `endDate: null` renders **"Present"** (the page is `lang="en"`). `escapeHtml` moves to one shared module.
- **AC added:** [ ] `repoUrl` becomes a link only for `http:`/`https:`; any other scheme (`javascript:`, `data:`…) renders as escaped text. Tested. Entity-escaping alone does not neutralize a scheme (QA, stage 0).
- Wave concurrency cap (adapter `max_concurrent_agents: 2`): this task's developer starts when the first of T-409 / T-108 frees a slot.
