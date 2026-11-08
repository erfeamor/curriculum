---
id: T-068
title: "App host behind a CloudFront VPC origin; release the EIP"
repo: cv-infra
status: done
owner: claude
branch: feat/vpc-origin-no-eip
pr: https://github.com/erfeamor/cv-infra/pull/55
depends_on: [T-067, T-070, T-071]
risk: high
security_review: true
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

Only if T-067 says go. Saves $3.60/month. As a side benefit, the origins become reachable only through CloudFront, which closes T-025's documented accepted risk.

## Scope

- A private dual-stack subnet and `aws_cloudfront_vpc_origin` for :8080 and :3000. `frontend.tf:82-108` switches to the VPC origins.
- Security groups (`network.tf:77-83` and the BFF's): from the CloudFront prefix list to CloudFront's VPC-origin security group.
- Remove `aws_eip.domain_service` and its association (`compute.tf:44-51,136-139`), the output, and the test references.
- Move to the ECR dual-stack hostnames. Findings from T-067 (verdict GO) are in that task file: SSM agent dual-stack config, `awslogs-endpoint`, `AWS_USE_DUALSTACK_ENDPOINT=true`, IMDS IPv6. Docker Hub works over IPv6, so no mirrors.
- Default VPC: associate an IPv6 block, add a private dual-stack subnet in the volume's AZ and an egress-only IGW (decided at H1, 2026-11-08; no new VPC). The T-067 pin keeps the host off it by data source, so the host's `subnet_id` must be set to the new subnet deliberately.
- The migration SQL now comes from S3 (T-070/T-071); remove the git-clone fallback. Prerequisite: the tarball object exists before the apply.

## Acceptance criteria

- [x] `describe-addresses` is empty and the host has no public IP; direct `:8080` is unreachable.
- [x] A deploy, a migration and a backup all succeed through the new path.

## DONE (2026-11-08)

cv-infra#55 merged and applied: the EIP is released, the host has no public IPv4 and sits in the private dual-stack subnet, and CloudFront reaches it through two VPC origins. Three follow-ups were needed before the host was reproducible from code, all merged:

- **#56, containers need IPv6 egress too.** T-067 tested only the host. After the first apply the BFF could not reach Cognito (502) and the JVM hung on IPv4-first (504). Docker IPv6 + NAT66 in `daemon.json`, the `cv` network created with an IPv6 subnet, `accept_ra=2`, and `-Djava.net.preferIPv6Addresses=true` on the domain service. Hot-patched live first, then codified.
- **#57, CI host subnet.** `data.aws_subnets.default` also listed the new private subnet, so the plan moved the CI host into it (no IPv4 route). Added the `default-for-az` filter; check-static 30.
- **#58, VPC origins replaced create-before-destroy.** AWS answers 409 `CannotUpdateEntityWhileInUse` to an update or delete of an origin a distribution uses, and the provider plans a new instance ARN as an in-place update, so replacing the host (the #56 apply) failed half-applied. The origins now carry `replace_triggered_by` the instance, `create_before_destroy` and a name with the instance id; check-static 31. Recovered with `-replace` on both origins.

Live proof on the host built from master (`i-0f2999fd101493bcd`, no hand patches): `describe-addresses` empty, no public IP; `https://erfeamor.com/` 200, `/api/v1/people/1` 401, `/bff/api/v1/people/1/cv` 200; `daemon.json`, `accept_ra`, the `cv` IPv6 subnet and the JVM flag all came from the script; `cv-redeploy migrate` read the SQL from S3 (schema `cv` up to date, version 2); a manual backup uploaded a new dump.

Left for T-069: refresh the cost docs (the EIP's $0.12/day is gone from the run rate) and delete the old 8 GB MySQL volume `vol-092113db466c84bc1` after 2026-11-14.
