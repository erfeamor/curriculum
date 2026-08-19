---
id: T-019
title: "Stop paying for an idle CI host: start it on demand, stop it when quiet"
repo: cv-infra
status: todo
owner:
branch: feat/ci-host-on-demand
pr:
depends_on: []
risk: normal
security_review: true
---

> ## H1 RATIFIED 2026-08-19 — build it. And two premises below have changed.
>
> **Decision, by the account owner:** build the start-on-push automation. DoR §4 offered closing this task in favour of a documented manual habit and that option is **declined** — see the reason below, which is new information rather than a preference.
>
> **1. The box is already stopped.** `i-073e5284ca2a1ceed` has been `stopped` since **2026-08-14 08:12:29 GMT** (`StateTransitionReason: User initiated`). Nothing on the board recorded it. So the table below — *"runs 24/7"*, *"idle well over 95% of the time, and it is billing every hour of it"* — **describes a state that ended five days before this ruling**. The $17.24/month saving this task promises has *already been taken*, by hand.
>
> **2. That is exactly why the automation is worth building, and it is not the cost argument.** Jenkins and Drone are on this box. **T-102, T-103 and T-104 all carry *"Jenkins CI green"* in their definition of done**, so while it is stopped the entire M2 backend wave cannot close. A manual habit therefore has a failure mode nobody costed: the box gets started for a build and left running (restoring ~$1.23/day and the ~2026-11-17 credit cliff), or it stays stopped and M2 silently cannot land. Start-on-push resolves both — the host is up when work needs it and down otherwise, with no one having to remember either transition.
>
> **3. The saving is now a *retention* problem, not a reduction one.** [T-020](T-020-cost-model-correction.md) measured the current rate at **$0.6837/day ≈ $20.81/month**, below the **$0.761/day** crossover, so the Free-plan window (2027-01-12) binds before the credits (~2027-01-28). This task's job is to keep it that way through months of real CI use. Every hour the host is left up moves the cliff back toward 17 November.
>
> **Acceptance criterion added by this ruling:** the measured rate after a full billing week must still be at or near $0.684/day *with builds actually running through the automation* — proving the doorbell shuts the door again, which is the only part a manual habit reliably gets wrong.

## Why this exists

~~`cv-project-drone` (Jenkins **and** Drone, `t3.small`) runs 24/7 and is **the single largest line on the AWS bill**.~~ **Stale — it was stopped by hand on 2026-08-14; see the ruling above.** It *was* the largest line, and it becomes so again the moment it is started and forgotten. From the 2026-08 cost export, back when it ran continuously:

| Line | $/month | Share of bill |
|---|---|---|
| **CI host compute** | **$17.24** | **46%** |
| domain-service compute | $8.62 | 23% |
| Public IPv4 × 2 | $7.30 | 20% |
| EBS | $4.14 | 11% |

A portfolio project sees a handful of pushes a week. That box is idle well over 95% of the time, and it is billing every hour of it.

This matters more than a normal cost tidy-up because the account is on a **finite credit pot with a hard cliff** (T-010, T-012 — window closes 2027-01-12). Idle spend is runway burned for nothing.

## What makes this feasible — verified, not assumed

**`aws_eip.drone` exists** (`ci.tf:50`), and `server_host` is derived from it (`ci.tf:44,87`). The public IP therefore **survives a stop/start**, so the GitHub webhook URL and the Drone/Jenkins server URLs stay valid across cycles.

If the host had an auto-assigned public IP this task would be near-impossible: every start would hand out a new address and silently break every webhook. Confirm this still holds before building — it is the load-bearing assumption.

## What this is NOT

**Jenkins and Drone cannot run on Lambda.** This was asked and investigated; recording the answer so it is not re-explored:

- Both are stateful long-running servers — Jenkins needs a persistent `JENKINS_HOME` (job config, history, credentials, plugin state); Drone's server holds a queue and a database. Lambda offers ephemeral `/tmp` and nothing that survives an invocation.
- Lambda's **15-minute cap** leaves no headroom for a Maven build plus a cold dependency or image pull.
- **No Docker daemon** on Lambda — no privileged containers, no nested virtualisation. Any pipeline step that builds or pushes an image cannot run there.
- They are webhook receivers with web UIs. A function that is not running is not listening.

**Nor is this a move to CodeBuild.** Serverless CI on AWS exists and would genuinely cost near-zero, but adopting it deletes the multi-CI diversity the demo exists to show (meta CLAUDE.md: *"Different CI per repo is a feature of the demo, not drift to fix."*). Rejected deliberately.

## The shape

Lambda as the **doorbell**, not the building:

```
GitHub webhook → Lambda (Function URL) → ec2:StartInstances → 200 returned immediately
                                              ↓
                                     CI host boots, runs the build
                                              ↓
                     EventBridge schedule → Lambda → stop when idle
```

Lambda cost at this volume is effectively **$0** (a few invocations a month; a Function URL needs no API Gateway).

## What it actually saves — do not overstate this

**~$17.24/month, the compute only.** A *stopped* instance still bills for:

- its **EIP** — since 2024-02-01 AWS charges every public IPv4 ~$0.005/hour whether attached, unattached, or on a stopped instance (~$3.65/month), and
- its **EBS root volume**.

So the CI host costs roughly **$5–6/month stopped versus ~$23/month running**. Releasing the EIP would save the rest but breaks the webhook URL, which is the one thing making this work — do not do it.

## Definition of Ready — settle these before writing code

**1. Webhook replay — this determines whether this is an afternoon or a weekend.** By the time the box is up, the event that woke it is gone and GitHub will not redeliver. Options, cheapest first:
   - *Jenkins polls SCM on startup* — a checkbox; catches anything pushed while down. Least code, slight delay, and it is unclear how the Drone half is covered.
   - *Lambda writes the event to SQS; CI drains the queue on boot* — durable, more moving parts.
   - *Lambda retries against the Jenkins/Drone API once the host is healthy* — most work, most to go wrong, needs the Lambda to wait or self-reschedule.

   **Pick one at H1.** Do not start building before this is decided; it drives the whole design.

**2. Idle detection.** What proves CI is finished and not merely between stages? A fixed timer will kill a running build. Needs the queue to be empty *and* no executor busy for N minutes. Decide N, and decide what happens to a build that starts during the shutdown window.

**3. Function URL authentication — do not skip this.** See the security note below.

**4. ~~Automate at all, or just stop it by hand?~~ SETTLED at H1 on 2026-08-19: automate.** ~~Manual `aws ec2 stop-instances` saves the **identical** $17.24/month with zero new infrastructure, zero IAM, and nothing to break. The Lambda buys convenience, not savings… **A defensible H1 outcome is to close this task in favour of a documented manual habit.**~~ The reasoning was sound and lost to a fact it did not have: the manual habit was *already in force* (stopped 2026-08-14) and it silently blocks M2, whose three backend tasks require Jenkins green. The choice was never "save $17.24 twice" — it is between a host that is up when work needs it, and a human remembering both transitions correctly every time for five months. The Lambda's failure modes are real and are what §§1–3 above exist to settle; they are now accepted rather than avoided.

## Security — why `security_review: true`

**An unauthenticated Function URL that can start EC2 instances is a cost-denial-of-service endpoint.** Anyone who learns the URL can start the instance repeatedly and burn credits that are finite and on a deadline.

- The Lambda **must validate GitHub's HMAC signature** (`X-Hub-Signature-256`) against the webhook secret before taking any action, and reject everything else. The secret goes in SSM Parameter Store, never in a `.tf` file.
- The Lambda's IAM role gets `ec2:StartInstances`/`ec2:StopInstances` **scoped by resource ARN to this one instance**, never `Resource: "*"`. cv-infra's own review guidance ranks over-broad IAM fourth on its list.
- The role must not be able to terminate, resize, or modify the instance.

## Acceptance criteria

- [ ] A push to a watched repo starts the CI host, and the build **actually runs** — proven end to end with a real push, not by reading the Terraform.
- [ ] The host stops automatically when idle, and **a build in progress is never killed** — proven by starting a build and confirming it survives the shutdown window.
- [ ] An unsigned or wrongly-signed request to the Function URL changes nothing and starts no instance (test it).
- [ ] IAM is scoped to the single instance ARN and to start/stop only.
- [ ] The webhook secret lives in SSM, not in a committed file.
- [ ] `terraform fmt -check -recursive`, `terraform validate`, `terraform test` pass offline, with assertions for the new Lambda, its IAM policy and the schedule.
- [ ] The measured saving is recorded against **[T-020](T-020-cost-model-correction.md)**'s cost model (not T-010's, which is superseded) after a full billing week — and the rate is still at or near **$0.6837/day** *with builds running through the automation*. Added at H1 2026-08-19: the host is already stopped, so a low rate proves nothing on its own. What needs proving is that it goes back down after each build.
- [ ] **A build that needs the host actually completes end to end while the automation owns the lifecycle** — pick one of T-102/T-103/T-104's PRs, or an equivalent push to `cv-domain-service`, and confirm Jenkins reports a commit status. This is the criterion that connects the task to why it was ratified.

## Definition of done

PR open against `master` from `feat/ci-host-on-demand`, gates green, applied, verified with a real push, merged.

## dev-loop notes

- **Developer:** `infrastructure-engineer`. **Reviewers:** `/code-review` + `infrastructure-engineer` + `/security-review` (forced — IAM plus a public endpoint).
- **Interacts with three other tasks on this same host.** [T-005](T-005-ci-secret-blast-radius.md) (block IMDS from containers), [T-008](T-008-drone-host-backup-and-snapshot.md) (real backup) and [T-009](T-009-user-data-size-ceiling.md) (get the provisioning script out of `user_data`) all touch it. **T-009 especially** — if this task adds bootstrap logic it pushes `user_data` further toward the 16 KB wall T-009 exists to avoid. Check T-009's headroom measurement before adding to that script.
- **Stopping the host takes Jenkins and Drone offline**, which are part of what the demo shows. If someone is being walked through CI, the box needs to be up — factor a manual override into whatever is built.
- **Related but separate:** the cost model in `cv-infra/CLAUDE.md` (~$0.92/day ≈ $28/month) and T-010's runway are both stale since the 2026-08-08 `t3.micro`→`t3.small` resize took the real rate to ~$1.23/day ≈ $37.30/month. Correcting those is not this task, but this task's saving should be folded in when they are. **Now owned by [T-020](T-020-cost-model-correction.md)**, filed 2026-08-14 precisely because no task owned it.
- **What this task is worth changed on 2026-08-14 — read before H1.** T-010 ratified *"do NOT trim the run rate"* on the grounds that savings expire unspent while the 6-month window binds. Re-deriving the dates at the real $1.23/day shows **credits bind first, by ~8 weeks** ([T-012](T-012-aws-endgame-decision.md)), so a trim now buys elapsed demo time instead of nothing. This task's $17.24/month is roughly enough to push credit exhaustion past the window and hand the binding constraint back to it.
  - ~~**That argues for the saving, not necessarily for the Lambda.** … **Closing this task in favour of a documented manual habit remains the defensible H1 outcome** — the changed numbers make the saving worth taking, not the automation worth building.~~ **Overtaken by events, 2026-08-19.** The manual habit was adopted (2026-08-14) *before* this argument was ever weighed at a gate, and [T-020](T-020-cost-model-correction.md)'s readings show what it actually bought: the rate fell to $0.684/day and the window binds again — but the same act took Jenkins offline, and three M2 tasks require it. **H1 ratified building the automation.** The saving is no longer the argument; keeping the saving *without* blocking M2 is.
