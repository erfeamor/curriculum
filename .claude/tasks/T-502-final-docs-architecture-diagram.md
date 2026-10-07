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

## Known drift to fix (narrowed 2026-10-07 by T-501)

[T-501](T-501-e2e-cv-milestone.md)'s PR already corrected the README roadmap and backlog (EN + ES), the CI/CD table (CI and deploy per repo, GitHub Actions ×5), the "Cloud Infrastructure" services list (`t4g.micro` app host, `t3.small` CI host, Paid plan, Vercel, log groups unused), and `docs/architecture.md`'s deployed-state note, observability and Infra bullets. What's left:

- `docs/architecture.md` still lacks: the BFF's Cognito service token (T-043), machine tokens read-only (T-116), optimistic locking (T-113), the S3 bootstrap + `cv-redeploy` (T-044), the deploy and migrate flows via GitHub OIDC + per-service SSM documents (T-047/T-049/T-112/T-158/T-203), the CI host's DNS name + doorbell/reaper (T-034/T-041/T-042/T-048), the observability decision ([T-052](T-052-observability-scope-decision.md)).
- `diagrams/architecture.mmd` (linked from `architecture.md`) predates all of the above; the new Mermaid diagram replaces or updates it.
- Per-repo README pointers that contradict the live system (not yet audited).

## Scope

- **A current architecture diagram** (Mermaid in `docs/architecture.md` so it renders on GitHub): the edge (CloudFront paths `/`, `/admin/*`, `/api/*`, `/bff/*`), Vercel, the app host's containers, MySQL on its volume, Cognito (users + the BFF's machine client), the CI host (Jenkins, Drone, doorbell, reaper) and the deploy flows.
- Refresh `docs/architecture.md`, the README roadmap (EN + ES mirror) and per-repo README pointers where they contradict the live system.

## Acceptance criteria

- [ ] The diagram matches the live system, checked against the account and Terraform.
- [ ] No doc in the meta repo claims a state the system isn't in; the roadmap's last item ticked.
