---
id: T-404
title: "Public site (React): point Vercel's BFF_URL at the deployed BFF"
repo: cv-public-react
status: todo
owner:
branch: chore/vercel-bff-url
pr:
depends_on: [T-014]
risk: normal
security_review: false
---

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

- **The value.** The BFF's public edge path is `https://<cloudfront-domain>/bff/api/v1` (contract § BFF; the prefix is **not** stripped at the edge). Confirm whether `container.ts` expects the base with or without the `/bff/api/v1` suffix before setting it — an off-by-one-segment here produces a 404 that looks identical to a routing bug in T-014.
- **CORS does not apply and must not be added.** This app fetches the aggregate **server-side** under ISR, so no `Origin` header is ever sent. T-014 ruling 6 explicitly refuses to add the Vercel domain to `CORS_ALLOWED_ORIGINS` for exactly this reason. If a fix here seems to need a CORS entry, something has moved to the client and that is the real finding.
- **ISR caches the result.** A wrong value bakes a failed fetch into a cached page until the next revalidation (`revalidate = 60`), and the app's graceful `role="alert"` path will render *successfully* while showing nothing. Verify by loading the deployed page, not by reading the env var.
- **Whether this needs a repo change at all** is the open question. If the default and the deployed value can both be satisfied by configuration, this is a project-setting change with a documentation note. If `container.ts` needs to fail loudly on a missing `BFF_URL` in production — the same defect T-403 fixes for `cv-public-vanilla`'s `localhost:3000` fallback — then it is a code change and it should say so.

## Acceptance criteria

- [ ] The deployed Vercel site renders real person data fetched from the **deployed** BFF — verified by loading the production URL, not by inspecting configuration.
- [ ] The `BFF_URL` value is recorded somewhere durable (repo README or `docs/`), because a Vercel project setting is invisible to Terraform, to git, and to every other check in this project.
- [ ] No `CORS_ALLOWED_ORIGINS` entry was added for the Vercel domain, or the PR explains what changed to make one necessary.
- [ ] If a missing/misconfigured `BFF_URL` currently degrades silently, it either fails the build or is recorded as an accepted behaviour with its reasoning.
- [ ] `npm test`, `npm run typecheck`, `npm run lint`, `npm run build` pass if any code changed.

## Definition of done

The deployed site serves live data from the deployed BFF; if code changed, PR open against `master` from `chore/vercel-bff-url` with the Vercel build gate green, merged. If no code changed, the setting is applied and recorded, and this task closes with that recorded rather than assumed.

## dev-loop notes

- **Developer:** `fullstack-developer` (adapter §2 — `cv-public-react` is Next.js/TS). **Reviewers:** `/code-review` if there is code; otherwise the verification *is* the review.
- **`security_review: false`** — a base URL for a public, anonymous read endpoint. No credentials, no IAM, no CI surface.
- **Depends on T-014** and nothing else: there is no point pointing at a BFF that is not deployed. It does **not** depend on T-402 — an unrendered section list and a wrong base URL are independent defects, and fixing this one early means T-402's live check has somewhere real to point.
- **Blocks [T-501](T-501-e2e-cv-milestone.md)**, whose step 4 requires all four sections rendering on **both** public sites.
- **The human dependency:** the Vercel project setting needs whoever owns that Vercel account. No agent persona can apply it — flag it at the gate rather than reporting the task blocked.
