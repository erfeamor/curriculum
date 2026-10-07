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

**Deployed state (verified against the account 2026-10-07, T-501):** every path above is live. One CloudFront distribution serves `cv-public-vanilla` at its root, `cv-admin-react` under `/admin/`, the BFF under `/bff/*` and the domain service under `/api/*`; `cv-public-react` runs on Vercel and calls the BFF through that same CloudFront domain, server-side only. The public reads (`/bff/api/v1/people/1` and `.../cv`) answer anonymously; the domain service's `/api/*` needs a token.

The two edge prefixes are the routing contract (`docs/api-contract.md` § BFF, amended 2026-08-13 by T-013). `/bff/*` reaches the BFF on :3000; `/api/*` reaches the domain service on :8080. They are distinct because both services would otherwise claim `GET /api/v1/people/:id`. The prefix is carried through to the origin, not stripped, so the BFF serves `/bff/api/v1/...` in every environment.

`cv-admin-react` talks directly to `cv-domain-service`, bypassing the BFF, since the admin UI needs full CRUD rather than the aggregated/normalized shape the public site consumes. `cv-public-react` consumes the same BFF aggregate as `cv-public-vanilla`; it renders via ISR, so at runtime it only ever calls the BFF and is otherwise decoupled from `cv-domain-service`.

The BFF's public read routes (`GET /bff/api/v1/people/:id` and `.../cv`) serve anonymous traffic by an explicit allowlist even when `AUTH_ENABLED=true` — see the contract for why that is deliberate and what it puts at stake.

## Cross-cutting concerns

- **Auth**: AWS Cognito issues JWTs. `cv-domain-service` and `cv-bff-node` both validate tokens independently; `cv-admin-react` is the only client that authenticates interactively.
- **Observability** *(target design; only partly deployed)*: metrics (Prometheus/Grafana via Micrometer / prom-client) and logs (MongoDB Atlas or CloudWatch) are deliberately separate pipelines, not a unified stack. See `cv-observability`. **Deployed state (2026-10-07):** Prometheus and Grafana run only in the local dev stack; nothing scrapes the deployed services, and no logs pipeline exists. Whether that changes is [T-052](../.claude/tasks/T-052-observability-scope-decision.md).
- **Infra**: one `t3.micro` runs `cv-domain-service` beside a self-hosted MySQL 8.4 container (no RDS), with S3+CloudFront, Cognito, CloudWatch and SSM Parameter Store; a separate `t3.small` CI host runs Jenkins and Drone and is started only for builds. The account is on AWS's **Paid plan** (since 2026-09-29, upgraded from the post-July-2025 Free Tier). The remaining credits pay first, then the card; there's no free EC2 allowance, so every instance-hour bills. The cost model is T-020's, the endgame T-012's. See `cv-infra`.

See [../diagrams/architecture.mmd](../diagrams/architecture.mmd) for a renderable diagram.
