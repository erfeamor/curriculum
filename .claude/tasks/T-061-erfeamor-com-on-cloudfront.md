---
id: T-061
title: "erfeamor.com on CloudFront: ACM (us-east-1), aliases, IPv6, apex/www/react DNS, redirects, CORS via SSM"
repo: cv-infra
status: todo
owner: 
branch: feat/erfeamor-com
pr:
depends_on: [T-060]
risk: high
security_review: true
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

Serve the project on the domain the human owns (Route 53 zone `Z0608270B7WND031GVOW`, today only read as `data.aws_route53_zone.ci` for `ci.erfeamor.com`). The distribution currently has no `aliases` and uses `cloudfront_default_certificate` (`frontend.tf:185-187`).

## Scope

- **Certificate:** `provider "aws" { alias = "us_east_1" }` plus **one** `aws_acm_certificate` for `erfeamor.com`, `www.erfeamor.com` and `auth.erfeamor.com`. Including auth now means T-062 never has to replace an attached certificate. DNS validation records go in the zone, with an `aws_acm_certificate_validation`. Rename the zone data source to something neutral.
- **Distribution:** `aliases`; a `viewer_certificate` fed by the validation resource's `certificate_arn`, with `sni-only` and `TLSv1.2_2021`; `is_ipv6_enabled = true`.
- **DNS:** alias A and AAAA records for the apex and `www`, and a `react` CNAME to Vercel (target from the Vercel dashboard, for T-410).
- **Redirects:** `spa-router.js` sends `Host: www.erfeamor.com` to the apex and `/react` / `/react/*` to `https://react.erfeamor.com`. A small host-redirect viewer function on `/api/*` and `/bff/*` covers `www` there too. Build a test harness with `aws cloudfront test-function`; there is none today, only regex checks in `plan.tftest.hcl`.
- **Cognito:** `admin_react` callback and logout URLs (`auth.tf:27-34`) gain `https://erfeamor.com/admin/`. Keep the cloudfront.net URLs until T-306.
- **CORS moves to SSM:** a new parameter `app/cors-allowed-origins` read through `cv_need` in `cv_run_*` (pattern: `templates/domain-service-provision.sh:166-171`), replacing the values baked in at `:154,183`. Add it to `local.app_host_ssm_parameter_names`. This is the host replacement that makes every later origin change a plain `cv-redeploy`.
- **Tests:** `tests/plan.tftest.hcl` gets `mock_provider "aws" { alias = "us_east_1" }` plus assertions for aliases, certificate region and validation wiring. check-static covers the new parameter.

## Acceptance criteria

- [ ] `https://erfeamor.com/`, `/admin/`, `/bff/api/v1/people/1/cv` (200) and `/api/v1/people/1` (401) are served with a valid certificate.
- [ ] `www` and `/react` return 301; `dig AAAA erfeamor.com` answers.
- [ ] CORS origins come from SSM, and a `cv-redeploy` picks up a change.
