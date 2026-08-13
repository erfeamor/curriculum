---
id: T-014
title: Deploy cv-bff-node to AWS — registry, container, edge route
repo: cv-infra
status: todo
owner:
branch: feat/deploy-bff-node
pr:
depends_on: [T-013, T-202, T-001]
risk: high
security_review: true
---

## Why this exists

This is the task that closes the gap. `cv-bff-node` has no registry, no runtime and no route in AWS (evidence table in T-013), while `cv-infra` claims in two places that it is already running. Both the deployment and the correction of those claims live in **this** repo.

The intended approach is the domain service's, per the meta README backlog — *"backend services still deployed manually"*: build image → push to ECR → run it as a container on the existing EC2 box. This task builds the target; T-203 automates the push.

## Scope

**1. Registry** — `aws_ecr_repository.bff_node` + lifecycle policy in `registry.tf`, mirroring `domain_service`. The header comment there budgets against ECR's 500 MB; a `node:20-alpine` runtime image is ~50-60 MB compressed, so two retained tags fit comfortably. Keep `force_delete = true` for parity.

**2. Runtime** — a `docker run` block in `templates/domain-service-user-data.sh`, on the existing `cv` docker network, with:
- `DOMAIN_SERVICE_URL=http://domain-service:8080` (container-to-container on the `cv` network — **not** the public EIP; do not send BFF→domain traffic out to the internet and back),
- `AUTH_ENABLED` / `COGNITO_ISSUER_URI` per T-013's ratified auth model, issuer read from SSM like the domain service does,
- `CORS_ALLOWED_ORIGINS` including the CloudFront domain (`aws_cloudfront_distribution.frontend.domain_name` is already threaded into this template),
- `--restart unless-stopped`, and the same retry-until-the-image-exists loop the domain service uses — the image will not exist on first boot.

**3. Edge** — a CloudFront origin + `ordered_cache_behavior` in `frontend.tf` for the path T-013 ratified, **declared before** the `/api/*` behavior if the chosen prefix could otherwise be shadowed. Copy the `/api/*` behavior's no-cache posture (TTLs 0) — the aggregate is per-person and revalidated by ISR upstream, so edge caching here would fight `cv-public-react`'s own caching story.

**4. Exposure** — the BFF's port must be reachable by CloudFront but **not** open to the world beyond what that requires. Adding a second internet-facing port to `aws_security_group.domain_service` is the obvious move and the one to justify explicitly in the PR: state why the chosen ingress is no wider than needed. (`observability.tf` already has the `bff_node` log group; it is currently empty and should start receiving logs — wire it or say why not.)

**5. Correct the false claims in this repo** — `compute.tf:1` (*"Runs cv-domain-service and cv-bff-node"*) and `README.md:14` (*"plus cv-bff-node alongside it"*) both assert this task's outcome as already true. They become true with this PR; if any part of the scope is dropped, the comments must say what is actually running. Do not leave them describing an aspiration.

**6. `terraform test`** — `tests/plan.tftest.hcl` uses `mock_provider`; extend the mocks for any new data source and add assertions for what this task pins (the new ECR repo, the new behavior's origin). Per the repo's own review guidance, a task that pins a resource property updates the assertions in the same PR.

## Watch-outs (measured, not hypothetical)

- **RAM.** The box is a `t3.micro` (1 GB) already carrying MySQL 8.4 + a JVM on a 2 GB swapfile; `templates/domain-service-user-data.sh` itself recommends a `t3.small`. Adding a Node process pushes it further into swap. If the plan resizes the instance, `terraform test`'s instance-class assertion and the cost note must change **in the same PR** — and T-010's finding applies: trimming or growing run rate does not change the Free-plan cliff, so argue this on stability, not cost.
- **`user_data_replace_on_change`** is already set on `aws_instance.domain_service` and must stay. Editing the bootstrap without it updates state and never re-provisions the box — this exact bug shipped once (repo review guidance item 3). This task edits `user_data`, so the instance **will** be replaced: MySQL data lives on `/var/lib/cv-mysql` on the host volume and **is lost when the instance is replaced**. Plan for that before applying — this is the sharpest edge in the task.
- **No NAT gateway, no new EIP.** ~$32/mo and ~$3.60/mo respectively; the two existing public IPv4s are already ~24% of the bill (T-010).
- **No SSH.** Shell access stays SSM Session Manager. Do not add port 22 or a key pair to debug the container.

## Acceptance criteria

- [ ] `terraform fmt -check -recursive` clean, `terraform validate` succeeds, `terraform test` passes **offline** (mocks extended, assertions added).
- [ ] Applied for real, and verified against the live account: the BFF container is running, a public read route returns 200 through the **CloudFront domain** (not the origin directly), and `/api/*` still reaches Java so the live admin is unaffected.
- [ ] The domain service, MySQL and the admin are all still working after the apply — explicitly re-checked, given the instance replacement.
- [ ] MySQL data survived the replacement, or its loss was a recorded, accepted decision made **before** the apply.
- [ ] `compute.tf:1` and `README.md:14` describe what actually runs.
- [ ] **`/metrics` and `/health` are excluded from the `spa_router` CloudFront Function** (`functions/spa-router.js`) so they return 404 at the edge. Added 2026-08-13 from T-013's review: the function rewrites every extensionless URI to `/index.html`, so without this both paths answer **200 with the public SPA shell**. No metrics leak — nothing routes them to the BFF — but a monitoring probe aimed at the CloudFront domain reads that 200 as "healthy". Verify with a real request against the distribution, not by reading the Terraform.
- [ ] No new EIP, no NAT gateway, no port-22 ingress, no secret in a committed file.

## Definition of done

PR open against `master` from `feat/deploy-bff-node`, gates green, applied and verified, merged. Unblocks T-203, T-403 and the meta doc close-out (T-015).

## dev-loop notes

- **Developer:** `infrastructure-engineer` (adapter §2 — `cv-infra` Terraform/AWS). **Reviewers:** `/code-review` + `infrastructure-engineer` specialist lens + `quality-assurance`, plus `/security-review` (forced, see below). This is the `high`-risk reviewer set from adapter §7.
- **`security_review: true`, forced by adapter §5**, on three independent paths: security-group ingress, published container ports, and CORS config. Also touches auth env wiring.
- **`risk: high` is deliberate.** Adapter §7: *"a high-risk infra task with a real apply and stage-4 verification against AWS is the expensive shape — budget for the full ceiling and do not start one on a `SOFT` reading."* Probe the budget before starting, and do not run this in a wave with other tasks.
- **H2 must gate the apply, not just the merge.** The instance replacement is destructive to the self-hosted MySQL volume; the human gate is the point where that is accepted or a backup is taken first. T-001 (mysqldump→S3) is the mitigation and is still `todo` — consider doing it first, or take a one-off dump by hand and say so in the checkpoint.
- **`depends_on` includes T-001 to encode that mitigation** (added 2026-08-13). Only **T-001 §1 (backup)** gates this task — §2 (dev/prod parity) and §3 (docs drift) do not, so a split T-001 satisfies this dependency as soon as the backup PR merges. The alternative discharge is a hand-taken `mysqldump` verified restorable and recorded in this task's checkpoint; if you take it, note here that the dependency was satisfied that way rather than silently editing `depends_on` back. Without one of the two, do not apply — the board's sequential gating was the only thing standing between this task and an unbacked-up destroy.
- Gates (adapter §3): `terraform fmt -check -recursive` · `terraform validate` · `terraform test`, from `cv-infra/`. No CI system — the gates are the local commands.
- `terraform apply` stays in `ask` in `settings.local.json` **on purpose** — do not allowlist it to speed this up.
