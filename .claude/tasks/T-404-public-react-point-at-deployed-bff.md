---
id: T-404
title: "Public site (React): point Vercel's BFF_URL at the deployed BFF"
repo: cv-public-react
status: in_review
owner: tech-product-owner
branch: chore/vercel-bff-url
pr: https://github.com/erfeamor/cv-public-react/pull/9
depends_on: [T-014, T-043]   # T-043 added 2026-10-01: the deployed BFF can't serve the public routes until it has a service token
risk: normal
security_review: false
checkpoint:
  stage: h2   # review round 1 clean; Vercel preview build green
  repo: cv-public-react
  branch: chore/vercel-bff-url
  worktree: none   # main cv-public-react checkout
  commit: 3098e88
  pr: https://github.com/erfeamor/cv-public-react/pull/9
  developer: fullstack-developer
  reviewers: [code-review]
  risk: normal
  security_review: false
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a   # Vercel preview build is the CI
  updated: 2026-10-04T12:00:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 33555
    spawns: 1   # fullstack-developer (fresh)
    status: ok
    checked: 2026-10-04T12:00:00+02:00
---

> **Board review 2026-10-04 — this is a human step first.** There's no Vercel CLI or linked Vercel project on the driver's machine, so setting `BFF_URL` in the Vercel project is the **human's action** (dashboard). The driver then verifies the deployed page renders real data from the deployed BFF (`https://dvdlxl0zqepqi.cloudfront.net`, whose `/bff/api/v1/people/1/cv` answers 200 since T-043) and records the value durably in the repo (AC 2). If the page shows the `role="alert"` path, ISR may be serving a cached failure for up to `revalidate = 60` s; reload after a minute before concluding.

## Done live — 2026-10-04 (the human set the variable; the driver verified)

- **The human** set `BFF_URL = https://dvdlxl0zqepqi.cloudfront.net` (bare origin: `BffCvRepository.ts:228` appends `/bff/api/v1/people/:id/cv`) for Production in the Vercel project, and redeployed. The previous production build dated from 2026-09-26, before the BFF existed.
- **Verified by the driver:** `https://cv-public-react.vercel.app` → 200, `x-vercel-cache: HIT`, **no** `role="alert"` panel. The person's name, headline, experience company and role, and skill from the BFF's `/cv` all appear on the page. No CORS entry was added (server-side ISR fetch).
- **Found:** the production content is **T-018's durability-probe rows** ("T018 Survival Probe", "T018 Testing Co", `t018-probe-skill`). Recorded on T-501 at the human's decision.

## H1 — decided by the human, 2026-10-04

- **A missing `BFF_URL` fails the production build** (`VERCEL_ENV=production`) instead of silently shipping a page that fetches `localhost:3000`. Local dev keeps the localhost default; previews may keep it too (decide at implementation, with the reasoning).
- **Record the value** in the repo's CLAUDE.md Vercel section (AC 2).

## Implement + review — 2026-10-04 (3098e88, cv-public-react#9)

- Developer (fresh fullstack-developer, ~34k tokens): `resolveBffUrl(env)` + `BffConfigError` in `src/composition/container.ts`. Production with `BFF_URL` unset or blank throws; a trailing slash or a `/bff…` path throws anywhere; otherwise the localhost default. `app/page.tsx` rethrows `BffConfigError` (its catch-all otherwise rendered the alert), so `next build` fails at prerender. **Previews keep the default** (a preview build is the PR's CI gate). CLAUDE.md records the value.
- Red first (22 failing incl. the end-to-end page test) → 172/172. `VERCEL_ENV=production` without `BFF_URL` → `next build` exit 1; with the real value → exit 0, live data, no alert.
- Driver-verified: diff read; lint, typecheck, 172 tests, build green; **Vercel preview green**.
- **Review round 1 (driver): clean.** Only `BffConfigError` is rethrown, so real upstream failures keep the graceful alert; the suffix regex doesn't misfire on a `bff.` hostname.

## Why this exists

**A hot potato with no landing spot.** Filed 2026-08-17 during a board consistency sweep.

`cv-public-react` fetches the aggregate server-side under ISR from `BFF_URL` (`src/composition/container.ts:23`), which defaults to `localhost:3000`. In the Vercel deployment that default points at nothing — so once T-014 deploys the BFF, this site is the one consumer still not talking to it.

Three task files each pass the job to another:

- **[T-402](T-402-public-react-cv-sections.md)**: *"Pointing Vercel's `BFF_URL` at the deployed edge path is a project-setting change tracked at T-501, not a code change in this repo."*
- **[T-403](T-403-public-vanilla-deploy.md)**: *"`cv-public-react` (Vercel) is deliberately not in scope… Handle it at T-501, or file it separately if it turns out to need code."*
- **[T-501](T-501-e2e-cv-milestone.md)**: says nothing about it.

Both hand-offs were individually reasonable and the destination never accepted delivery. This task is the "file it separately" branch that T-403 offered.

## What is actually involved

Probably one Vercel environment variable — but *probably* is the reason this needs an owner rather than a bullet in someone else's checklist:

- **The value.** ~~The BFF's public edge path is `https://<cloudfront-domain>/bff/api/v1` (contract § BFF; the prefix is **not** stripped at the edge). Confirm whether `container.ts` expects the base with or without the `/bff/api/v1` suffix before setting it~~ **SETTLED by [T-406](T-406-public-react-bff-path-missing-prefix.md)'s ruling (a), 2026-09-22 (struck 2026-09-23): `BFF_URL` is a BARE ORIGIN — `https://<cloudfront-domain>`, no path — and `BffCvRepository` builds `/bff/api/v1/…` itself.** Setting the edge path this bullet used to name would now produce `/bff/api/v1/bff/api/v1/…`. The warning still stands: an off-by-one-segment here produces a 404 that looks identical to a routing bug in T-014.
- **CORS does not apply and must not be added.** This app fetches the aggregate **server-side** under ISR, so no `Origin` header is ever sent. T-014 ruling 6 explicitly refuses to add the Vercel domain to `CORS_ALLOWED_ORIGINS` for exactly this reason. If a fix here seems to need a CORS entry, something has moved to the client and that is the real finding.
- **ISR caches the result.** A wrong value bakes a failed fetch into a cached page until the next revalidation (`revalidate = 60`), and the app's graceful `role="alert"` path will render *successfully* while showing nothing. Verify by loading the deployed page, not by reading the env var.
- **Whether this needs a repo change at all** is the open question. If the default and the deployed value can both be satisfied by configuration, this is a project-setting change with a documentation note. If `container.ts` needs to fail loudly on a missing `BFF_URL` in production — the same defect T-403 fixes for `cv-public-vanilla`'s `localhost:3000` fallback — then it is a code change and it should say so.

## Acceptance criteria

- [x] The deployed Vercel site renders real person data fetched from the **deployed** BFF — verified by loading the production URL, not by inspecting configuration.
- [x] The `BFF_URL` value is recorded somewhere durable (repo README or `docs/`), because a Vercel project setting is invisible to Terraform, to git, and to every other check in this project.
- [x] No `CORS_ALLOWED_ORIGINS` entry was added for the Vercel domain, or the PR explains what changed to make one necessary.
- [x] If a missing/misconfigured `BFF_URL` currently degrades silently, it either fails the build or is recorded as an accepted behaviour with its reasoning.
- [ ] **A trailing slash on `BFF_URL` must not silently 404.** `BffCvRepository` concatenates without normalizing (`src/infrastructure/BffCvRepository.ts:64`), so `https://host/` yields `https://host//bff/api/v1/...`, which CloudFront and the BFF both reject. Either trim the slash in the composition root or assert its absence — a Vercel project setting is typed by hand into a web form, which is exactly where a trailing slash gets added. Found by `/code-review` during [T-406](T-406-public-react-bff-path-missing-prefix.md), 2026-09-22; pre-existing and deliberately not fixed there (board rule 3), recorded here because this task is the one that sets the value.
- [ ] `npm test`, `npm run typecheck`, `npm run lint`, `npm run build` pass if any code changed.

## Definition of done

The deployed site serves live data from the deployed BFF; if code changed, PR open against `master` from `chore/vercel-bff-url` with the Vercel build gate green, merged. If no code changed, the setting is applied and recorded, and this task closes with that recorded rather than assumed.

## dev-loop notes

- **Developer:** `fullstack-developer` (adapter §2 — `cv-public-react` is Next.js/TS). **Reviewers:** `/code-review` if there is code; otherwise the verification *is* the review.
- **`security_review: false`** — a base URL for a public, anonymous read endpoint. No credentials, no IAM, no CI surface.
- **Depends on T-014** and nothing else: there is no point pointing at a BFF that is not deployed. It does **not** depend on T-402 — an unrendered section list and a wrong base URL are independent defects, and fixing this one early means T-402's live check has somewhere real to point.
- **Blocks [T-501](T-501-e2e-cv-milestone.md)**, whose step 4 requires all four sections rendering on **both** public sites.
- **The human dependency:** the Vercel project setting needs whoever owns that Vercel account. No agent persona can apply it — flag it at the gate rather than reporting the task blocked.
