---
id: T-036
title: "`qa-env-override.py` shifts the BFF's host port but not its CORS allowlist, so a port-shifted frontend preview is CORS-blocked"
repo: cv-project (meta)
status: todo
owner:
branch: fix/qa-env-cors-origins
pr:
depends_on: []
risk: normal
security_review: false   # a dev/QA-only compose override; production CORS lives in cv-infra and is untouched
---

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
