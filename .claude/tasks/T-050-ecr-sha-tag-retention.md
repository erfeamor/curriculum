---
id: T-050
title: "cv-infra: ECR keeps every `:<sha>` deploy image forever — add a retention rule for sha tags"
repo: cv-infra
status: todo
owner:
branch: fix/ecr-sha-tag-retention
pr:
depends_on: [T-112, T-203]
risk: low
security_review: false
---

## Why

Found at T-112/T-203's review (non-blocking), filed by the 2026-10-06 board review. Every automated deploy pushes `:latest` **and** an immutable `:<sha>` multi-arch image (~100 MB). T-035's lifecycle rule expires only **untagged** images, so sha-tagged ones accumulate without bound (ECR storage $0.10/GB-month: cents now, unbounded later).

## Scope

- A lifecycle rule on both repos that keeps the **last N (e.g. 10) sha-tagged images** and never touches `:latest`. ECR rules match `tagPatternList`; sha tags are 40 hex chars, so use a pattern that can't match `latest`. Keep T-035's untagged rule.
- `terraform test` assertion; the runbook's rollback note says only the last N shas are kept.

## Acceptance criteria

- [ ] Applied; `aws ecr get-lifecycle-policy-preview` shows only old sha tags would expire, never `:latest`.
