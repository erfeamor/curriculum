---
id: T-158
title: "cv-database: apply new migrations to production automatically on master (GitHub Actions after Jenkins is green → SSM `cv-redeploy-migrate`)"
repo: cv-database
status: done
owner: tech-product-owner
branch: feat/ci-migrate-on-master
pr: https://github.com/erfeamor/cv-database/pull/8
depends_on: [T-049]
risk: normal
security_review: true   # CI config + AWS credentials — adapter §5
checkpoint:
  stage: done   # merged 0e7a566 (squash of cv-database#8), 2026-10-07 — its merge was the first live run: Jenkins green → SSM migrate Success, schema up to date; H2 accepted
  repo: cv-database
  branch: feat/ci-migrate-on-master
  worktree: none
  commit: 0e7a566
  pr: https://github.com/erfeamor/cv-database/pull/8
  developer: infrastructure-engineer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 2
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a
  updated: 2026-10-07T11:10:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 31429
    spawns: 1   # infrastructure-engineer (fresh), resumed once for the fix round
    status: ok   # human-reported /usage 40–75%: implement + review, checkpoint before the apply
    checked: 2026-10-06T23:45:00+02:00
---


## Live — 2026-10-07: the merge was the first run (cv-database#8 → 0e7a566, run 37596433369)

- `wait-for-jenkins` 08:50:15 → 08:53:03Z: `absent` while the doorbell woke the CI host, `pending` 08:52:40, **`success`** 08:53:00.
- `migrate` 08:53:06 → 08:53:32Z: OIDC into `cv-project-database-migrate` (the variable set at T-049's live stage), SSM `cv-redeploy-migrate` → **1 invocation, `Success` in 11 s**: "Successfully validated 2 migrations … Schema `cv` is up to date. No migration necessary." BFF aggregate 200.
- The ordering rule is in both repos: cv-database CLAUDE.md Rules item 2 (this PR) and cv-domain-service CLAUDE.md ([cv-domain-service#18](https://github.com/erfeamor/cv-domain-service/pull/18), b0a32e6; its merge redeployed an unchanged image).
- **Not yet exercised:** a real pending migration (the next schema change is the proof), and the failure path (`flyway repair` is manual by design).

## H1 — decided by the human, 2026-10-06 (T-049 + T-158 together)

1. **Trigger (T-158):** a push to `master` touching `sql/migrations/**` or the workflow file itself (so its own merge is the first live run), plus `workflow_dispatch` (still master-only: the OIDC trust pins `ref:refs/heads/master`). Docs- and seed-only pushes never touch production.
2. **Mode:** both implemented and reviewed in parallel against pinned names (document `cv-redeploy-migrate`, role `cv-project-database-migrate`, repo variable `AWS_DEPLOY_ROLE_ARN`, target `tag:Name=cv-project-domain-service`); then strictly serial: apply T-049 → set the variable on cv-database → merge T-049 → merge T-158.
3. **Ordering (schema first, then the domain change):** a documented rule in both repos' CLAUDE.md; no cross-repo guard.
4. **Budget:** `/usage` 40–75% → implement and review both, **checkpoint before the apply**.

## Implement + review — 2026-10-06 (cv-database `feat/ci-migrate-on-master`)

- Developer (fresh infrastructure-engineer, ~31k tokens): `.github/workflows/migrate.yml` (wait-for-jenkins → migrate via OIDC + SSM `cv-redeploy-migrate` on the tagged host, bounded poll, "exactly one target", BFF smoke). Both jobs start with a failing master-ref guard (not an `if:`, so a wrong-ref dispatch shows red, not skipped). `scripts/tests/test_migrate_workflow.py` (6 structural tests, red first: the file was missing). CLAUDE.md: the CI flow, the failure procedure, Rules item 2 rewritten as schema-first. Jenkinsfile Deploy note, README pointer.
- **Review round 1 (driver, code + security):** the workflow is accepted. Two fixes: a committed `.pyc`, and the failure note overstated safety (MySQL DDL isn't transactional; `flyway repair` is manual). **Round 2: clean** (f3e68f3).
- The cv-domain-service half of the ordering rule is a driver docs commit on `docs/schema-first-ordering` (4793d5f, local, not pushed yet).

## Why

Filed by the 2026-10-06 board review; see [T-049](T-049-ci-migrate-role-and-ssm-document.md) for the hazard: an automated domain deploy whose schema change hasn't reached production fails to start (`ddl-auto: validate`). Migrations are additive by convention (T-157), so **migrating first is always safe** for the running image.

## Scope (mirror T-112's `deploy.yml`)

- `.github/workflows/migrate.yml`, on a push to `master` only: a **`wait-for-jenkins`** job (the commit's newest `continuous-integration/jenkins/branch` status: success → go, red → stop, bounded) whose Jenkins gate already runs the Flyway migration against MySQL 8.4. Then a **`migrate`** job: OIDC → `vars.AWS_DEPLOY_ROLE_ARN` (T-049's role), `aws ssm send-command --document-name cv-redeploy-migrate --targets Key=tag:Name,Values=cv-project-domain-service`, a bounded `list-command-invocations` poll, print the output, fail unless `Success`. Timeouts on every job.
- **Ordering rule, documented** in cv-database and cv-domain-service CLAUDE.md: a schema change merges in cv-database **first** and its migrate run must be green before the domain change that needs it merges.
- Docs: the repo variable, the flow, and what to do if a migration fails (the domain service keeps running on the old schema; fix forward).

## Acceptance criteria

- [x] PRs never migrate; a master push migrates only after Jenkins is green.
- [x] Proven live with the next real migration, or with a no-op run (`cv-redeploy migrate` reports "up to date") on a docs-only master push.
- [x] The ordering rule is in both repos' CLAUDE.md.
