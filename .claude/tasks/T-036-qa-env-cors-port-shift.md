---
id: T-036
title: "`qa-env-override.py` shifts the BFF's host port but not its CORS allowlist, so a port-shifted frontend preview is CORS-blocked"
repo: cv-project (meta)
status: done
owner: tech-product-owner
branch: fix/qa-env-cors-origins
pr: https://github.com/erfeamor/curriculum/pull/101
depends_on: []
risk: normal
security_review: false   # a dev/QA-only compose override; production CORS lives in cv-infra and is untouched
checkpoint:
  stage: done   # merged e472948 (squash of curriculum#101), 2026-09-27 — H2 accepted; live QA slot 1 all pass (GET+OPTIONS, recipe verbatim)
  repo: cv-project (meta)
  branch: fix/qa-env-cors-origins
  worktree: none   # removed after merge
  commit: e472948
  pr: https://github.com/erfeamor/curriculum/pull/101
  developer: infrastructure-engineer
  reviewers: [code-review, quality-assurance]
  risk: normal
  security_review: false
  review_round: 3   # r1: 6 findings, r2: 3, r3: clean
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: 1   # QA live CORS check
  updated: 2026-09-27T12:30:00+02:00
  budget:
    turns: 130   # --since 2026-09-27T09:19:56.000Z (baseline reset by the human)
    total_tokens: 17000000
    subagent_tokens: 0
    spawns: 2   # quality-assurance (shared plan) + infrastructure-engineer
    status: ok
    checked: 2026-09-27T12:30:00+02:00
---

## H1 — accepted by the human, 2026-09-27

**Premise re-checked: it holds.** The BFF allows only `:4173`. The 2026-09-27 observation below concerned the **domain service's** list (`5173,4173`), a different allowlist.

- **Rule:** for each service whose base compose sets `CORS_ALLOWED_ORIGINS`, the generator **adds** each frontend-port origin it lists, shifted by `(s+1)*10` (admin 5173, vanilla 4173), and keeps the base origins. The ports are derived from the base compose, not a hard-coded table. public-react (4300) fetches server-side and needs no entry.
- **Adapter §6** gets the per-slot launch recipe, including `VITE_AUTH_ENABLED=false`.
- **Live QA** includes an OPTIONS preflight. QA's 17-case plan is binding.

## The gap

`docker-compose.dev.yml` hardcodes `CORS_ALLOWED_ORIGINS: http://localhost:4173` on the `bff` service. `scripts/qa-env-override.py` remaps each service's **host port** by wave slot (adapter §6), but it leaves environment variables alone. So in an isolated QA stack, a frontend served anywhere except `:4173` gets responses **without** `Access-Control-Allow-Origin`, and a real browser blocks them.

Found by `quality-assurance` during [T-401](T-401-public-cv-sections.md)'s stage 4, 2026-09-26. The request was to preview on `:4174` to stay off the base port. `curl -H "Origin: http://localhost:4174"` returned 200 with no ACAO header, while `:4173` got one. QA worked around it by serving on `:4173`. That only worked because no other stack held that port. Two wave-parallel frontend QA runs would collide there, which the adapter §6 "known limitation" note already says about dev servers.

## Scope

- Have the generator write a per-task `CORS_ALLOWED_ORIGINS` into the override. It should cover the slot's frontend preview ports (admin, public-vanilla, public-react shifted by the same `(s+1)*10` rule) and keep the base ones. Or pick another way that makes a shifted preview work.
- Update adapter §6 to say how QA should serve a frontend against an isolated stack, and on which port.
- Add a test in the generator's existing test style, if it has tests.

## Acceptance criteria

- [ ] In an isolated stack at slot `s`, a frontend preview on that slot's shifted port gets a matching `Access-Control-Allow-Origin` from the BFF.
- [ ] The base dev stack's CORS behaviour is unchanged.
- [ ] Adapter §6 documents the preview port per slot.

## Provenance

Filed by the driver on 2026-09-26, from T-401's QA report. The human approved filing it at T-401's H2.

## Added 2026-09-27 — the admin app needs its own auth toggle in a QA stack

Found by QA in T-301's stage 4. Against an isolated stack with `AUTH_ENABLED=false`, the admin app still shows the Cognito sign-in screen when launched with only `VITE_DOMAIN_SERVICE_URL=…`. The cause is `src/auth/cognitoConfig.ts`, which gates on a separate client-side `VITE_AUTH_ENABLED` that defaults to `true` without a `.env`. `VITE_AUTH_ENABLED=false` is needed alongside it. Fold this into the same QA-recipe/adapter §6 guidance as the CORS port fix: how to launch each frontend against slot `s`, with the env vars it needs.

## Observation — 2026-09-27, from T-302's exploratory QA

On slot 0, the admin UI on `:5173` reached the port-shifted domain service on `:8090` with **no CORS workaround**. The base `CORS_ALLOWED_ORIGINS` in `docker-compose.dev.yml` lists `http://localhost:5173` statically, and the slot override does not shift the *frontend* port. **Re-check this task's premise at its H1:** the gap may only apply when the frontend itself runs on a shifted port. This comes from one QA run and is not yet a correction.

## Resolution — 2026-09-27

Merged e472948. For each service, the generator adds the frontend-port origins from the base compose, shifted by `(s+1)*10`: at slot 1, BFF gets `4173,4193` and domain-service gets `5173,4173,5193,4193`. Host-env passthroughs and unparseable origins are reported on stderr.

**Adapter §6** (local and gitignored, so it is recorded here) now carries the per-slot frontend launch recipe:
- `--strictPort` on every Vite command.
- Admin: `VITE_DOMAIN_SERVICE_URL` and `VITE_AUTH_ENABLED=false`.
- Vanilla: `VITE_BFF_URL`, plus a rebuild before `preview`.
- public-react: an explicit `BFF_URL`.

QA ran the recipe verbatim on slot 1, and every step worked first time.
