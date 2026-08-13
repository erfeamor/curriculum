---
id: T-202
title: "BFF: implement the public edge path and anonymous read routes"
repo: cv-bff-node
status: done
owner: fullstack-developer
branch: feat/public-routing-and-auth
pr: https://github.com/erfeamor/cv-bff-node/pull/4
depends_on: [T-013]
risk: normal
security_review: true
checkpoint:
  stage: done               # merged as b63eae2 (cv-bff-node), 2026-08-13
  repo: cv-bff-node
  branch: feat/public-routing-and-auth
  base: b953756
  worktree: none   # cv-bff-node has no competing task in flight; single-task run, no wave
  developer: fullstack-developer
  reviewers: [code-review, infrastructure-engineer, quality-assurance]
  risk: normal
  security_review: true
  env_slot: 0
  pr: https://github.com/erfeamor/cv-bff-node/pull/4
  commits: [c8e8f00, 3876307]
  a1: pass   # lint/typecheck/test/build all green, re-run independently by the driver after each round
  review_round: 1
  open_findings: 0
  review_status: CONVERGED
  security_review: done   # infrastructure-engineer, adversarial: no critical, no blocking
  review_trail: "R1 on c8e8f00. Security lens tested with raw HTTP rather than by reading — percent-encoding (%2F, %2e%2e), dot-segment traversal, double slashes, case and trailing-slash variants. No input reached a gated route anonymously. requireAuth() confirmed fail-CLOSED: missing COGNITO_ISSUER_URI under AUTH_ENABLED=true throws out of createApp() and crashes at startup rather than silently mounting no guard. 2 non-blocking applied in 3876307: HEAD not exempted (Express auto-generates a HEAD handler per GET route, so a probe would have seen 401) and allowlist case-sensitive while Express routing is not (over-gated a public URL). The i flag widens nothing — Express already dispatched those to the same public handler."
  implementation_traps: "express-unless matches plain strings by === with no :param support, so a literal '/bff/api/v1/people/:id' entry would match nothing and 401 every public request — hence anchored regexes. useOriginalUrl set explicitly rather than inherited: it defaults true in express-unless@2.1.3, but relying on a version-dependent default for an auth boundary breaks on a dependency bump."
  spawned_task: "T-204 — validate req.params.id before the upstream interpolation. Pre-existing on master, but this task moves the route from JWT-gated to anonymous, so the exposure changed even though the defect did not."
  qa_stage_4: waived   # NOT passed — never run. Waived by human decision at H2 on 2026-08-13, with CI green (test + docker) and the auth matrix proven by unit tests against createApp(). Recorded as waived rather than passed so nobody later reads this task as having had live-stack verification: no request ever traversed a real CloudFront/BFF/domain-service path.
  h2: "accepted 2026-08-13 by the human, who merged with --admin (master ruleset requires an approving review the sole account cannot self-supply)."
  budget_note: "Entered stage 0 at 263/400 turns (65.8%). A code task with TDD, A1, a forced security lens and stage-4 QA is unlikely to fit in the remaining ~137 turns. Expect a checkpointed budget stop mid-pipeline; that is the designed behavior, not a failure."
---

## Why this exists

`cv-bff-node` cannot be deployed as it stands — see T-013 for the full evidence that it is absent from AWS. Two things in `src/app.ts` make a correct deployment impossible, and both are code changes in **this** repo:

1. **`app.use('/api/v1', peopleRouter)` (`src/app.ts:26`)** makes the BFF serve `GET /api/v1/people/:id`, identical to the domain-service path CloudFront already routes to Java for the live admin. One path, two targets.
2. **`app.use('/api/v1', requireAuth())` (`src/app.ts:22-25`)** gates the *entire* `/api/v1` surface when `AUTH_ENABLED=true`. The public sites are anonymous, so a production-correct `AUTH_ENABLED=true` 401s every visitor, while `AUTH_ENABLED=false` leaves everything open. There is no middle setting today.

T-013 decides the shape; this task implements it. **Do not start before T-013 is `done`** — the whole point of the sequencing is that the route layout is not invented here.

## Scope

- Re-mount the public routes onto the base path T-013 ratified (whatever it is — read the merged contract, do not assume the recommendation).
- Replace the blanket `/api/v1` auth guard with the exemption model T-013 ratified: public read routes anonymous, everything else still gated by `AUTH_ENABLED`.
- Keep `AUTH_ENABLED=true` meaningful — the toggle must still protect whatever the contract does *not* list as public. A PR that simply removes `requireAuth()` fails this task.
- CORS (`src/app.ts:14-17`) must accept the deployed CloudFront origin, not just `localhost:4173`. It is env-driven already (`CORS_ALLOWED_ORIGINS`); confirm the deployed value is settable and documented in `.env.example`, and do not hardcode the distribution domain.
- `/metrics` (`src/app.ts:28-31`) stays reachable in-network for cv-observability. Do not move or gate it beyond what T-013 decided.

**Out of scope:** the aggregate endpoint itself (that is T-201, independent), and anything in `cv-infra` (T-014).

## Acceptance criteria

- [ ] Public routes are served on the contract's base path; a request to the *old* path either still works or is deliberately removed — whichever the contract says, asserted by a test.
- [ ] With `AUTH_ENABLED=true`, an **anonymous** request to each public read route returns 200 (test), and a request to a non-public `/api/v1` route without a token returns 401 (test). Both directions asserted — one without the other is how this regresses.
- [ ] Existing `people/:id` normalization behaviour is unchanged (no `id`, no `email`) — the existing tests still pass unmodified.
- [ ] `CORS_ALLOWED_ORIGINS` documented in `.env.example` with the deployed-origin case shown.
- [ ] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` all pass.

## Definition of done

PR open against `master` from `feat/public-routing-and-auth`, GitHub Actions green, merged. Unblocks T-014.

## dev-loop notes

- **Developer:** `fullstack-developer` (adapter §2 — `cv-bff-node` is Node 20 + Express + strict TS). **Reviewers:** `/code-review` + `infrastructure-engineer` (adapter §5 forces the security lens, see below) + `quality-assurance` on the auth-matrix coverage.
- **`security_review: true` is not a guess** — the diff touches `src/middleware/auth.ts` / the auth wiring and CORS config, both named security paths in adapter §5. A1 would force it anyway; it is set up front so the reviewer set is right from stage 0.
- **TDD, per the workspace non-negotiables.** The anonymous-200 / gated-401 pair is the test that defines this task; write it before the wiring change.
- Gates (adapter §3): `npm run lint` · `npm run typecheck` · `npm test` · `npm run build`, run from `cv-bff-node/`. Authoritative CI is **GitHub Actions**.
- Risk `normal`: single repo, small diff — but it moves an auth boundary, so it does not qualify for the `trivial` fast-path under any reading of §5.
