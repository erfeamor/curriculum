---
id: T-019
title: "Stop paying for an idle CI host: start it on demand, stop it when quiet"
repo: cv-infra
status: done
owner: infrastructure-engineer
branch: feat/ci-host-on-demand
pr: https://github.com/erfeamor/cv-infra/pull/17   # filled in 2026-08-20 — was blank while the URL sat in checkpoint.pr only (board rule 6, the same bug this sweep fixed in T-011 three days earlier)
depends_on: []
risk: normal
security_review: true
checkpoint:
  stage: stage-4-verified
  pr: https://github.com/erfeamor/cv-infra/pull/17
  applied: "2026-08-19 — 15 added, 1 changed, 2 destroyed. aws_instance.drone updated in place (user_data only; no replacement, instance type untouched). SSM re-provisioning succeeded in 37s. terraform plan after the follow-up fixes: No changes."
  stage4: |
    13 of 14 live checks passed on the first full run; the 14th was drift from a
    hand-set tag and is now resolved. Proven by request against the live account,
    never by reading Terraform:
      - stopped -> signed webhook -> "starting" -> RUNNING   (the core loop)
      - stopped -> UNSIGNED request -> "bad signature" -> still STOPPED
      - stopped -> WRONG signature  -> "bad signature" -> still STOPPED
      - GET -> 405, signed ping -> pong (no start), signed push for a repo
        outside the allowlist -> handler 403
      - reaper honours CIKeepAlive: {"stopped": false, "reason": "keepalive tag set"}
      - both IAM policies read back from the live account: ARN-scoped to the one
        instance, start/stop only, no destructive actions
      - secret is SecureString; schedule ENABLED at rate(5 minutes)
  stage4_findings: |
    TWO DEFECTS, neither visible from the config, both fixed in 03faeb5:
    1. The Function URL 403'd every request and the Lambda was NEVER invoked
       (zero log streams) while a direct invoke worked. This account's default
       Lambda block-public-access makes aws_lambda_function_url's own
       InvokeFunctionUrl grant insufficient; an unconditioned
       lambda:InvokeFunction grant is required. The whole deployment was inert
       and every plan-time assertion passed anyway.
    2. CIKeepAlive -- the documented manual override -- was queued for removal
       by the next plan. Terraform would have stripped it silently, mid-demo.
       Now under lifecycle.ignore_changes.
  SUPERSEDED_remaining: "ONE manual step, and the automation is inert until it happens: re-point the GitHub webhooks at the Function URL with the secret (ci.tf manual step 5). Until then a real push does not reach the doorbell and the box must be started by hand. T-019's 'proven with a real push' criterion is NOT yet met -- the doorbell path is proven with a signed synthetic payload."
  remaining: |
    CORRECTED 2026-08-20 against GitHub and the live account. The note above was stale in
    its premise and right in its conclusion, for a different reason:
      - THE MANUAL STEP WAS DONE. Both Jenkins repos point at the doorbell:
        cv-domain-service and cv-database -> https://5jw5mezcgcwzhx4zasjmlnd6340gczrd
        .lambda-url.eu-west-3.on.aws/, active=true, last delivery OK. The automation
        is NOT inert; nothing has to be started by hand.
      - THE CRITERION IS STILL UNMET, but only this much: the hook delivery history
        holds exactly one event, "2026-08-19T09:39:19Z ping status=OK code=200". No
        PUSH has ever reached the doorbell, so "the build actually runs" is unproven.
        The NEXT push to either Jenkins repo is the proof -- T-102 supplies it for free.
      - Also still open: the billing-week criterion (rate at/near $0.6837/day WITH
        builds running through the automation). Needs elapsed time, not work.
    Merged as bd65353 (cv-infra#17), so this task is `done` by board rule 6. The two
    criteria above are recorded here rather than held open as a status, because a task
    parked in `in_review` after its PR merged is what this board keeps having to fix.
  note: "Stage 0 refinement done 2026-08-19; §4 was ratified the same day (build it) and §§1-3 are ruled on below, PENDING H1 RATIFICATION. Nothing is implemented yet — T-019's own DoR §1 forbids writing code before the replay design is chosen."
  repo: cv-infra
  branch: feat/ci-host-on-demand
  worktree: none      # cv-infra has a local Terraform backend; it cannot be worked from a worktree (same as T-014/T-018)
  developer: infrastructure-engineer
  reviewers: [code-review, infrastructure-engineer, security-review]
  risk: normal
  security_review: true
  review_round: 0
  premises_reverified: |
    2026-08-19 against cv-infra@774a9fc, and this is where refinement earned its keep:
    - aws_eip.drone CONFIRMED (ci.tf:50), server_host derived from it (ci.tf:44, :87). The
      load-bearing assumption holds — the public IP survives stop/start.
    - The box is ALREADY STOPPED (since 2026-08-14 08:12 GMT), so this task's premise that it
      "runs 24/7" is false and the $17.24/mo is already saved. See the H1 ruling at the top.
    - Jenkins jobs are multibranchPipelineJob via JCasC + job-dsl with NO periodic trigger
      configured (jenkins-provision.sh:101, :135) — they are driven purely by the GitHub
      webhook at /jenkins/github-webhook/. This is the fact that decides ruling 1.
    - user_data measured at 15,796 / 16,384 B = 96.4%, headroom 588 B — TIGHTER than T-009's
      95.7%. Anything this task adds to a template competes with that.
    - No GitHub webhook secret exists anywhere in the repo (T-005 planned one and it was never
      built), so ruling 3's HMAC validation has nothing to validate against yet. See ruling 4.
    - tests/plan.tftest.hcl: mock_provider, 77 assertions. New data sources need mocks.
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

## Definition of Ready — refined 2026-08-19, rulings PENDING H1

§4 was ratified separately (build it). These settle §§1–3, each against a fact from the repo rather than a preference.

### Ruling 1 — replay: give the Jenkins jobs a periodic scan; the Lambda stays a pure doorbell

**The deciding fact:** the two Jenkins jobs are `multibranchPipelineJob`s (`jenkins-provision.sh:101`, `:135`) with **no trigger block at all**. They act on the GitHub webhook and nothing else. But a multibranch pipeline also *scans* its SCM on a `periodicFolderTrigger`, and a scan finds any branch whose head moved while Jenkins was down — which is exactly the replay problem, already solved by the plugin.

**Ruling:** add `triggers { periodicFolderTrigger { interval('5m') } }` to both jobs. The Lambda then never has to store, queue, or forward a payload: it starts the box and returns 200, Jenkins boots, the first scan picks up whatever was pushed, and the build runs. DoR §1's option 1 ("Jenkins polls SCM on startup — a checkbox"), confirmed feasible against the actual job config rather than assumed.

Rejected — **SQS + drain on boot** (option 2) and **Lambda retries against the API** (option 3): both exist to move a payload the periodic scan makes unnecessary, and each adds a component that fails looking like "CI is broken", which this task's §4 warns about explicitly.

**The cost of this ruling, stated plainly: it does not cover Drone.** Drone is webhook-only — no SCM polling — so a push to `cv-admin-react` while the box is down starts the box and then builds nothing. Accepted deliberately: the ratified reason for building this task is that M2's backend wave needs Jenkins, and `cv-admin-react`'s task (T-301) is waves away. **Documented, not silently dropped** — the Drone half wants its own decision at T-301, and forcing a payload-forwarding design now would buy a repo nobody is working in.

### Ruling 2 — idle detection: ask the CI systems, do not infer from CPU

§2 requires the queue empty **and** no executor busy. A CPU-threshold rule would be far simpler and is **rejected**: a Maven build that is pulling dependencies or waiting on Docker sits near-idle for minutes and would be killed mid-run, which is the one failure this task must not have.

**Ruling:** an EventBridge schedule every 5 minutes invokes a *reaper* Lambda, which reads Jenkins `/api/json` (queue) and `/computer/api/json` (`busyExecutors`), plus Drone's build list. **N = 4 consecutive idle checks (~20 minutes)** before stopping — long enough that a gap between pipeline stages never trips it. Immediately before `StopInstances` it re-checks once more, which is the answer to §2's "what happens to a build that starts during the shutdown window": the window is closed by a fresh read, not by the age of an old one.

The reaper needs Jenkins' admin password, so its role gets `ssm:GetParameter` on that **one** parameter. Note this is a *separate identity* from the instance profile — it narrows rather than widens the picture T-005 is worried about.

### Ruling 3 — Function URL: `NONE` + HMAC, because GitHub cannot sign SigV4

**Ruling:** `authorization_type = "NONE"` is not a shortcut here, it is the only option — GitHub webhooks cannot produce SigV4. The authentication is therefore entirely in the handler and is **mandatory**: validate `X-Hub-Signature-256` (HMAC-SHA256 over the raw body) with a constant-time compare against a secret from SSM, reject anything that is not a `POST`, and ignore payloads whose repository is not on a small allowlist. Anything failing returns 401/403 and **starts no instance**.

IAM: `ec2:StartInstances`/`ec2:StopInstances` scoped by resource ARN to `i-073e5284ca2a1ceed` only — never `Resource: "*"` — and no `TerminateInstances`, `ModifyInstanceAttribute`, or `RunInstances` anywhere in the policy.

### Ruling 4 — the webhook secret does not exist yet, and this task creates it

**Found during refinement:** nothing in `cv-infra` defines a GitHub webhook secret. [T-005](T-005-ci-secret-blast-radius.md) lists adding one under "also worth doing here" and it was never built, so ruling 3 currently has nothing to validate against.

**Ruling:** this task introduces it — a new `SecureString` SSM parameter plus a new manual step in `ci.tf`'s header list (set the same value in each GitHub webhook). It is genuinely this task's dependency rather than scope creep: without it the Function URL is the cost-DoS endpoint the security note describes. **T-005 should drop that bullet** rather than build it twice.

### Ruling 5 — `user_data` headroom is 588 bytes, and ruling 1 spends some of it

Measured 2026-08-19: `drone-user-data.sh` + `jenkins-provision.sh` render to **15,796 B of EC2's 16,384** — **96.4%**, tighter than the 95.7% [T-009](T-009-user-data-size-ceiling.md) recorded. Ruling 1's two trigger blocks cost roughly 120 B, taking it to ~97.1%.

**Ruling:** it fits, but **measure the real render before applying and record the figure in the PR**. If it does not fit, **do T-009 first** — do not trim explanatory comments again, which is the toll T-009 exists to stop paying. Everything else this task builds (Lambda, IAM, schedule, Function URL) lives outside `user_data` and costs nothing against this limit.

### Ruling 6 — the GitHub webhooks must be re-pointed by hand, and nothing works until they are

The hooks currently point at the EIP (`ci.tf` header, manual step 5). While the box is stopped, **that endpoint answers nothing and GitHub simply records a failed delivery** — which is why a doorbell has to live somewhere always-on.

**Ruling:** the webhooks move to the Function URL, as a manual step added to `ci.tf`'s existing list. Sequence: apply → re-point the hooks → verify with a real push. Until the re-point happens the automation is inert, and that is invisible from Terraform — so it belongs in the acceptance criteria, not in a comment.

### Ruling 7 — start the box by hand now; do not wait for this task

~~M2's backend wave is blocked today (T-102/T-103/T-104 all require Jenkins green). This task will take an apply and a verification cycle. **Start the instance manually in the meantime** — the automation's job is to stop it again afterwards, and nothing here depends on it having stayed off.~~ **Stale, struck 2026-08-20.** The apply landed on 2026-08-19 and the webhooks are re-pointed, so nothing needs starting by hand: a push to `cv-domain-service` or `cv-database` now wakes the box by itself. M2's backend wave is **unblocked**.

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
