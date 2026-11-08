---
id: T-068
title: "App host behind a CloudFront VPC origin; release the EIP"
repo: cv-infra
status: todo
owner: 
branch: feat/vpc-origin-no-eip
pr:
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

- [ ] `describe-addresses` is empty and the host has no public IP; direct `:8080` is unreachable.
- [ ] A deploy, a migration and a backup all succeed through the new path.
