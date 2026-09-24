---
id: T-035
title: "Move the app host from t3.micro to t4g.micro (Graviton, same 1 GB) — −$1.75/month, 20% of the instance line"
repo: cv-infra
status: todo
owner:
branch: feat/app-host-t4g-micro
pr:
depends_on: [T-014]   # deliberately AFTER, not bundled: T-014 replaces the same instance, but three changes in one high-risk apply (first BFF deploy, new CPU architecture, Flyway bump) make a failure hard to attribute. A replacement costs no money — only minutes of downtime on a demo with no users. Decided 2026-09-24.
risk: high   # replaces the production app host and changes its CPU architecture; every image it runs must exist for arm64
security_review: false   # instance type and AMI only; re-checked at A1 against the real diff
---

## Why this exists

Filed 2026-09-24 from the cost review behind [T-012](T-012-aws-endgame-decision.md)'s decision **A**. The app host is the largest line on the bill: `EUW3-BoxUsage:t3.micro`, **$8.61/month, 41%**. AWS Pricing API, EU (Paris), Linux on-demand, read the same day:

| Type | $/hour | $/month | RAM |
|---|---|---|---|
| `t3.micro` (today) | 0.0118 | 8.61 | 1 GiB |
| **`t4g.micro`** | **0.0094** | **6.86** | **1 GiB** |
| `t4g.nano` | 0.0047 | 3.43 | 0.5 GiB — **ruled out**: the JVM + MySQL 8.4 + the BFF do not fit |

## Cross-repo — decompose at refinement

The instance change is `cv-infra`, but **every image the box runs must exist for `linux/arm64`**, and today they are built on x86:

| Image | Where it is built today | arm64? |
|---|---|---|
| `mysql:8.4` | upstream | multi-arch ✔ |
| `flyway/flyway` | upstream | **verify for the pinned tag** (13.7.0 if T-155 has landed) |
| `cv-domain-service` | manually, and by [T-112](T-112-domain-service-ci-ecr-deploy.md) once it exists — Jenkins on the x86 CI host | needs `buildx` multi-arch or a native arm64 build |
| `cv-bff-node` | first built by [T-014](T-014-deploy-bff-to-aws.md); later [T-203](T-203-bff-ci-deploy-stage.md) | same |

Per adapter §2, stage 0 splits this into dependency-ordered single-repo tasks (image builds first, the instance swap last).

## Acceptance criteria

- [ ] `aws_instance.domain_service` is `t4g.micro` on an arm64 AMI; the MySQL datadir on `vol-092113db466c84bc1` survives the replacement (T-018's guarantee — confirm with `findmnt` before and after).
- [ ] Every container on the box runs its arm64 variant — verified by `docker image inspect … Architecture` on the live host, not by reading the Dockerfile.
- [ ] The public path works end to end after the swap: `/bff/api/v1/people/1/cv` through CloudFront, the admin through `/api/*`.
- [ ] Memory headroom measured under a warm JVM and compared with T-014's numbers on `t3.micro` — the same 1 GiB, but not assumed to behave the same.
- [ ] The saving recorded against [T-020](T-020-cost-model-correction.md)'s model.

## Watch-outs

- **[T-021](T-021-mysql-password-rotation-persistent-datadir.md) applies to every replacement:** do not change `db_password` in the same apply.
- **Serialize with every other cv-infra apply.**
- T3 and T4g both default to *unlimited* CPU credits; check that the monthly bill shows no `CPUCredits` surplus line after a week on the new type.

## dev-loop notes

- **Developer:** `infrastructure-engineer` (the swap); the image-build splits go to the owners of their repos. **Reviewers:** `/code-review` + `infrastructure-engineer` + QA coverage (`risk: high`).
- ⚖ Worth doing because T-012 chose **A** — the saving pays off only if the stack outlives the Free-plan window.
