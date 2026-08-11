---
id: T-010
title: Track the AWS credit runway and the free-plan cliff before it stops the demo
repo: cv-project (meta)
status: done
owner: tech-product-owner
branch: chore/credit-runway-decision
depends_on: []
risk: high
security_review: false
checkpoint:
  stage: done
  repo: cv-project (meta)
  branch: chore/credit-runway-decision
  developer: tech-product-owner   # NOT an implementable-by-agent task — see human_dependency
  reviewers: [infrastructure-engineer]
  risk: high
  security_review: false
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: 0
  split: "Stage 0 split the implementable half out as T-011 (cv-infra, budget alarm). This task was repo: 'cv-infra + meta', which the adapter forbids past stage 0 — every task leaving stage 0 touches exactly one repo. What remains here is meta-only."
  RESOLVED_console_read: "2026-08-09, read by the account owner. TOTAL CREDIT GRANT: $160 on the FREE PLAN (not Paid). $39.34 already consumed in calendar 2026, leaving $121.03 at the time of reading. Owner intends to reach $200 by completing two more credit-earning activities (Lambda, and a foundation-model experimentation one) worth $20 each — so this figure is expected to move, and the budget limit should move with it."
  RESOLVED_the_date: "Credits exhaust ~18 December 2026 at the measured $0.92/day. The Free-plan 6-month window closes ~12 January 2027 (account created 2026-07-12). CREDITS BIND FIRST, by about 3.5 weeks. On the Free plan, exhaustion means AWS PAUSES the account and STOPS resources — not a surprise invoice. Around 18 Dec the demo goes dark, CI host included, unless a decision is taken before then."
  RESOLVED_why_no_warning: "AWS billing mail was landing in the owner's SPAM folder. A console-created 'My Monthly Cost Budget' ($5 limit, subscribed to the owner) had ACTUAL 85% and 100% both in ALARM state and had been firing all along — the mail simply was not seen. The owner has since deleted that budget (it was Terraform-unmanaged; verified no drift). This is worth remembering: the alerting T-011 builds is only as good as the recipient's spam rules."
  remaining_work: "The alarm half is done (T-011). What is left here is the DECISION: accept the ~18 Dec cliff and plan a teardown/rebuild, upgrade to the Paid plan, or cut the run rate. Trim candidates measured earlier: two public IPv4 at ~$3.60/mo each is ~26% of the bill, and two t3 instances running 24/7 for an interactively-used demo. NOTE T-008 becomes urgent if the answer is teardown-and-rebuild: Drone's drone-deploy AWS credentials exist only in /var/lib/drone/database.sqlite."
  human_dependency: "BLOCKING and unavoidable: steps 1 and 3 need the AWS console (Billing → Credits) — remaining credit balance, each credit's expiry, and Free-plan vs Paid-plan. Neither is exposed by any AWS API; the CLI cannot read them. No developer persona can satisfy this. Everything downstream (the projected date, the real budget thresholds in T-011, and whether any trimming is warranted) depends on those two numbers."
  DECISION: "Ratified by the account owner 2026-08-11. (a) Complete the two remaining $20 credit-earning activities now — free, ~1 hour, moves the cliff from 20 Dec to 12 Jan. (b) Do NOT trim the run rate: the modelling shows it buys nothing on the Free plan, because past ~$32/mo burn the 6-month WINDOW binds before the credits do, so savings would expire unspent. Trimming only pays on the Paid plan, where the bill is ongoing. (c) Defer the Paid-vs-teardown decision to early January — filed as T-012 so it is not lost."
  DECISION_modelling: |
    grant $160 (today):   $120.66 left -> 131d -> credits die 2026-12-20   CREDITS bind
    grant $200 (+2 acts): $160.66 left -> 175d -> but window shuts 2027-01-12  WINDOW binds
    => the activities buy ~3 weeks; after that 2027-01-12 is a HARD ceiling on the Free plan
       regardless of burn rate. This inverts this task's own original framing, which listed
       "cut the run rate" as an endgame option — it is not one while the plan window binds.
    burn breakdown (~$28/mo): compute 2 instances $18.30 (65%), 2 public IPv4 $6.80 (24%), EBS gp3 $3.20 (11%)
  spam_resolved: "2026-08-11 — the owner allowlisted no-reply@sns.amazonaws.com. Combined with the confirmed SNS subscription, the delivery path that failed silently for months is now clear end to end. Worth remembering that this is the ONLY link in the chain that lives outside AWS: Terraform cannot assert it, describe-budgets cannot see it, and stage-4 verification cannot test it. If the mailbox or its filters change, the alarm reverts to the exact failure this task was written to fix, with no signal anywhere."
  alarm_trap_found: "Closing this decision exposed a trap in T-011's shipped comment, which instructed the next reader to raise budget_credit_grant_amount to $200 once the activities land. That would push the 100% alert to 2027-02-01 — ~20 days AFTER the Free-plan window pauses the account. The alarm would stay armed, stay green, and fire only once it could no longer help. Corrected in cv-infra PR #14: the limit is HELD at $160, where thresholds fire 24 Sep / 15 Nov / 20 Dec. Semantics shift with it — 100% now means '~3 weeks to the window', not 'credits exhausted'. The instruction that created the trap was the driver's own; it was caught by comparing the two candidate death dates against each other rather than looking at either alone."
  outcome: "All acceptance criteria met. Balance/plan/expiry recorded; the date derived from measured burn and the binding constraint identified; the budget alarm built, applied and verified (T-011); the endgame decision written down; CLAUDE.md corrected in both repos. No trims applied — deliberately, per the modelling above, and that non-action is the recorded decision rather than an omission."
  updated: 2026-08-11
---

## Why this exists

The whole project has been reasoning about cost using a rule that does not apply to this account, while the constraint that *does* apply is untracked and has a deadline.

`CLAUDE.md` says "AWS resources stay within Free Tier limits", and T-002 budgeted a *"+$8/mo Free Tier exception"* on the basis that the account gets 750 h/month of `t2/t3.micro` and is therefore only billed for the excess. **Neither is true here.**

AWS replaced the Free Tier for accounts created on or after **15 July 2025**: instead of a 12-month allowance, new accounts get a pot of signup credits (up to ~$200 — $100 at signup plus $100 earned through activities) and a **6-month window**, whichever runs out first. The legacy 750 h/month allowance applies only to accounts created before that cutoff.

Account `760904708057`'s oldest IAM principal dates to **2026-07-12**, so it is on the new model. Verified directly rather than inferred:

```
$ aws freetier get-free-tier-usage
  → Always Free: AWS Glue, Amazon SQS, AWS KMS
  → NO "12 Month Free" entries for EC2, RDS or EBS
```

The absence of those rows is the proof: **there is no 750 h EC2 allowance on this account.** Every instance-hour bills.

## What is actually happening

```
2026-07   Usage $22.90    Credit -$22.90    net $0
2026-08   Usage $16.06    Credit -$16.06    net $0     (to Aug 9)
```

Credits are absorbing 100% of usage, which is exactly why no billing alarm has ever fired and why the "no warnings" observation is not evidence of being within a free allowance.

Steady-state burn since the RDS teardown finished is **$0.92/day ≈ $28/month** — not the ~$16.60 T-002 projected. Roughly **$38.96 of credits already consumed.**

## The risk, stated plainly

**If the credits run out, or the 6-month window closes, while the account is on the Free plan, AWS pauses the account and stops the resources.** That is not a surprise invoice — it is the demo going dark, including the CI host that gates `cv-domain-service` and `cv-database`.

Rough runway at ~$28/month:

| Starting credits | Exhausted around |
|---|---|
| $100 | **mid-October 2026** |
| $200 | **January 2027** |

The 6-month window closes around **2027-01-12** regardless.

**Two numbers are needed to turn this from an estimate into a date, and neither is available from the CLI** — both are console-only, under **Billing and Cost Management → Credits** and the account's plan setting:

1. The **remaining credit balance** (and each credit's own expiry date).
2. Whether the account is on the **Free plan** (pause on exhaustion) or the **Paid plan** (billed to the card on file). These have completely different failure modes and the mitigation differs accordingly.

Getting those two facts is step one of this task and it takes about a minute.

## Work

1. **Read the balance and plan type in the console; record both in this file**, with the date read. Everything below depends on them.
2. **Create an AWS Budget with alerts** — Terraform `aws_budgets_budget`. Worth doing even beyond the alerting: creating a budget is one of the activities that earns $20 of additional credits under the new Free Tier, so this step may partly fund itself. Suggest alerting on both actual spend and forecast, and — more usefully here — on **credit depletion** rather than invoice total, since the invoice reads $0 right up until it doesn't.
3. **Decide the endgame and write it down.** Options, not mutually exclusive:
   - Accept the cliff and plan a teardown/rebuild (`terraform destroy` + re-apply is already the demo's stated capability — but note T-008: Drone's SQLite state and its `drone-deploy` credentials do not survive that without a backup).
   - Move to the Paid plan and accept ~$28/month.
   - Cut the run rate. The obvious targets are below.
4. **Trim what is cheap to trim**, if the runway is short:
   - **Two public IPv4 addresses at ~$3.60/mo each ≈ $7.20/mo — about 26% of the bill.** Since Feb 2024 AWS charges for *all* public IPv4, associated or not. The Drone EIP is load-bearing (GitHub webhooks and the OAuth callback are registered against it); the domain-service one may not need to be static.
   - Two `t3` instances running 24/7 for a demo that is used interactively. A stop/start schedule outside working hours would roughly halve the compute line.
   - Confirm nothing is left over from the RDS era — verified clean on 2026-08-09 (no instances, no manual snapshots), but re-check after any rollback.

## Explicitly not in scope

Re-architecting for cost (serverless, spot, smaller regions). This task is about knowing the deadline, being told before it arrives, and having a decided answer — not about rebuilding the stack.

## Acceptance criteria

- [ ] Remaining credit balance, individual credit expiry dates, and account plan type (Free vs Paid) recorded in this file with the date read.
- [ ] A projected exhaustion date derived from actual burn, and the earlier of that and the 6-month window identified as **the** date.
- [ ] `aws_budgets_budget` in Terraform with alerting that fires on credit depletion, not just invoice total — and verified to actually deliver (a budget nobody receives is worse than none, because it manufactures false confidence).
- [ ] A written decision on the endgame: accept the cliff, upgrade to Paid, or reduce burn — with its cost recorded.
- [ ] Any agreed trims applied, with before/after run rate measured via Cost Explorer rather than estimated.
- [ ] `CLAUDE.md` (meta + cv-infra) no longer states or implies the legacy Free Tier rule. *(Partly done — see the docs PR that accompanied this task's creation; verify it still reads true.)*

## Definition of done

PR open against `master` from `chore/credit-runway-guardrails`, the two console numbers recorded here, a working budget alarm, and a decision written down rather than deferred.

## Related

- **T-002** budgeted against the legacy model; its "Free Tier exception" framing is corrected but its `t3.small` decision stands — it was the right call, just mis-labelled.
- **T-008** matters if the answer is "tear down and rebuild": Drone's `drone-deploy` AWS credentials exist only in `/var/lib/drone/database.sqlite`, and the T-002 gate snapshot (`snap-0d7f5ae272ce0cef5`) is currently their only backup.
- **T-001** covers the same durability question for self-hosted MySQL.
