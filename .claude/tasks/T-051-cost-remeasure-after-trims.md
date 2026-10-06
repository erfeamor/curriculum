---
id: T-051
title: "Re-measure the AWS run rate after this week's trims (not before Friday 2026-10-09) and refresh the cost model"
repo: cv-project (meta)
status: todo
owner:
branch: docs/cost-remeasure
pr:
depends_on: []
risk: low
security_review: false
due: 2026-10-16
---

> **Not before Friday 2026-10-09.** The post-trim stack (no CI-host EIP since T-034, the app host on Graviton since T-035 on 2026-10-05, the BFF + Cognito machine tokens since T-043) needs a few full days of usage in Cost Explorer before the daily rate means anything.

## Why

Filed by the 2026-10-06 board review. Every cost figure on the board and in both CLAUDE.md files is the **2026-09-28** measurement (~$0.69/day ≈ $21/month), taken before: the CI-host EIP release (−$3.64/month), Graviton (−$1.75/month), plus small new lines (Cognito M2M tokens, the BFF's own ECR repo, multi-arch images, the hosted zone). The real number is probably lower, and the runway (credits $120.75 on 2026-10-01) longer.

## Scope

- Read Cost Explorer (`UnblendedCost`, `RECORD_TYPE=Usage`, daily, the full days since 2026-10-06) per service, and `aws freetier get-account-plan-state` for the credits.
- Update the meta repo's figures: CLAUDE.md "AWS cost" bullet, [T-012](T-012-aws-endgame-decision.md)'s runway note, [T-020](T-020-cost-model-correction.md)'s model (as a dated addendum, not a rewrite), and the TASKS.md lane's human note.
- The cv-infra half (its CLAUDE.md cost table) is [T-053](T-053-cv-infra-cost-table-refresh.md), using these numbers.
- Check the budget alarms still fit (the `gross-usage` $30/month limit, the `credit-runway` $160 against the $200 grant).

## Acceptance criteria

- [ ] The measured daily rate (and its per-service breakdown) recorded with its date range.
- [ ] The credits and runway re-derived; the meta docs updated.
- [ ] Any anomaly (e.g. a `CPUCredits` line on the Graviton host) noted or filed.
