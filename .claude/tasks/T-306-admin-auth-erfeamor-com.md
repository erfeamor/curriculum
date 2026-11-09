---
id: T-306
title: "Admin build on auth.erfeamor.com; drop the old callbacks and the prefix domain"
repo: cv-admin-react
status: done
owner: infrastructure-engineer
branch: feat/admin-auth-domain
pr: https://github.com/erfeamor/cv-admin-react/pull/19   # companion: https://github.com/erfeamor/cv-infra/pull/61
depends_on: [T-062, T-305]
risk: normal
security_review: false
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

Final step of the Cognito move.

## Scope

- `VITE_COGNITO_HOSTED_UI_DOMAIN=auth.erfeamor.com` in the workflow and `.env.example`.
- Then, in cv-infra, as a small companion PR: remove the cloudfront.net callback and logout URLs and the prefix `aws_cognito_user_pool_domain`.

## Acceptance criteria

- [x] A human logs in through `auth.erfeamor.com`; the prefix domain is gone.

## DONE (2026-11-09)

[cv-admin-react#19](https://github.com/erfeamor/cv-admin-react/pull/19) (admin build on `auth.erfeamor.com`) merged and deployed first; the user logged in and saved through the new domain. Then [cv-infra#61](https://github.com/erfeamor/cv-infra/pull/61) (stacked on #60, rebased onto master) merged and applied: the `admin_react` client keeps only the localhost and `https://erfeamor.com/admin/` callback and logout URLs, the prefix domain `aws_cognito_user_pool_domain.cv` is destroyed, and the SSM CORS parameter is exactly `https://erfeamor.com`. check-static 25 and 26 and the `t061`/`t062` tests now guard against the cloudfront.net URL in callbacks, logout URLs or CORS and against a second Cognito domain (each mutation-checked). `cv-redeploy` of domain-service and bff-node re-read the CORS value: a preflight from the apex is allowed, one from the old cloudfront.net origin gets 403.

Left alone on purpose: cloudfront.net strings in test fixtures and docs (cv-public-react `CLAUDE.md:116` and `container.test.ts:3`, cv-bff-node `.env.example`), and the cloudfront.net hostname itself still serves the site.
