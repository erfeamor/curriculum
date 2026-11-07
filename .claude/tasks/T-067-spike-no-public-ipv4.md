---
id: T-067
title: "Spike: run the app host with no public IPv4 (CloudFront VPC origin + IPv6 egress)"
repo: cv-infra
status: todo
owner: 
branch: spike/no-public-ipv4
pr:
depends_on: [T-061]
risk: normal
security_review: true
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

The EIP costs $3.60/month. A CloudFront VPC origin plus IPv6-only egress (a free egress-only internet gateway, no NAT) could remove it. This spike is go/no-go only and changes nothing in production.

## Scope

- **First, pin production's subnet:** add `filter { name = "default-for-az", values = ["true"] }` to `data.aws_subnets.domain_service` (`network.tf:23-35`). Otherwise a new subnet in eu-west-3a can capture the host on the next apply.
- **Then test a throwaway Spot `t4g.nano`** in a new private dual-stack subnet with no public IPv4. Check each item:
  - **CloudFront VPC origin:** can it be created in eu-west-3, and does it reach :8080 and :3000?
  - **ECR:** dual-stack pulls (the hostname differs)
  - **SSM:** Run Command and Session Manager with `UseDualStackEndpoint`
  - **CloudWatch Logs:** the awslogs driver on the dual-stack endpoint
  - **S3:** dual-stack access
  - **Cognito:** the token endpoint on `auth.erfeamor.com` and JWKS on `cognito-idp`
  - **OS packages:** `dnf`
  - **Docker Hub:** the mysql and flyway images, or mirror them into ECR
  - **GitHub has no IPv6:** `cv-redeploy migrate` clones github.com (`provision.sh:79-82`), so the migration SQL would need another path (S3, or an image built by cv-database)
- Record each result. **Go** only if every item works without NAT or a paid endpoint.

## Acceptance criteria

- [ ] A written go/no-go with evidence for each item; the throwaway resources are destroyed.
