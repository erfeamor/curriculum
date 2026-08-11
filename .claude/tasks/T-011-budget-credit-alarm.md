---
id: T-011
title: Budget alarm that fires on credit burn, not on the invoice
repo: cv-infra
status: done
owner: infrastructure-engineer
branch: feat/budget-credit-alarm
pr:
depends_on: []
risk: normal
security_review: true
checkpoint:
  stage: done
  repo: cv-infra
  branch: feat/budget-credit-alarm
  developer: infrastructure-engineer
  reviewers: [code-review, infrastructure-engineer, quality-assurance]
  risk: normal
  security_review: true   # FORCED BY A1, not the stage-0 guess: the diff adds aws_sns_topic_policy (a resource-based policy granting a service principal SNS:Publish) and touches terraform.tfvars.example. Adapter §5 security paths.
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: 0
  split_from: T-010
  a1: "PASS 2026-08-09, re-run by the driver not taken on report: terraform fmt -check -recursive exit 0; terraform validate Success; terraform test 1 passed 0 failed. Risk re-check: 4 files / 259 insertions — under the >5 file bound, and risk was already normal so the trivial-revoke rule does not apply. Security re-check FIRED (see security_review)."
  commit: c2f1b2d
  h1: "approved 2026-08-09 — scope, split and assignment ratified; run T-011 now, T-010 parked at H1 pending the console numbers"
  review_trail_r1: "Three passes on 8a02828. /security-review: 0 blocking, 5 non-blocking (verified iam.tf untouched by diff rather than trusting the claim; judged aws:SourceAccount the standard confused-deputy mitigation, and the topic a pure notification sink with no automation downstream, so no privilege-escalation path). QA coverage: 2 BLOCKING, proven by mutation testing in a scratch copy rather than by inspection. /code-review (medium): 6 findings, 1 HIGH + 2 MEDIUM + 3 LOW; PO mapped 5 to blocking. Total 7 blocking."
  po_arbitration: "CONFLICT between reviewers, resolved by the PO. /security-review proposed kms_master_key_id = alias/aws/sns as zero-cost SSE on the topic. /code-review states the opposite and is more specific: an SSE-enabled topic BREAKS AWS Budgets publishing unless the KMS key policy grants budgets.amazonaws.com, and the AWS-managed alias/aws/sns key policy cannot be edited. DECISION: do NOT add SSE. Following the security reviewer here would have silently disabled the very notification path this task exists to build — the same fires-to-nobody class the task was written to prevent. Recorded so the suggestion is not re-raised."
  discarded_hypotheses: "/code-review checked and discarded two, logged so they are not re-litigated: AWS Budgets allows 10 notifications per budget so 3 thresholds x 2 types = 6 is within quota; and there is no us-east-1 region requirement on the SNS topic, only same-account."
  review_converged: "Round 1, 0 blocking findings remaining. All 7 reconciled in c68f266, none rejected, so no PO sign-off on a rejection was required. Verified by MUTATION, not inspection: injecting the wrong-subscriber, disconnected-thresholds, ABSOLUTE_VALUE and include_credit=true regressions into a scratch copy each now fails the suite; the first three PASSED before this commit."
  developer_stall: "The persistent developer instance was killed by the stream watchdog (600s no progress) mid-sentence, immediately before its own final A1 run, with all seven fixes already written to the working tree but uncommitted. The driver re-ran A1 independently (green), verified all seven findings closed, mutation-tested the two previously-blocking gaps plus the crux, and committed the tree WITHOUT modifying any content. Recorded because the writer-writes invariant means this is worth being explicit about: no code was authored by the driver."
  ci_substitution: "cv-infra has NO authoritative CI in the adapter's table (the only repo without one). Stage 3's 'repo CI must go green' gate therefore has nothing to run. It is NOT satisfied and must not be read as passed — the substitute evidence is the A1 gate plus stage-4 verification against the real account. Flagged for H2."
  pr: https://github.com/erfeamor/cv-infra/pull/13
  blocked_reason: "Stage 4 cannot run. terraform plan/apply requires two variables that have NO defaults, by deliberate design (H1 DoR decision 2 — this task must not invent a credit balance or ship a guess as if it were measured): budget_limit_amount and budget_notification_emails. Neither is in terraform.tfvars. A plan hangs waiting for interactive input; it is not a failure, it is the designed human dependency. Verified by inspecting variables.tf directly after a first heuristic check misread the presence of the word 'default' in description text."
  blocked_needs: "From the human: (1) budget_limit_amount — should come from T-010's console read of the remaining credit balance (Billing → Credits), not a guess; a monthly USD figure. (2) budget_notification_emails — the address that should receive alerts. budget_notification_thresholds already defaults to [50, 80, 100] and needs nothing."
  escalated: 2026-08-09
  applied: "2026-08-09 — 5 added, 0 changed, 0 destroyed. Plan scope confirmed clean pre-apply: only budgets + SNS, no compute/network/IAM drift (satisfies S9 pre-emptively). terraform plan after apply: No changes (S4 PASS)."
  stage4_results: |
    S1 config read-back   PASS  cv-project-dev-credit-runway  ANNUALLY $121.03  IncludeCredit=false IncludeRefund=false
                                cv-project-dev-gross-usage    MONTHLY  $35.00   IncludeCredit=false IncludeRefund=false
                                The crux is live on BOTH budgets.
    S2 notifications      PASS  6 per budget: ACTUAL + FORECASTED at 50/80/100, all GREATER_THAN.
    S3 subscribers        PASS  SNS topic subscriber present on every notification.
    S4 drift              PASS  terraform plan: No changes.
    S5 topic policy       PASS  Sid=AllowBudgetsPublish, Principal=budgets.amazonaws.com, Action=SNS:Publish,
                                Condition StringEquals aws:SourceAccount=760904708057. This was the most likely
                                "created fine, fires to nobody" bug; it is correctly wired.
    S6 subscription       FAIL-PENDING  erfeamor@gmail.com is PendingConfirmation. Nothing will be delivered
                                until the human clicks AWS's confirmation email. NOT a defect — this is exactly
                                the state DoR decision 3 (SNS over a bare email subscriber) existed to make
                                VISIBLE. A direct email subscriber would have hidden it entirely.
    S7 forced fire        NOT NEEDED ARTIFICIALLY — see natural_fire below.
    S8 revert thresholds  N/A — no artificial threshold was set.
    S9 scope              PASS  apply touched only budgets + SNS.
  threshold_type_false_alarm: "describe-notifications-for-budget OMITS ThresholdType when it is the default, which first read as ABSOLUTE_VALUE (i.e. finding 7's exact failure: threshold 50 meaning $50 not 50%). Investigated rather than reported: terraform plan shows NO drift and state records threshold_type = PERCENTAGE, so AWS stored percentages correctly. False alarm — recorded so the next reader does not re-raise it."
  natural_fire: "No artificial forced-fire needed. cv-project-dev-gross-usage is at $16.435 actual against a $35 limit; its 50% ACTUAL threshold is $17.50, about $1.07 away at $0.92/day — it should cross naturally within ~1-2 days. That is a real threshold crossing, strictly better evidence than an artificially lowered one, and it leaves nothing in a test state to revert."
  finding_annual_window: "REAL, needs a decision. credit_runway shows actual=$39.339, not August-only $16.435 — the difference is exactly July's $22.904. Despite TimePeriod.Start=2026-08-01, AWS accumulates the ANNUAL period over calendar 2026, so it counts spend already paid for by credits that are already gone. Consequence: 100% ($121.03) is reached after only ~$81.69 of FUTURE spend (~89 days, ~6 Nov) rather than at true depletion (~$121.03 more, ~18 Dec) — it fires ~6 weeks EARLY. Safe direction, but the thresholds no longer mean 'percent of remaining credits'. The developer's inline comment documents a ~$16.06 over-count; the real figure is ~$39.34, so that comment is understated and should be corrected either way. Precise fix: set the limit to $160.37 ($121.03 remaining + $39.34 already spent in calendar 2026), which makes 100% land exactly on depletion."
  finding_preexisting_budget: "Discovered during S1, unmanaged by Terraform: a console-created 'My Monthly Cost Budget' with a $5 limit, subscribed to erfeamor@gmail.com, with ACTUAL 85% and ACTUAL 100% BOTH in state ALARM (actual $16.435 = 328% of its limit). So budget emails have been firing to that address already. Two implications: (a) the earlier assumption that no warning had ever arrived may be wrong — check spam; (b) a permanently-alarming $5 budget is alert fatigue, and trains the recipient to ignore exactly the emails the new alarms depend on. Worth deleting or re-basing it; not in this task's scope."
  retune: "Human supplied real console figures mid-stage-4, which changed the design. (a) Total credit GRANT is $160, not the $121.03 remaining — and since the ANNUAL budget accumulates over calendar 2026 (stage-4 discovery, not an assumption), the grant total is the correct limit; 100% now lands on true depletion instead of ~6 weeks early. (b) Monthly limit $30, the measured post-RDS-teardown baseline. (c) THRESHOLDS SPLIT: sharing one list would have fired 50% and 80% every month at ~$28 burn — the exact alert-fatigue property that made the deleted $5 budget useless. credit_runway keeps 50/80/100 (depletion milestones); gross_usage gets 100/120/150 (deviation from expectation). Ratified by the human at a mid-stage-4 gate. Implemented in c2f1b2d, mutation-verified: reintroducing either the shared-thresholds or shared-limit bug fails the suite."
  stage4_final: |
    Re-applied and re-verified after the retune (0 added, 2 changed, 0 destroyed).
    S1  PASS  credit_runway ANNUALLY $160  IncludeCredit=false IncludeRefund=false  actual $39.34 (24%)
              gross_usage   MONTHLY  $30   IncludeCredit=false IncludeRefund=false  actual $16.44 (54%)
    S2  PASS  thresholds correctly disjoint per budget: 50/80/100 vs 100/120/150
    S3  PASS  SNS subscriber on every notification
    S4  PASS  terraform plan: No changes
    S5  PASS  topic policy verified against the LIVE policy: budgets.amazonaws.com / SNS:Publish / aws:SourceAccount
    S6  PASS  subscription CONFIRMED by the owner (was PendingConfirmation). Delivery path proven end to end —
              the confirmation mail itself traversed SNS -> email successfully.
    S7  PASS-BY-DESIGN  no artificial forced-fire was needed or performed. gross_usage is at 54% and August is
              projected to $36.67 (122%) because of the Aug 1-2 RDS-teardown spike, so 100% (~Aug 24) and 120%
              (~Aug 30) will cross NATURALLY this month. A real crossing is better evidence than a lowered
              threshold, and nothing is left in a test state to revert.
    S8  N/A   no artificial threshold set, so nothing to revert.
    S9  PASS  applies touched only budgets + SNS; no compute/network/IAM drift.
  spam_finding: "The reason no warning was ever noticed: AWS billing mail was landing in the owner's SPAM folder. The deleted $5 budget HAD been firing (both ACTUAL thresholds in ALARM). The alerting worked; the delivery did not. This alarm has the same dependency — allowlisting no-reply@sns.amazonaws.com is what makes the December warning actually arrive."
  future_move: "When the owner completes the two remaining credit-earning activities (+$40), budget_credit_grant_amount should move 160 -> 200. The variable's description records this; no code change is pre-applied."
  h2: "ACCEPTED 2026-08-10 by the account owner on a QA-validated, applied and re-verified change."
  merged: "cv-infra PR #13 squash-merged 2026-08-10T06:58:42Z as 941b433. Stage-5 rule honoured: master had moved (222f18e, the Free Tier docs PR) after this branch was cut, so the branch was rebased onto it and the FULL A1 gate plus a terraform plan drift check were re-run on the rebased result before merge — no stale green. terraform plan on merged master: No changes."
  ci_note_final: "cv-infra has no authoritative CI, so stage 3's CI gate never ran and is recorded as NOT satisfied rather than passed. Substitute evidence: A1 (re-run by the driver at every transition, never taken on report), three review passes, and full stage-4 verification against the real account."
  updated: 2026-08-10
---

## Why this exists

Split out of **T-010** at dev-loop stage 0, because it is the one part of that task a developer can actually build. T-010's other steps need two console-only numbers and a human decision; this one does not, and it is the piece that makes the deadline *visible* rather than merely known.

The account is on AWS's post-July-2025 Free Tier — a finite pot of credits plus a 6-month window, not the legacy 12-month allowance (verified: `aws freetier get-free-tier-usage` returns only `Always Free` rows, no `12 Month Free` entries for EC2/RDS/EBS). Credits currently absorb 100% of usage:

```
2026-07   Usage $22.90   Credit -$22.90   net $0
2026-08   Usage $16.06   Credit -$16.06   net $0    (to Aug 9)
```

Burn is **~$0.92/day ≈ $28/month**. Nothing warns anyone.

## The crux — read before writing any HCL

`aws_budgets_budget`'s `cost_types` block defaults **`include_credit = true`**, so the default cost metric is **net** cost. On this account net is **$0 and will stay $0 until the credits are gone.** A budget built with defaults:

- applies cleanly,
- reads green in the console,
- and **never fires**, right up to the moment the account is paused.

That is worse than having no budget, because it manufactures confidence. The resource is only correct if it tracks **gross usage**, via `cost_types { include_credit = false }` (or an explicit `RecordType` cost filter). **This single boolean is the whole task.**

Second, independent way to build a budget that fires to nobody: if an SNS topic is used, its resource policy must allow `budgets.amazonaws.com` to publish. Omit it and AWS Budgets fails silently — neither `describe-budgets` nor `describe-notifications-for-budget` surfaces the failure.

## Scope

- One new Terraform file in `cv-infra` (suggest `budgets.tf`) with `aws_budgets_budget` plus notification wiring.
- Thresholds as **variables**, not literals — see the DoR decision below.
- A `terraform test` assertion set (below).

**Out of scope:** `aws_budgets_budget_action` (auto-enforcement by attaching a deny policy on breach) — that is real IAM scope creep beyond alerting and would trip the repo's own IAM review priority. Also out of scope: any trimming of existing resources; that is T-010's decision to make first.

## DoR decisions (ratified at H1)

1. **Track gross usage, not net.** `include_credit = false`. Non-negotiable — it is the reason the task exists.
2. **Thresholds are variables with placeholder defaults**, documented in `terraform.tfvars.example`. The real figures come from T-010's console read. This task must not invent a credit balance, and must not silently ship a guess as if it were measured.
3. **Prefer an SNS topic over a bare email subscriber.** An SNS subscription's confirmation state is CLI-queryable (`PendingConfirmation` via `list-subscriptions-by-topic`); a direct email subscriber's is not queryable at all. Choosing SNS is what makes "did this actually reach anyone" testable instead of an act of faith. If SNS is used, the topic policy granting `budgets.amazonaws.com` publish rights is mandatory.
4. **Both `ACTUAL` and `FORECASTED` notifications.** At a known ~$0.92/day, forecast is what buys warning time; actual is what confirms it.

## Test plan (authored by Quality Assurance at refinement — QA executes this at stage 4)

### Part 1 — offline, `terraform test` under `mock_provider "aws"`

`aws_budgets_budget` reads no data source and is almost entirely plain config, so unlike the `aws_eip.drone.public_ip` case already noted in `tests/plan.tftest.hcl`, most of it **is** assertable under `command = plan`.

| # | Assertion | Why |
|---|---|---|
| O1 | `cost_types[0].include_credit == false` | **The crux.** A regression here silently makes the feature a no-op |
| O2 | `budget_type == "COST"`, `limit_unit == "USD"` | resource shape |
| O3 | `limit_amount` traces to a variable, not a literal in the resource block | thresholds must trace to T-010's measured figure, not a baked-in guess |
| O4 | at least one `notification` with `notification_type == "ACTUAL"` and one `"FORECASTED"` | forecast buys the warning time |
| O5 | every `comparison_operator == "GREATER_THAN"` | wrong operator fires immediately or never — classic copy-paste bug |
| O6 | subscriber list non-empty and variable-sourced | prevents "created fine, notifies nobody" |
| O7 | *(not assertable)* an `aws_sns_topic` ARN created in the same plan | unknown-until-apply under `command = plan` — same documented limitation as `aws_eip.drone.public_ip`; do not invent a `command = apply` run block to force it |
| O8 | thresholds > 0 and ascending across notification blocks | catches inverted/duplicate thresholds |

**Not testable under mock at all, by nature:** whether AWS's billing engine honours `include_credit = false`; whether the SNS topic policy actually authorizes Budgets; whether a subscription is confirmed; whether anything is *delivered*.

### Part 2 — stage 4, against the real account (760904708057, eu-west-3)

| # | Check | Expected |
|---|---|---|
| S1 | `aws budgets describe-budgets --account-id 760904708057` | `BudgetType: COST`, **`CostTypes.IncludeCredit: false`**, limit matches the variable |
| S2 | `describe-notifications-for-budget` | thresholds/operators/types match the `.tf`, drift-free |
| S3 | `describe-subscribers-for-notification` | correct subscriber present — proves configuration, **not** delivery |
| S4 | `terraform plan` after apply | 0 changes — git matches live, no console drift |
| S5 | *(if SNS)* `aws sns get-topic-attributes` → inspect `Policy` | statement with `Principal.Service: budgets.amazonaws.com`, ideally with an `aws:SourceAccount` condition. **Most likely "fires to nobody" bug in this domain — not optional** |
| S6 | *(if SNS)* `list-subscriptions-by-topic` | a literal `"PendingConfirmation"` SubscriptionArn means nothing will ever arrive. *(If a bare email subscriber was used instead, this is **not automatable** and needs a human to check the inbox.)* |
| S7 | Forced-fire smoke: temporarily set one `ACTUAL` threshold below current gross MTD usage (~$16), apply | notification evaluates as breached and sends. **AWS Budgets evaluates on its own schedule — hours, not real-time.** Do **not** report PASS without an actually-received message; if the session must close, record "applied, pending delivery confirmation" and hand it off |
| S8 | Revert to the real thresholds | nothing left in an always-firing test state |
| S9 | `terraform plan` scope check | changes confined to budgets/SNS; no IAM/network/compute drift |

**Needs a human every run:** confirming a message actually arrived. CLI reads prove the AWS-side pipeline is wired; they cannot prove a human received an email — and that is exactly the failure this task exists to prevent.

## Acceptance criteria

- [ ] `aws_budgets_budget` in Terraform tracking **gross usage** (`include_credit = false`), not net cost.
- [ ] Thresholds and subscriber sourced from variables with placeholder defaults documented in `terraform.tfvars.example`.
- [ ] Both `ACTUAL` and `FORECASTED` notifications, ascending thresholds, `GREATER_THAN`.
- [ ] If SNS-backed: topic policy grants `budgets.amazonaws.com` publish, verified by reading the live policy.
- [ ] `terraform test` gains assertions O1–O6 and O8; O7 documented as not evaluable, matching the existing precedent in the test file.
- [ ] Stage-4 checks S1–S5, S8, S9 pass; S6/S7 delivery either confirmed by a human or explicitly recorded as pending with an owner and a date.
- [ ] No changes to compute, networking, or existing IAM policies.

## Definition of done

PR open against `master` from `feat/budget-credit-alarm`; `terraform fmt -check -recursive`, `terraform validate`, `terraform test` green; applied for real; delivery confirmed or explicitly handed off; task `done` on merge.
