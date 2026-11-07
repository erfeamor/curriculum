---
id: T-061
title: "erfeamor.com on CloudFront: ACM (us-east-1), aliases, IPv6, apex/www/react DNS, redirects, CORS via SSM"
repo: cv-infra
status: done
owner: tech-product-owner
branch: feat/erfeamor-com
pr: https://github.com/erfeamor/cv-infra/pull/48
depends_on: [T-060]
risk: high
security_review: true
---

## H1 — approved 2026-11-07

Scope as in the plan, with two simplifications ("money over complexity"):
- **No extra redirect function on `/api/*` and `/bff/*`.** Only the default behavior's function redirects `www`. Nobody calls `www`/`api`; they would just serve the same content.
- **The `react` CNAME moves to [T-410](T-410-react-erfeamor-com.md)**, because Vercel gives the exact target when the human adds the domain there. Until T-410 lands, `erfeamor.com/react` redirects to a name that doesn't resolve yet (today `/react` just shows the vanilla shell).

Also fixed at H1: the CORS value in SSM is `https://erfeamor.com,https://<cloudfront domain>`; the domain service appends its two localhost origins in the script. The redirect function is tested offline with node (`aws cloudfront test-function` needs the function deployed). **The apply replaces the app host once** (`/api` and `/bff` down ~3–5 min) and stays in "ask".

**Stage-0 facts (2026-11-07):** the zone has only NS, SOA and `ci.` records, so the apex is free; the domain auto-renews and expires 2027-09-29; no other distribution uses these names.

## ✅ DONE 2026-11-07 ([cv-infra#48](https://github.com/erfeamor/cv-infra/pull/48), `ab1939b`)

## Review and live evidence (2026-11-07)

**Reviews:** `/code-review` (10 findings) and the infrastructure lens (no blockers), plus `/security-review` (no findings ≥ 8). Taken and fixed test-first: `www` redirects for every path (before the probe exclusion), the Host match ignores case, query values are encoded without double-encoding and a valueless parameter stays valueless, a lone surrogate no longer throws, and `/react` is a **302** until T-410 gives it a target. A precondition ties the fixed Route 53 zone to `var.public_domain`. Not taken: the admin's redirect URI is built from `window.location.origin` at runtime, so it follows the page host (this PR registers the apex callback for exactly that); the data volume is a separate EBS volume that survives the host replacement; `check-static`'s text greps stay in the file's existing style.

**A bug only the real plan found:** the zone precondition failed against the real account, because the real `aws_route53_zone` data source returns the name without a trailing dot while the mock had one. Fixed with `trimsuffix`, and the mock now matches reality.

**Apply (12:06–12:11Z):** a backup first (`cv-20261107T120407Z.sql.gz`), then the saved plan: 13 added, 6 changed, 3 destroyed; the host is now `i-009de3a4d696f6213` and the old one is terminated. The BFF answered 200 about 8 minutes after the apply began (`/api` and `/bff` were down for that long). A plan afterwards: **no changes**.

**Live checks:**
- the apex `/`, `/admin/`, an admin deep link and `/bff/api/v1/people/1/cv` return 200, and `/api/v1/people/1` returns 401;
- `www` returns 301 to the apex for `/`, a path with query, `/health` and an uppercase Host, and `%20` / `%26` come through unchanged;
- `/react` and `/react/x` return a 302 to `https://react.erfeamor.com`;
- the certificate covers `erfeamor.com`, `www` and `auth`, and expires 2027-05-24 (ACM renews it);
- A and AAAA records answer for the apex;
- `dvdlxl0zqepqi.cloudfront.net` still serves a valid `*.cloudfront.net` certificate (200), so other repos' smoke tests keep working;
- CORS: the apex origin is allowed, an unknown origin gets no header;
- SSM is online on the new host, and its logs are flowing.

**H2 (human):** logged in at `https://erfeamor.com/admin/` and saved a change: it works.

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

- [x] `https://erfeamor.com/`, `/admin/`, `/bff/api/v1/people/1/cv` (200) and `/api/v1/people/1` (401) are served with a valid certificate.
- [x] `www` and `/react` return 301; `dig AAAA erfeamor.com` answers.
- [x] CORS origins come from SSM, and a `cv-redeploy` picks up a change.
