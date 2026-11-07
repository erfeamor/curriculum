---
id: T-068
title: "App host behind a CloudFront VPC origin; release the EIP"
repo: cv-infra
status: todo
owner: 
branch: feat/vpc-origin-no-eip
pr:
depends_on: [T-067]
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
- Move to the ECR dual-stack hostnames, the mysql and flyway mirrors, and the migration-SQL path from the spike.

## Acceptance criteria

- [ ] `describe-addresses` is empty and the host has no public IP; direct `:8080` is unreachable.
- [ ] A deploy, a migration and a backup all succeed through the new path.
