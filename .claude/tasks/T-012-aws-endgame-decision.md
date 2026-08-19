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
due: 2026-11-01          # re-dated 2026-08-14 — was 2026-12-20, which is AFTER the credits run out at the real burn rate
deadline: 2027-01-12     # the Free-plan window; no longer the binding constraint, see below
---

## Why this exists

T-010 answered *when* the account dies and built the alarm that warns about it. It deliberately **deferred one decision**, and this task holds it so it is not lost in a task marked `done`.

**On the Free plan, 2027-01-12 is a hard ceiling.** Not a soft one, and not one more credits can move. But it is no longer the thing that binds first.

### Re-dated 2026-08-14 — the credits run out ~5 weeks earlier than this task said

The model below was built at **$0.92/day**. The real rate has been **$1.23/day** since the 2026-08-08 `t3.micro`→`t3.small` resize of the CI host (verified against the August cost export). The rate change was recorded on the board; the dates derived from it were not re-run. Re-running them, from the same console read ($120.66 remaining on 2026-08-11):

```
                          modelled ($0.92/d)          re-derived ($1.23/d)
grant $160 (current):     131d -> 2026-12-20          98d -> ~2026-11-17   CREDITS bind (~8wk)
grant $200 (after acts):  175d -> 2027-01-12          130d -> ~2026-12-19  CREDITS bind (~3wk)
```

**`due` was 2026-12-20 — after the money is gone in the $160 case.** It is now **2026-11-01**, which keeps T-010's principle intact: decide while there is still time to act calmly, not on the day the alarm fires.

**Two conclusions below are now wrong, and are struck rather than deleted:**

- ~~"Completing the two $20 activities buys ~3 weeks and then stops helping."~~ They still buy ~4½ weeks, but they no longer reach the window — credits bind in **both** rows now. Whether they were ever completed is unrecorded (T-010 ratified doing them on 2026-08-11); establishing that is T-020's §2.
- ~~"Trimming the run rate buys nothing at all while the window binds — savings would expire unspent."~~ **This no longer follows from its own reasoning.** It rested on a crossover at ~$32/month: *below* that, the window binds and savings expire unspent. Real burn is **$37.30/month — above the crossover** — so credits bind first and trimming buys real elapsed demo time (up to ~8 weeks in the $160 case; enough to hand the binding constraint back to the window). T-010's "no trims" was a correct decision on the numbers it had; the numbers changed three days before it was ratified and nobody re-checked. See **[T-019](T-019-ci-host-on-demand.md)** — and note its DoR §4: stopping the CI host by hand saves the identical $17.24/month with no new infrastructure.

**These dates are derived, not read.** The balance is from 2026-08-11 and the rate is inferred from a cost export; the true remaining balance is visible only in the console (no AWS API exposes it). **[T-020](T-020-cost-model-correction.md) holds that read** and will correct this task again if the console disagrees.

When the window closes on the Free plan, AWS **pauses the account and stops the resources**. That is the whole stack: both EC2 instances, the CI host that gates `cv-domain-service` and `cv-database`, CloudFront, the lot.

## The decision

Pick one, by **1 November 2026** at the latest (was 20 December — see the re-dating above; the old date assumed a burn rate a third too low, and the alarm threshold it was pinned to fires on the same stale model, which is T-020's §4).

**A · Upgrade to the Paid plan.** ~$37/month ongoing at the current rate — **not the ~$28 written below**, same staleness; the table's line items are pre-resize and understate compute. The demo survives indefinitely. **Trimming becomes worthwhile the moment this is chosen**, because the bill is now recurring rather than notional:

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
- [ ] **Do not raise `budget_credit_grant_amount` to $200** when the grant increases. Corrected in cv-infra PR #14, restated here because it is counter-intuitive: at $200 the 100% alert fires ~20 days *after* the account is paused. ~~Held at $160 it fires 24 Sep / 15 Nov / 20 Dec.~~ **Those three dates are stale (struck 2026-08-17): they were derived at $0.92/day, in the same file that re-derives everything else at $1.23/day.** At the real rate the thresholds arrive earlier — the 100% one lands on credit exhaustion (~2026-11-17), not 20 December. The *decision* (hold at $160) is unaffected and still correct; only the predicted dates were wrong. Re-deriving them against the real console balance is **[T-020](T-020-cost-model-correction.md) §4**, which owns the alarm question.

## Acceptance criteria

- [ ] The two activities completed, and the new grant total recorded here.
- [ ] A written decision — A, B, or C — with its cost and its consequences, made on or before **2026-11-01**.
- [ ] If **A**: the plan upgraded, and a follow-up task filed for the trims that are now worth doing.
- [ ] If **B**: T-008 landed first, a teardown runbook written, and the rebuild verified at least once against a throwaway apply rather than assumed.
- [ ] If **C**: the migration scoped as its own dependency-ordered tasks.
- [ ] Whichever is chosen, `docs/architecture.md` and both `CLAUDE.md` files reflect it.

## Definition of done

A decision written down before the deadline, with its consequences owned — not a date that passed while the board said `todo`.
