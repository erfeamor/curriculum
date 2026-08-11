---
id: T-012
title: Decide Paid-vs-teardown before the Free-plan window closes (~2027-01-12)
repo: cv-project (meta)
status: todo
owner:
branch: chore/aws-endgame-decision
pr:
depends_on: []
risk: high
due: 2026-12-20
deadline: 2027-01-12
---

## Why this exists

T-010 answered *when* the account dies and built the alarm that warns about it. It deliberately **deferred one decision**, and this task holds it so it is not lost in a task marked `done`.

**On the Free plan, 2027-01-12 is a hard ceiling.** Not a soft one, and not one more credits can move:

```
grant $160 (Aug 2026):   $120.66 left -> 131d -> credits die 2026-12-20   CREDITS bind
grant $200 (after acts): $160.66 left -> 175d -> window shuts 2027-01-12  WINDOW binds
```

Completing the two $20 activities buys ~3 weeks and then stops helping. **Trimming the run rate buys nothing at all while the window binds** — savings would expire unspent. That is why T-010 recorded "no trims" as a decision rather than an oversight.

When the window closes on the Free plan, AWS **pauses the account and stops the resources**. That is the whole stack: both EC2 instances, the CI host that gates `cv-domain-service` and `cv-database`, CloudFront, the lot.

## The decision

Pick one, by **20 December 2026** at the latest — that is when the runway alarm's 100% threshold fires and when there is still time to act calmly.

**A · Upgrade to the Paid plan.** ~$28/month ongoing. The demo survives indefinitely. **Trimming becomes worthwhile the moment this is chosen**, because the bill is now recurring rather than notional:

| Line | $/mo | Share | Note |
|---|---|---|---|
| compute — 2 instances | $18.30 | 65% | consolidating to one box is the big lever, but it undoes T-002's CI host split |
| public IPv4 — 2 EIPs | $6.80 | 24% | the Drone EIP is load-bearing (webhooks + OAuth callback registered against it); the domain-service one is referenced by CloudFront's `/api/*` behaviour, so removing it is work, not a toggle |
| EBS gp3 | $3.20 | 11% | |

**B · Accept the cliff, tear down, rebuild later.** The stack is IaC, so a rebuild is `terraform apply`. Cheap in money, expensive in the one thing Terraform does not hold — see the blocker below.

**C · Migrate off AWS** for the always-on parts. `cv-public-react` already runs on Vercel; the static site is CloudFront+S3. The genuinely AWS-shaped pieces are the two EC2 instances and Cognito. Out of scope to plan here, but worth naming so it is a considered option rather than a forgotten one.

## Blocker on option B — read before choosing it

**`terraform destroy` does not preserve Drone's state.** Its `drone-deploy` `aws_access_key_id`/`aws_secret_access_key` exist only in `/var/lib/drone/database.sqlite` on the CI host — not in SSM, not in Terraform state, not reconstructable without re-issuing an IAM key and re-activating repositories by hand.

The only copy today is `snap-0d7f5ae272ce0cef5`, the T-002 pre-apply gate snapshot, retained deliberately for exactly this reason. **If B is chosen, T-008 must land first**, or the rebuild starts by re-issuing credentials.

Same question applies to self-hosted MySQL, tracked as **T-001**.

## Do first, regardless of which option wins

- [ ] **Complete the two remaining $20 credit-earning activities** (Lambda; foundation-model experimentation). Free, ~1 hour, moves the cliff 20 Dec → 12 Jan. Ratified in T-010.
- [x] **Allowlist `no-reply@sns.amazonaws.com`** — **done 2026-08-11.** T-010 found the previous budget had been firing for months into a spam folder: the alerting worked, the delivery did not. The December warning inherited that dependency and has exactly one job. With the subscription confirmed *and* the sender allowlisted, the delivery path is now clear end to end. Note this is an inbox-side setting, invisible to Terraform and to `describe-budgets` — if the mailbox or its rules ever change, this silently reverts and nothing in AWS will say so.
- [ ] **Do not raise `budget_credit_grant_amount` to $200** when the grant increases. Corrected in cv-infra PR #14, restated here because it is counter-intuitive: at $200 the 100% alert fires 2027-02-01, ~20 days *after* the account is paused. Held at $160 it fires 24 Sep / 15 Nov / 20 Dec.

## Acceptance criteria

- [ ] The two activities completed, and the new grant total recorded here.
- [ ] A written decision — A, B, or C — with its cost and its consequences, made on or before 2026-12-20.
- [ ] If **A**: the plan upgraded, and a follow-up task filed for the trims that are now worth doing.
- [ ] If **B**: T-008 landed first, a teardown runbook written, and the rebuild verified at least once against a throwaway apply rather than assumed.
- [ ] If **C**: the migration scoped as its own dependency-ordered tasks.
- [ ] Whichever is chosen, `docs/architecture.md` and both `CLAUDE.md` files reflect it.

## Definition of done

A decision written down before the deadline, with its consequences owned — not a date that passed while the board said `todo`.
