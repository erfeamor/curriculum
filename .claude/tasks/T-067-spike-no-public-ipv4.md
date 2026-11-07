---
id: T-067
title: "Spike: run the app host with no public IPv4 (CloudFront VPC origin + IPv6 egress)"
repo: cv-infra
status: in_review
owner: claude
branch: spike/no-public-ipv4
pr: https://github.com/erfeamor/cv-infra/pull/53
depends_on: [T-061]
risk: normal
security_review: true
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

The EIP costs $3.60/month. A CloudFront VPC origin plus IPv6-only egress (a free egress-only internet gateway, no NAT) could remove it. This spike is go/no-go only and changes nothing in production.

## Scope

- **First, pin production's subnet:** add `filter { name = "default-for-az", values = ["true"] }` to `data.aws_subnets.domain_service` (`network.tf:23-35`). Otherwise a new subnet in eu-west-3a can capture the host on the next apply.
- **Then test a throwaway on-demand `t4g.nano`** (not Spot: eu-west-3a has scarce Spot capacity, see T-065) in a new private dual-stack subnet with no public IPv4. Check each item:
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

- [x] A written go/no-go with evidence for each item; the throwaway resources are destroyed.

## DONE (2026-11-08) — verdict: **GO**

Subnet pin merged as cv-infra#53 (`default-for-az` filter, plan test, real plan: no changes). Experiments ran with the AWS CLI in a scratch VPC `10.99.0.0/16` (Amazon IPv6 /56, IGW attached, egress-only IGW, one private /24+/64 subnet in eu-west-3a), outside Terraform state. On-demand `t4g.nano`, no public IPv4, the app host's instance profile. Everything was deleted afterwards (instances, distribution, both VPC origins, SG, subnet, gateways, VPC).

| Item | Result | How T-068 must do it |
|---|---|---|
| CloudFront VPC origin | **Works** in eu-west-3 (an EC2 instance ARN as target; ~10 min to deploy). A test distribution served `/` from :8080 and `/bff/*` from :3000 with `x-cache: Miss from cloudfront`. | One `aws_cloudfront_vpc_origin` per port (the port belongs to the origin). Instance SG allows 8080/3000 only from AWS's managed `CloudFront-VPCOrigins-Service-SG` (it appears in the VPC once a VPC origin exists). The VPC needs an attached IGW. |
| SSM Run Command | **Works only with** `{"Agent":{"UseDualStackEndpoint":true}}` in `/etc/amazon/ssm/amazon-ssm-agent.json`. Without it the instance never registered (the default endpoints are IPv4-only). | Write that file in user_data before the agent first starts, or restart the agent. |
| ECR | **Works** via `<account>.dkr-ecr.eu-west-3.on.aws`; `aws ecr get-login-password` with `AWS_USE_DUALSTACK_ENDPOINT=true`; pulled the bff image. The old hostname fails. | Registry hostname changes everywhere (deploy workflows keep pushing to the old one). |
| CloudWatch Logs (awslogs) | **Works only with** `--log-opt awslogs-endpoint=https://logs.eu-west-3.api.aws`; the default endpoint timed out. Event confirmed in the group. | Add the option to `cv_run_*`. |
| S3 | **Works** (dual-stack endpoint; requests reached S3 over IPv6, answers were IAM denials for actions the role lacks by design). | `AWS_USE_DUALSTACK_ENDPOINT=true` in the host environment. |
| Cognito | **Works**: `auth.erfeamor.com` and `cognito-idp.eu-west-3.amazonaws.com` answer over IPv6. | None. |
| SSM Parameter Store | **Works** with the dual-stack flag. | Same flag. |
| dnf | **Works** (AL2023 repos, `dnf install docker`). | None. |
| Docker Hub | **Works** over IPv6: pulled `mysql:8.4` and `flyway/flyway:13.7.0` (the image name production uses; `redgate/flyway` has no arm64). No ECR mirror needed. | None (anonymous pull limits apply per IPv6 /64, fine at this volume). |
| GitHub | **No IPv6, as expected** (`github.com` times out). `cv-redeploy migrate` clones it. | T-068 must ship the migration SQL differently: simplest is cv-database's migrate workflow publishing the `sql/` tree as an S3 object (or an ECR image) that the host fetches. |
| IMDS | Works over IPv6 with `HttpProtocolIpv6=enabled`. | Set it on the instance. |

No NAT, no paid endpoint. The private IPv4 inside the VPC is free; only a *public* IPv4 bills. Saves the EIP's $3.60/month.

**Open for T-068:** the apex distribution reaches origins through VPC origins, so the new subnet must be one the host's volume AZ matches (3a); the existing `ssm_*`, deploy workflows and `deploy.yml`'s smoke test need re-checking against the new registry hostname.
