---
id: T-502
title: "Final documentation and architecture diagram (the roadmap's last unchecked item)"
repo: cv-project (meta)
status: todo
owner:
branch: docs/final-architecture
pr:
depends_on: [T-501, T-052]
risk: low
security_review: false
---

## Why

The README roadmap's last open item: "Final documentation and architecture diagram". Filed by the 2026-10-06 board review, **after** [T-501](T-501-e2e-cv-milestone.md) (which only ticks the domain-model item), so the docs describe the verified system.

## Known drift to fix (2026-10-06)

- `README.md` / `README.es.md` roadmap: "Java API … remaining entities pending", "React Admin (person CRUD)", "Next.js … (person view)": all four sections are done everywhere. CI count "GitHub Actions ×3": now ×4 (cv-domain-service's deploy workflow).
- `README.md` § stack (line ~189, "EC2 t2.micro/t3.micro") and its ES mirror: the app host is a `t4g.micro` (found at T-501, 2026-10-07).
- `docs/architecture.md`: "one `t3.micro`" → `t4g.micro` (Graviton, arm64); missing the BFF's Cognito service token (T-043), domain-service write scoping (T-116), optimistic locking (T-113), the S3 bootstrap + `cv-redeploy` (T-044), automated deploys via GitHub OIDC + per-service SSM documents (T-047/T-112/T-203), the CI host's DNS name + doorbell/reaper (T-034/T-041/T-042/T-048), the observability scope ([T-052](T-052-observability-scope-decision.md)).

## Scope

- **A current architecture diagram** (Mermaid in `docs/architecture.md` so it renders on GitHub): the edge (CloudFront paths `/`, `/admin/*`, `/api/*`, `/bff/*`), Vercel, the app host's containers, MySQL on its volume, Cognito (users + the BFF's machine client), the CI host (Jenkins, Drone, doorbell, reaper) and the deploy flows.
- Refresh `docs/architecture.md`, the README roadmap (EN + ES mirror) and per-repo README pointers where they contradict the live system.

## Acceptance criteria

- [ ] The diagram matches the live system, checked against the account and Terraform.
- [ ] No doc in the meta repo claims a state the system isn't in; the roadmap's last item ticked.
