# Architecture Notes

See [README.md](../README.md) / [README.es.md](../README.es.md) for the full spec. This file tracks decisions and details that don't belong in the top-level pitch.

## Repo topology

`cv-project` (this repo) is the **meta repo**: orchestration scripts, shared docs, diagrams, and the global devcontainer. It holds no application code and no submodules. The eight product repos are ordinary siblings on disk, cloned via [`../clone-all.sh`](../clone-all.sh):

- `cv-database`
- `cv-domain-service`
- `cv-bff-node`
- `cv-admin-react`
- `cv-public-vanilla`
- `cv-public-react`
- `cv-observability`
- `cv-infra`

Each has its own git history, CI pipeline, issue tracker, and release cadence.

## Request flow

```
cv-public-vanilla ─┐                    /bff/*
cv-public-react   ─┴→ CloudFront ──────────────→ cv-bff-node → cv-domain-service → cv-database
cv-admin-react ─────→ CloudFront ──────────────→ cv-domain-service → cv-database
                                        /api/*
```

The two edge prefixes are the routing contract (`docs/api-contract.md` § BFF, amended 2026-08-13 by T-013). `/bff/*` reaches the BFF on :3000; `/api/*` reaches the domain service on :8080. They are distinct because both services would otherwise claim `GET /api/v1/people/:id`. The prefix is carried through to the origin, not stripped, so the BFF serves `/bff/api/v1/...` in every environment.

`cv-admin-react` talks directly to `cv-domain-service`, bypassing the BFF, since the admin UI needs full CRUD rather than the aggregated/normalized shape the public site consumes. `cv-public-react` consumes the same BFF aggregate as `cv-public-vanilla`; it renders via ISR, so at runtime it only ever calls the BFF and is otherwise decoupled from `cv-domain-service`.

The BFF's public read routes (`GET /bff/api/v1/people/:id` and `.../cv`) serve anonymous traffic by an explicit allowlist even when `AUTH_ENABLED=true` — see the contract for why that is deliberate and what it puts at stake.

## Cross-cutting concerns

- **Auth**: AWS Cognito issues JWTs. `cv-domain-service` and `cv-bff-node` both validate tokens independently; `cv-admin-react` is the only client that authenticates interactively.
- **Observability**: metrics (Prometheus/Grafana via Micrometer / prom-client) and logs (MongoDB Atlas or CloudWatch) are deliberately separate pipelines, not a unified stack. See `cv-observability`.
- **Infra**: all AWS resource choices stay within Free Tier limits (EC2 t2/t3.micro running a self-hosted MySQL 8.4 container — no RDS, S3+CloudFront, Cognito, CloudWatch, SSM Parameter Store). See `cv-infra`.

See [../diagrams/architecture.mmd](../diagrams/architecture.mmd) for a renderable diagram.
