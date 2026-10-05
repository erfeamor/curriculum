---
id: T-035
title: "Move the app host from t3.micro to t4g.micro (Graviton, same 1 GB) — −$1.75/month, 20% of the instance line"
repo: cv-infra
status: done
owner: tech-product-owner
branch: feat/app-host-t4g-micro
pr: https://github.com/erfeamor/cv-infra/pull/36
depends_on: [T-014]   # deliberately AFTER, not bundled: T-014 replaces the same instance, but three changes in one high-risk apply (first BFF deploy, new CPU architecture, Flyway bump) make a failure hard to attribute. A replacement costs no money — only minutes of downtime on a demo with no users. Decided 2026-09-24.
risk: high   # replaces the production app host and changes its CPU architecture; every image it runs must exist for arm64
security_review: false   # instance type and AMI only; re-checked at A1 against the real diff
checkpoint:
  stage: done   # merged 972afb3 (squash of cv-infra#36), 2026-10-05 — applied from the branch first; H2 accepted; master plans No changes
  repo: cv-infra
  branch: feat/app-host-graviton
  worktree: none
  commit: 972afb3
  pr: https://github.com/erfeamor/cv-infra/pull/36
  developer: infrastructure-engineer
  reviewers: [code-review, security-review]
  risk: high
  security_review: true
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a   # live app host
  updated: 2026-10-05T13:00:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 55623
    spawns: 1   # infrastructure-engineer (fresh)
    status: ok   # human-reported /usage 40–75%
    checked: 2026-10-05T13:00:00+02:00
---

## H1 — decided by the human, 2026-10-05

**Stage-0 facts:** every upstream base image is multi-arch with arm64 (`mysql:8.4`, `flyway/flyway:13.7.0`, `node:20-alpine`, `eclipse-temurin:17-jre`, `maven:3.9-eclipse-temurin-17`), so **no Dockerfile or repo-code change** is needed; arm64 is a build step. This machine has buildx but no arm64 emulation. The app host's AMI lookup is pinned to `al2023-ami-2023.*-x86_64`, with `ignore_changes = [ami]` (so the swap is a deliberate `-replace`). Both image repos are public.

1. **arm64 builds: local QEMU** (`docker run --privileged --rm tonistiigi/binfmt --install arm64`, one-time until reboot), then `docker buildx build --platform linux/amd64,linux/arm64 --push`. A driver step, so this task stays **single-repo (cv-infra)**: no split.
2. **Multi-arch manifests on `:latest`** (amd64 + arm64): rollback to `t3.micro` stays a plain revert, and the x86 CI host can still run the images.
3. **`t4g.micro` (1 GiB)**, as T-043's real-path burst held with mild swap: $8.61 → **$6.86/month (−$1.75)**. Stage 4 re-measures memory on Graviton.
4. **IMDSv2 on the app host** (from T-005): `http_tokens = required`, hop limit 1. The containers never call AWS (secrets come from the host's `param()` reads), so prove that a bridge container gets no credentials.
5. **A separate arm64 AMI data source** for the app host; the CI host keeps its x86 one.
6. **The ECR lifecycle must keep a multi-arch `:latest` intact:** the current rule keeps the 2 most recent images of any kind, and a multi-arch push creates an index plus per-architecture manifests (plus attestations). Raise it so `:latest`'s children can't be expired (storage is ~$0.10/GB-month).
7. **Budget:** `/usage` 40–75%: images built and pushed (harmless to the running x86 host), developer and review, then **checkpoint before the apply**. The apply also needs `domain_service_instance_type = "t4g.micro"` in the gitignored `terraform.tfvars` (the driver edits it at apply time).

> **Board review 2026-10-04:** run this **after [T-044](T-044-app-host-bootstrap-s3-and-redeploy.md)**, so the Graviton replacement inherits the S3 bootstrap (no user_data size pressure) and its images can be rolled with `cv-redeploy` if an arm64 build needs a fix after the swap.

## Live — 2026-10-05, applied from the branch (cv-infra#36 @ 17ff6f4)

- **Before:** ECR `:latest` digests saved (domain `sha256:992a4862…` 9c989b0, bff `sha256:0be74fab…` 7d34e7d; both amd64 single-arch); state backed up (`pre-t035.tfstate`); rows person 1 (version 1), experience 1, skill 1, person_skill 1; Flyway V2. **`terraform.tfvars` (gitignored) switched to `domain_service_instance_type = "t4g.micro"`.**
- **Plan** (`-replace=aws_instance.domain_service`): 5 add / 5 destroy (the instance `t3.micro` → `t4g.micro`, AMI `al2023-ami-2023.12.20260930.0-kernel-6.18-arm64` (arm64), hop limit 2 → 1; the EIP association and volume attachment; both ECR lifecycle policies `any`/2 → `untagged`/20).
- **Apply** 20:55–20:57Z. New instance **`i-0ae1377c04594b2b0` (t4g.micro)**. Both images pushed **multi-arch** right after (bff 20:57:20, domain 20:57:39; each index carries linux/amd64 + linux/arm64 + 2 attestations). Boot done 20:59:46 (about 2 minutes).
- **Stage 4:** host `aarch64`; **mysql, domain-service (6da4732) and bff-node (7d34e7d) all arm64**; rows identical, person version 1, Flyway V2, volume `nvme1n1`, backup timer enabled. **IMDS:** host token OK (56 chars), IMDSv1 → 401, **bridge container → no token (000)**. **Memory (Graviton):** a 200-request `/cv` burst → brief swap (si/so 144/340), pressure some avg10 1.80 / full 0.60, 171 MB available afterwards (domain 320 MiB, bff 58, mysql 64), `/cv` still 200; on par with t3.micro's 4.07 / 180 MB. `cv-redeploy bff-node` works on arm64. The edge: `/cv`, `/` and `/admin/` 200; `/api` 401. The branch plans **No changes**.
- **Cost:** the app-host line goes **$8.61 → $6.86/month (−$1.75)** (T-020's model; confirm on the bill after a week, with no `CPUCredits` surplus line).

## Implement + review — 2026-10-05 (17ff6f4, cv-infra#36)

- Developer (fresh infrastructure-engineer, ~56k tokens): `data.aws_ami.al2023_arm64` for the app host (the CI host keeps x86 `al2023`); `t4g.micro` default; a **plan-time precondition** (arm64 AMI ⇔ Graviton type); IMDSv2 (`http_tokens = required`, hop limit 1); the ECR lifecycle on both repos is **`untagged` > 20 → expire**, never tagged (a multi-arch `:latest`'s children are safe); docs and runbook (buildx multi-arch). The provisioning script has no arch assumptions.
- Driver-verified: the diff; full offline gate (`terraform test` 23/23 in 16 s, scoped). **Review round 1 (code + security): clean.** Trade-off noted: a superseded untagged image survives ~4 more pushes (local rollback tarballs cover it).
- **Images:** arm64 emulation registered locally (tonistiigi/binfmt) and a buildx builder `cvbuilder`. **Both multi-arch builds succeeded, not pushed**: bff 7d34e7d (431 s), domain 6da4732 (210 s). Pushing waits for the lifecycle fix to be applied.

**Resume here (the apply window):** save the ECR digests; back up state; set `domain_service_instance_type = "t4g.micro"` in `terraform.tfvars`; `terraform plan -replace=aws_instance.domain_service` (expect: the instance replaced; the EIP association and volume attachment re-created; 2 lifecycle policies updated in place); apply; **immediately** `docker buildx build --builder cvbuilder --platform linux/amd64,linux/arm64 --push` both images to `:latest` (the bootstrap's pull loop waits); then stage 4: `docker image inspect` Architecture arm64 for all three containers; data, Flyway and the backup timer intact; the public path and admin; IMDS (a bridge container gets no token; host `param()` works); memory under a `/cv` burst on Graviton; `cv-redeploy domain-service` still works. Then H2.

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

> **2026-10-01, T-014's H1 refresh:** T-014 builds `linux/amd64` only (multi-arch declined), so **both** `cv-bff-node` and `cv-domain-service` need arm64 builds here. Whether T-112/T-203's pipelines build multi-arch is for their own H1.

## Acceptance criteria

- [x] `aws_instance.domain_service` is `t4g.micro` on an arm64 AMI; the MySQL datadir on `vol-092113db466c84bc1` survives the replacement (T-018's guarantee — confirm with `findmnt` before and after).
- [x] Every container on the box runs its arm64 variant — verified by `docker image inspect … Architecture` on the live host, not by reading the Dockerfile.
- [x] The public path works end to end after the swap: `/bff/api/v1/people/1/cv` through CloudFront, the admin through `/api/*`.
- [x] Memory headroom measured under a warm JVM and compared with T-014's numbers on `t3.micro` — the same 1 GiB, but not assumed to behave the same.
- [x] The saving recorded against [T-020](T-020-cost-model-correction.md)'s model.
- [x] **(moved from [T-005](T-005-ci-secret-blast-radius.md), board review 2026-10-01)** `aws_instance.domain_service` gets `metadata_options` `http_tokens = "required"` and `http_put_response_hop_limit = 1`; verified on the live host that no container on it (domain service, MySQL, Flyway, BFF) needs the instance role through IMDS, that a bridge container cannot obtain credentials, and that SSM and the host's own `param()` reads still work.
- [x] **The target size follows [T-014](T-014-deploy-bff-to-aws.md)'s memory measurement:** if T-014 shows the 1 GiB box can't carry JVM + MySQL + BFF, the target is `t4g.small`, and the saving is re-derived rather than assumed.

## Watch-outs

- **[T-021](T-021-mysql-password-rotation-persistent-datadir.md) applies to every replacement:** do not change `db_password` in the same apply.
- **Serialize with every other cv-infra apply.**
- T3 and T4g both default to *unlimited* CPU credits; check that the monthly bill shows no `CPUCredits` surplus line after a week on the new type.

## dev-loop notes

- **Developer:** `infrastructure-engineer` (the swap); the image-build splits go to the owners of their repos. **Reviewers:** `/code-review` + `infrastructure-engineer` + QA coverage (`risk: high`).
- ⚖ Worth doing because T-012 chose **A** — the saving pays off only if the stack outlives the Free-plan window.
