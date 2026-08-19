---
id: T-020
title: "Correct the stale cost model, and stop the budget alarm from crying wolf every month"
repo: cv-project (meta) + cv-infra
status: in_progress
owner: tech-product-owner
branch: chore/cost-model-correction
pr:
depends_on: []
risk: normal
security_review: false
readings:
  date_read: 2026-08-19
  method: "AWS CLI, NOT the console — see the OBSOLETE_human_dependency note below. aws freetier get-account-plan-state + aws freetier list-account-activities + aws ce get-cost-and-usage (DAILY, RECORD_TYPE=Usage) + aws ec2 describe-instances."
  plan_type: FREE
  plan_status: ACTIVE
  remaining_credits: 111.08
  plan_expiration: 2027-01-12T15:38:35Z
  grant_total: 160          # $100 signup + 3 completed activities x $20
  activities_completed: [EC2 instance, Aurora/RDS database, AWS Budgets cost budget]
  activities_not_started: [Bedrock foundation model, Lambda web app]   # $40 still available, NEVER DONE despite T-010's ratified decision (a) on 2026-08-11
  measured_rate_now: 0.6837       # $/day, Aug 15/16/17 — three identical days, CI host stopped
  measured_rate_ci_running: 1.2261 # $/day, Aug 9-13 — confirms the board's $1.23 re-derivation exactly
  measured_rate_pre_resize: 0.92   # $/day, Aug 5-7 — confirms the old model was right for its time
  binding_constraint: WINDOW      # 2027-01-12, while the CI host stays stopped. CREDITS (~2026-11-17) if it runs 24/7.
  crossover_rate: 0.7608          # $/day from 2026-08-19: below it the window binds, above it the credits do
  OBSOLETE_human_dependency: "T-010 recorded that remaining balance, credit expiry and plan type are console-only and that 'no AWS API exposes them'. TRUE WHEN WRITTEN, FALSE NOW: aws freetier get-account-plan-state returns all three, and list-account-activities returns the activity status this task's §2 needed. Both post-date T-010. §1's blocking human dependency therefore did not need a human at all — the task was parked on a constraint that had expired. Recorded because the failure class is this project's recurring one: an assumption held long after it stopped being true."
---

> ## Readings taken 2026-08-19 — and what they overturned
>
> **§1 and §2 are done, and neither needed a human.** The full numbers are in the `readings:` frontmatter above. Three things came out of it that the task did not anticipate:
>
> **1. The CI host has been stopped since 2026-08-14 08:12 GMT** (`StateTransitionReason: User initiated`). Nothing on the board records this, and it invalidates the premise of [T-019](T-019-ci-host-on-demand.md) (*"runs 24/7 and is the single largest line on the AWS bill"*) and of this task's own §1. Measured daily gross usage, which tells the story cleanly:
>
> | Dates | $/day | State |
> |---|---|---|
> | Aug 5–7 | 0.92 | pre-resize — **the old model was accurate for its time** |
> | Aug 9–13 | 1.226 | post-resize, CI host up — **confirms the board's $1.23 re-derivation** |
> | Aug 15–17 | **0.684** | CI host stopped — current steady state, three identical days |
>
> (Aug 18 reads $0.39: Cost Explorer's lag on the most recent day, not a fourth data point.)
>
> **2. The binding constraint has flipped back to the window — conditionally.** From $111.08 on 2026-08-19, the crossover is **$0.761/day**; below it the window binds, above it the credits do.
>
> | Scenario | Rate | Credits exhaust | Binds |
> |---|---|---|---|
> | CI host stopped except during builds | $0.684/d ≈ $20.81/mo | ~2027-01-28 | **WINDOW** (2027-01-12) |
> | CI host running 24/7 | $1.226/d ≈ $37.32/mo | ~2026-11-17 | **CREDITS**, by ~8 weeks |
> | Stopped **+ the two $20 activities** | $0.684/d | ~2027-03-27 | WINDOW, comfortably |
>
> The board's 2026-08-14 re-derivation was arithmetically correct and is superseded by an operational change nobody wrote down. **This does not vindicate the original model** — it was wrong then and right now for unrelated reasons.
>
> **3. §3's premise about the alarm is no longer true.** The `$30` monthly budget is not structurally exceeded at the current rate: August still lands ~$34.68 (116%) because of its first half, but September projects to **$20.51 (68%)**. "Fires every month forever" holds only if the CI host returns to 24/7. See §4 below, which now has a different question to answer.
>
> **The catch, and it is not a cost one.** Jenkins and Drone are on the stopped box. T-102, T-103 and T-104 all carry *"Jenkins CI green"* in their definition of done, so **the M2 backend wave cannot close while it is stopped.** The cost model and the milestone schedule are now the same decision — exactly what T-019 predicted.
>
> **Ratified 2026-08-19 by the account owner: build [T-019](T-019-ci-host-on-demand.md)'s start-on-push automation.** That keeps the box off between builds (preserving the rate above) while removing the need for anyone to remember, and it resolves the M2/CI conflict without paying for an idle host. Recorded here because T-019's H1 was explicitly told to read this task's numbers first.

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

**1. ~~Read the real balance — this is blocking and cannot be automated.~~ DONE 2026-08-19, and it was never blocking.** ~~Remaining credit balance, each credit's expiry, and the plan type (Free vs Paid) come from the AWS console, Billing → Credits. **No AWS API or CLI exposes them**~~ — `aws freetier get-account-plan-state` returns the plan type, the remaining credits and the expiration date in one call. It post-dates T-010, whose `human_dependency` this section inherited without re-testing. Numbers and date read are in the `readings:` frontmatter.

**2. ~~Confirm whether the two $20 credit-earning activities were completed.~~ DONE — they were not.** `aws freetier list-account-activities` reports both `NOT_STARTED`: *"Use a foundation model in the Amazon Bedrock playground"* and *"Create a web app using AWS Lambda"*. T-010 ratified doing them on 2026-08-11 and nobody did. The grant is therefore **$160**, not $200, and the top row of the table above is the live one. **They are now optional rather than urgent** — the window binds before the credits do, so $40 more credits buy nothing while the CI host stays off. Worth doing only if the CI host goes back to 24/7, or for the Bedrock/Lambda experience itself.

**3. Correct the model where it is written down — in all *three* places.** `cv-infra/CLAUDE.md`'s cost section, T-010's runway figures, and **the meta `CLAUDE.md`** (added 2026-08-17), whose Conventions section states *"~$28/mo, net invoice $0"* — the same stale figure, in the file every agent loads on every session, and it was outside this task's scope until now. Give each a **date read** and the instance sizes it assumes, so the next resize makes the staleness visible instead of silent.

**4. Decide what the budget alarm should do** — retune, split into spend-vs-depletion, or accept and document the monthly fire. Not a bump; cv-infra#14's reasoning stands and must be addressed rather than reverted. **The question changed on 2026-08-19** (see the readings above): the `$30` monthly limit is *not* structurally exceeded at the current $20.81/month, so the "cries wolf every month forever" problem this task was filed for has evaporated on its own. What remains is narrower and worth one deliberate answer: August will breach once (~$34.68, 116%) on the strength of its first half, and the limit is now sized for a run rate that only returns if the CI host does. **Recommendation: change nothing, and record why** — a $30 limit against a $20.81 rate is a working deviation alarm that will fire precisely when the CI host is left running, which is now the single behaviour worth being told about. Retuning it down to hug the current rate would trade that signal for noise.

**5. Re-check T-012's re-dated deadline** against the real balance. **Done 2026-08-19 — and deliberately left at `due: 2026-11-01`.** The measured rate puts credit exhaustion at ~2027-01-28, *after* the window, which would justify relaxing the date. It is **not** relaxed, because the low rate rests on the CI host being stopped, [T-019](T-019-ci-host-on-demand.md)'s automation is not built yet, and a single forgotten `start-instances` restores the ~2026-11-17 credit cliff — a date the loosened deadline would then sit after. Revisit once T-019 is applied and verified; until then the conservative date costs nothing and the optimistic one is a bet on an unautomated habit.

## Acceptance criteria

- [x] Real credit balance, credit expiry dates and plan type recorded here with the date read. *(2026-08-19, `readings:` frontmatter.)*
- [x] Whether the two $20 activities landed, recorded with the resulting grant total. *(They did not; grant is $160.)*
- [ ] `cv-infra/CLAUDE.md`, the **meta `CLAUDE.md`**, and T-010 all state the real rate, with a date and the instance sizes assumed. Grep for the old figures (`0.92`, `$28`) rather than trusting this list — it has already been wrong once by omission.
- [ ] T-012's `due` verified against the real balance.
- [ ] A budget-alarm decision that does **not** reproduce the cv-infra#14 trap, with its reasoning written down.
- [ ] If the alarm changes: `terraform fmt -check -recursive`, `terraform validate`, `terraform test` pass, with assertions updated for any changed budget resource.

## Definition of done

PR open against `master` from `chore/cost-model-correction`, the console numbers recorded here, the model corrected in both places, and the alarm decision written down rather than deferred.

### Split as the notes below anticipated — what is done and what is left

**Meta half — done 2026-08-19** (this PR): §1 and §2 read and recorded, §4's recommendation and §5's re-check written down, the meta `CLAUDE.md` corrected, T-010's superseded figures and obsolete `human_dependency` corrected, T-019's H1 ratified and its falsified premise fixed, the board's cost block replaced with the measured model.

**cv-infra half — still open**, and it is why this task is `in_progress` rather than `done`:

- [ ] `cv-infra/CLAUDE.md` — the cost-model bullet (*"~$0.92/day ≈ $28/month"*) and the review-guidance line that judges cost drift against *"~$28/mo today"*. Both need the measured rate, the date read, and the instance-state assumption (CI host stopped except during builds), so the next resize makes staleness visible instead of silent.
- [ ] §4's "change nothing" recommendation either accepted and recorded in `budgets.tf`'s comments, or overridden — with `terraform fmt`/`validate`/`test` if any budget resource actually changes. It should not need to.

That is a `cv-infra` PR on its own branch, per the one-repo rule. Nothing in it blocks [T-019](T-019-ci-host-on-demand.md), which is now the higher-value work on that repo.

## dev-loop notes

- **Two repos.** Board rule: every task leaving stage 0 targets exactly one repo — so if §4 changes Terraform, **split it** into a meta-repo docs task and a cv-infra alarm task at refinement. The meta half is `trivial`; the cv-infra half is `normal` and carries the gates.
- **Developer:** `tech-product-owner` for the docs/model half, `infrastructure-engineer` if the budget resource changes.
- ~~**The human dependency in §1 is unavoidable** — do not let the loop "verify" the balance from the CLI. It cannot.~~ **Wrong as of 2026-08-19: it can, and it did.** `aws freetier get-account-plan-state` and `list-account-activities` cover §1 and §2 completely. This instruction was inherited from T-010 (written 2026-08-09, when it was true) and would have kept the task parked indefinitely on a human step that no longer existed. **The lesson generalises: a recorded "this is impossible" ages like any other assumption** — re-test it before building process around it. T-010's `human_dependency` has been corrected in place.
- **Interacts with [T-019](T-019-ci-host-on-demand.md)**: the corrected rate is what makes T-019's saving worth anything (see the board note of 2026-08-14). T-019's H1 should read this task's numbers, and this task should fold in T-019's measured saving if it lands first.
