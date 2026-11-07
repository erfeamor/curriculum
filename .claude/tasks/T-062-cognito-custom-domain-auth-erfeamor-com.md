---
id: T-062
title: "Cognito custom domain auth.erfeamor.com"
repo: cv-infra
status: todo
owner: 
branch: feat/cognito-custom-domain
pr:
depends_on: [T-061]
risk: high
security_review: true
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

Replace the prefix domain `cv-project-dev.auth.eu-west-3.amazoncognito.com` with `auth.erfeamor.com` (free). A Cognito custom domain needs a us-east-1 certificate (from T-061) and a parent domain that resolves (the apex, also from T-061).

## Scope

- `aws_cognito_user_pool_domain` with `domain = "auth.erfeamor.com"`, `certificate_arn` and **`managed_login_version = 1`**, matching today's domain. Version 2 needs a branding resource, or the login page breaks.
- A Route 53 alias to `cloudfront_distribution` / `cloudfront_distribution_zone_id`.
- Update the `cognito_hosted_ui_domain` output (`outputs.tf:35-37`).
- Point SSM `bff/service-token-url` (`ssm.tf:210-213`) at the new domain, then `cv-redeploy bff-node` (T-055's `cv_need` re-reads it).
- Keep the prefix domain until T-306 has moved the admin build.

## Acceptance criteria

- [ ] The BFF gets its service token from `auth.erfeamor.com`, and the public CV still returns 200.
- [ ] The hosted UI answers at `https://auth.erfeamor.com/login?...`.
