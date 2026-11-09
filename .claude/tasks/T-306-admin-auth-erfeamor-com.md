---
id: T-306
title: "Admin build on auth.erfeamor.com; drop the old callbacks and the prefix domain"
repo: cv-admin-react
status: in_progress
owner: infrastructure-engineer
branch: feat/admin-auth-domain
pr:
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

- [ ] A human logs in through `auth.erfeamor.com`; the prefix domain is gone.
