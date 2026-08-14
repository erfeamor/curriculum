---
id: T-020
title: "Correct the stale cost model, and stop the budget alarm from crying wolf every month"
repo: cv-project (meta) + cv-infra
status: todo
owner:
branch: chore/cost-model-correction
pr:
depends_on: []
risk: normal
security_review: false
---

## Why this exists

**No task owned this.** T-019 explicitly disclaims it (*"Correcting those is not this task"*, its dev-loop notes), T-010 is `done`, and T-012 consumes the numbers rather than maintaining them. So the project's cost model has been known-wrong since 2026-08-08 with nobody responsible for fixing it — which is the same shape as the T-013 deployment gap and T-010's own finding: **a documented assumption nobody re-checked.**

Two figures are wrong in two places, and one alarm is about to become noise.

### 1. The rate is understated by a third

`cv-infra/CLAUDE.md` and T-010's runway both encode **~$0.92/day ≈ $28/month**. The 2026-08-08 `t3.micro`→`t3.small` resize of the CI host (T-002, deliberate, for Maven headroom) took the real rate to **~$1.23/day ≈ $37.30/month** — verified against the August cost export and `describe-instances`.

### 2. Every date derived from that rate is late

Recorded on the board 2026-08-14. From T-010's console read ($120.66 remaining on 2026-08-11):

| Grant | modelled at $0.92/day | re-derived at $1.23/day |
|---|---|---|
| $160 (current) | 2026-12-20 | **~2026-11-17** |
| $200 (after the two $20 activities) | 2027-01-12 | **~2026-12-19** |

Under the old model the $200 case was safely window-bound; under the real rate **credits bind in both cases**. T-012 has been re-dated on that basis, but from *derived* numbers — see §1 of the scope.

### 3. The budget alarm is about to fire every month, forever

The `$30` monthly limit is structurally exceeded at ~124% of the real run rate, so its 100/120% thresholds fire from September onward regardless of what happens. **An alarm that always fires stops being a signal** — and this is the same alarm T-010 found had been firing into a spam folder for months, whose December warning has exactly one job.

The obvious fix is the wrong one. [cv-infra#14](https://github.com/erfeamor/cv-infra/pull/14) deliberately refused to raise `budget_credit_grant_amount`, because at $200 the 100% threshold lands ~20 days *after* the account is paused — an alarm that stays green until it can no longer help. **Whatever is done here must not recreate that trap.** The monthly-spend budget and the credit-depletion budget are different instruments serving different questions; the fix may be to separate them rather than to retune one number.

## Scope

**1. Read the real balance — this is blocking and cannot be automated.** Remaining credit balance, each credit's expiry, and the plan type (Free vs Paid) come from the AWS console, Billing → Credits. **No AWS API or CLI exposes them** (established as T-010's `human_dependency`; no developer persona can satisfy it). Record the numbers and the date read, the way T-010 did. Everything below is provisional until this happens — including the dates already written into T-012.

**2. Confirm whether the two $20 credit-earning activities were completed.** T-010's ratified decision (a) was *"complete them now"* on 2026-08-11 (Lambda; foundation-model experimentation). Nothing on the board records whether they were, and it selects which row of the table above is live.

**3. Correct the model where it is written down:** `cv-infra/CLAUDE.md`'s cost section, and T-010's runway figures. Give each a **date read** and the instance sizes it assumes, so the next resize makes the staleness visible instead of silent.

**4. Decide what the budget alarm should do** — retune, split into spend-vs-depletion, or accept and document the monthly fire. Not a bump; cv-infra#14's reasoning stands and must be addressed rather than reverted.

**5. Re-check T-012's re-dated deadline** against the real balance and correct it again if the console disagrees.

## Acceptance criteria

- [ ] Real credit balance, credit expiry dates and plan type recorded here with the date read.
- [ ] Whether the two $20 activities landed, recorded with the resulting grant total.
- [ ] `cv-infra/CLAUDE.md` and T-010 state the real rate, with a date and the instance sizes assumed.
- [ ] T-012's `due` verified against the real balance.
- [ ] A budget-alarm decision that does **not** reproduce the cv-infra#14 trap, with its reasoning written down.
- [ ] If the alarm changes: `terraform fmt -check -recursive`, `terraform validate`, `terraform test` pass, with assertions updated for any changed budget resource.

## Definition of done

PR open against `master` from `chore/cost-model-correction`, the console numbers recorded here, the model corrected in both places, and the alarm decision written down rather than deferred.

## dev-loop notes

- **Two repos.** Board rule: every task leaving stage 0 targets exactly one repo — so if §4 changes Terraform, **split it** into a meta-repo docs task and a cv-infra alarm task at refinement. The meta half is `trivial`; the cv-infra half is `normal` and carries the gates.
- **Developer:** `tech-product-owner` for the docs/model half, `infrastructure-engineer` if the budget resource changes.
- **The human dependency in §1 is unavoidable** — do not let the loop "verify" the balance from the CLI. It cannot. T-010's checkpoint is the precedent for how to park and resume on it.
- **Interacts with [T-019](T-019-ci-host-on-demand.md)**: the corrected rate is what makes T-019's saving worth anything (see the board note of 2026-08-14). T-019's H1 should read this task's numbers, and this task should fold in T-019's measured saving if it lands first.
