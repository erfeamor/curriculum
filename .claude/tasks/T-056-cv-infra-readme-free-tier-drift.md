---
id: T-056
title: "cv-infra README still says the stack is 'kept within the AWS Free Tier' and counts 'six' other repos"
repo: cv-infra
status: done
owner: tech-product-owner
branch: docs/readme-paid-plan
pr: https://github.com/erfeamor/cv-infra/pull/45
depends_on: []
risk: trivial
security_review: false
---

## Done — 2026-10-08

A driver-written docs fix in [cv-infra#45](https://github.com/erfeamor/cv-infra/pull/45), done outside the dev loop at the human's request (a trivial docs task); the human's merge is the gate.

## Why

Found by [T-502](T-502-final-docs-architecture-diagram.md)'s per-repo README audit (2026-10-08). `cv-infra/README.md`:
- line 3 says "everything the other **six** repos deploy onto, **kept within the AWS Free Tier**". There are seven other repos, and the account has been on the Paid plan since 2026-09-29.
- line 20 says it uses the default VPC "to stay **Free Tier-eligible**". The real reason is cost: no NAT gateway (see `CLAUDE.md`'s cost model).

`cv-infra/CLAUDE.md` is already correct (T-051/T-053); the README is the only stale file.

## Acceptance criteria

- [x] The README describes the Paid plan, funded by credits first, and points to `CLAUDE.md`'s cost model instead of quoting figures. It counts the repos correctly and gives the default-VPC rationale as cost.
