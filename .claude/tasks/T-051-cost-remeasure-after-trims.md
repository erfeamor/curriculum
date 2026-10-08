---
id: T-051
title: "Re-measure the AWS run rate after this week's trims (not before Friday 2026-10-09) and refresh the cost model"
repo: cv-project (meta)
status: done
owner: tech-product-owner
branch: docs/cost-remeasure
pr: https://github.com/erfeamor/curriculum/pull/120
depends_on: []
risk: low
security_review: false
due: 2026-10-16
checkpoint:
  stage: done   # measured 2026-10-08 outside the dev loop at the human's request (usage gap): driver-only, no spawns, no review pass
  repo: cv-project (meta)
  branch: docs/cost-remeasure
  worktree: none
  commit:
  pr:
  developer: tech-product-owner   # driver measures (Cost Explorer) and edits docs; no spawn
  reviewers: [code-review]
  risk: low
  security_review: false
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a
  updated: 2026-10-08T15:00:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 0
    spawns: 0
    status: stop   # human-reported /usage over 75%: H1 only, resume next window
    checked: 2026-10-08T15:00:00+02:00
---

## H1 — decided by the human, 2026-10-08

1. **Start early: the "not before Friday" gate is lifted.** Since the trims, nothing has changed the cost structure. T-049, T-050, T-054 and T-055 were IAM, an ECR lifecycle change, kilobytes of CloudWatch logs and two same-size host replacements. So only sample size is lost.
2. **Method:**
   - Use every full post-Graviton day available when this runs: 10-06 onward. Flag a day Cost Explorer may still be finalizing.
   - Split the daily rate into **fixed** (app host, EBS, public IPv4, Route 53, Cognito, ECR, CloudWatch) and **variable** (CI host instance-hours and its EBS).
   - The CI share in this window is a **busy-week sample** (many dev-loop builds 10-06 to 10-08). Derive the runway from fixed plus a *typical* CI share taken from the September history, not from the busy days.
   - Expect about 5–10 Cost Explorer calls (~$0.01 each).
3. **Docs: meta only, as scoped** (CLAUDE.md cost bullet, T-012 runway note, dated T-020 addendum, TASKS.md lane note). [T-053](T-053-cv-infra-cost-table-refresh.md) follows as its own small PR.
4. **Budget:** `/usage` over 75%: **stopped after H1.** Resume with `/dev-loop T-051` in the next window. The measurement starts there, and later is fine: more full days only help.

> ~~**Not before Friday 2026-10-09.**~~ **Lifted at H1, 2026-10-08** (see below). The post-trim stack (no CI-host EIP since T-034, the app host on Graviton since T-035 on 2026-10-05, the BFF + Cognito machine tokens since T-043) needs a few full days of usage in Cost Explorer before the daily rate means anything.

## Result — 2026-10-08

**~$0.51/day ≈ $15.5/month** (fixed ~$0.47 + CI ~$0.04); **$116.15** of credits, enough until about late May 2027. Full table and method in the dated addenda on [T-012](T-012-aws-endgame-decision.md) and [T-020](T-020-cost-model-correction.md). Done outside the dev loop at the human's request (usage over 75%): the driver ran 2 API calls (Cost Explorer + `freetier`), with no spawn and no `/code-review`; the human's merge is the gate. No anomaly: no `CPUCredits` line on the Graviton host.

## Why

Filed by the 2026-10-06 board review. Every cost figure on the board and in both CLAUDE.md files is the **2026-09-28** measurement (~$0.69/day ≈ $21/month), taken before: the CI-host EIP release (−$3.64/month), Graviton (−$1.75/month), plus small new lines (Cognito M2M tokens, the BFF's own ECR repo, multi-arch images, the hosted zone). The real number is probably lower, and the runway (credits $120.75 on 2026-10-01) longer.

## Scope

- Read Cost Explorer (`UnblendedCost`, `RECORD_TYPE=Usage`, daily, the full days since 2026-10-06) per service, and `aws freetier get-account-plan-state` for the credits.
- Update the meta repo's figures: CLAUDE.md "AWS cost" bullet, [T-012](T-012-aws-endgame-decision.md)'s runway note, [T-020](T-020-cost-model-correction.md)'s model (as a dated addendum, not a rewrite), and the TASKS.md lane's human note.
- The cv-infra half (its CLAUDE.md cost table) is [T-053](T-053-cv-infra-cost-table-refresh.md), using these numbers.
- Check the budget alarms still fit (the `gross-usage` $30/month limit, the `credit-runway` $160 against the $200 grant).

## Acceptance criteria

- [x] The measured daily rate (and its per-service breakdown) recorded with its date range.
- [x] The credits and runway re-derived; the meta docs updated.
- [x] Any anomaly (e.g. a `CPUCredits` line on the Graviton host) noted or filed.
