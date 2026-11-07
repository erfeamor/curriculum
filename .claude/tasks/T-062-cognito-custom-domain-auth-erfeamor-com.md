---
id: T-062
title: "Cognito custom domain auth.erfeamor.com"
repo: cv-infra
status: done
owner: claude
branch: feat/cognito-custom-domain
pr: cv-infra#51
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

- [x] The BFF gets its service token from `auth.erfeamor.com`, and the public CV still returns 200.
- [x] The hosted UI answers at `https://auth.erfeamor.com/login?...`.

## DONE 2026-11-07

- cv-infra#51: `aws_cognito_user_pool_domain.custom` (`auth.erfeamor.com`, validated us-east-1 certificate, `managed_login_version = 1`) beside the prefix domain; `auth_alias` A/AAAA to Cognito's distribution; `bff/token-url` and the `cognito_hosted_ui_domain` output use the new name.
- Review: code-review (7 findings: 4 fixed, the main one being that `bff/token-url` now waits for the alias record; 1 rejected: the output now names the full hostname, no consumer; 2 test hardenings) and security-review (no findings). check-static check 26, 9 mutants red.
- Apply (by the human): 3 added, 1 changed, 0 destroyed, no host replacement; plan afterwards: no changes.
- Live: `https://auth.erfeamor.com/login?...` 200 (and the prefix domain 200); the token endpoint 400 without credentials; `cv-redeploy-bff-node` Success; `/bff/api/v1/people/1/cv` 200, `/api/v1/people/1` 401 without a token, `react.erfeamor.com` 200; no token errors in the BFF log.
- T-306 can now move the admin build to `auth.erfeamor.com` and drop the prefix domain.
