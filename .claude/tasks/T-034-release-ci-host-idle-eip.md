---
id: T-034
title: "Release the CI host's fixed public IP — it bills $3.64/month while the box is stopped, a sixth of the whole account"
repo: cv-infra
status: in_progress
owner: tech-product-owner
branch: chore/release-ci-host-eip
pr:
depends_on: [T-007]   # SERIALIZATION, not file-level: cv-infra is one root module with local state, so its applies run one at a time; T-007 replaces the CI host first (AMI swap + disk shrink), and this task then changes how that host is addressed
risk: normal
security_review: true   # changes the CI host's public addressing and the GitHub webhook / Drone OAuth callback targets — adapter §5 network-exposure and CI-config paths
checkpoint:
  stage: review   # phase 1 r1: /code-review high 10 findings (incl. SECURITY: public InvokeFunction grant lets any AWS principal reach the async path) — fixes with the developer; branch feat/ci-doorbell-drone-redelivery @0567f6a
  repo: cv-infra
  branch: feat/ci-doorbell-drone-redelivery
  worktree: none   # main cv-infra checkout
  pr:
  developer: infrastructure-engineer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true   # new token, IAM, a public Function URL path
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a
  updated: 2026-09-29T12:30:00+02:00
  budget:
    turns: 20   # session 4, --since 2026-09-29T09:28:39.000Z
    total_tokens: 12000000
    subagent_tokens: 0
    spawns: 2   # quality-assurance (plan) + infrastructure-engineer
    status: ok
    checked: 2026-09-29T12:30:00+02:00
---

## H1 — decided by the human, 2026-09-29 (session 4); phase 2 waits on a domain

- **Drone cold start: the doorbell relays.** `cv-admin-react`'s webhook moves to the doorbell Function URL, which already verifies the HMAC and checks the allowlist. It starts the host, waits for Drone's `/healthz`, and **replays the exact body and headers** to Drone, so Drone's own signature check passes.
- **Reaper:** a **post-start grace** (no stop within about 15 minutes of launch) and a **Drone busy check** (running or pending builds from Drone's API), alongside the Jenkins and CPU checks.
- **EIP: design 1, release it.** The human registers a **domain** (their action, a real purchase). Then a Route 53 hosted zone, and a **DNS-on-boot updater** whose IAM grant is **scoped to one record name** (`route53:ChangeResourceRecordSetsNormalizedRecordNames`), because the CI role is reachable from builds (the T-005 gap). Then the EIP is released.
- **TLS is folded in (T-033 option b, via Let's Encrypt on the host):** `ci-proxy` gets a Let's Encrypt certificate for the CI hostname (HTTP-01, renewed when the host is up). `DRONE_SERVER_HOST`/`PROTO`, the GitHub OAuth callback and the webhooks are re-pointed to `https://<ci-hostname>`.
- **Phasing:** phase 1 (the relay and the reaper) needs no domain. Phase 2 (the zone, updater, EIP release and TLS) **waits for the human's domain**.

**H1 correction, same day, decided by the human: the relay is GitHub REDELIVERY, not a forward.** Checking the design against GitHub and Drone found two constraints. **GitHub times out a webhook after 10 seconds**, so the doorbell must answer at once and work asynchronously. **Drone verifies each webhook against a per-repo secret only it knows**, so a doorbell-signed delivery replayed to Drone would be rejected.

- **Design:** keep Drone's own hook, and add a second, **doorbell-signed** hook on `cv-admin-react`. The doorbell returns 202 at once, then asynchronously starts the host, waits for Drone's `/healthz`, and calls GitHub's **redeliver** API for the Drone hook's failed deliveries since the wake. Signatures stay intact end to end.
- **The token this needs is created by the human:** a **fine-grained token limited to `erfeamor/cv-admin-react`, Webhooks read/write only**. It goes into `terraform.tfvars`, and Terraform stores it as an SSM SecureString **outside `ci/*`**, readable only by the doorbell Lambda. The existing CI token was checked and **can't** manage webhooks (403, `repository_hooks=read` required).

**Phase-1 PO settlements, accepted at H1 confirm:**
- **Reaper:** a 15-minute post-start grace. **No Drone queue signal (deferred):** reading it needs a Drone token or public metrics, and CPU already sees Drone's npm builds.
- **Healthz ceiling:** 8 minutes, then skip and log; the runbook documents manual redelivery.
- The token is at `/cv-project/dev/doorbell/github-hooks-token`.


## Why this exists

Filed 2026-09-24 from the cost review that led to [T-012](T-012-aws-endgame-decision.md)'s decision **A (go Paid, with the stack trimmed)**. Cost Explorer, 2026-08-24 → 09-23:

| Usage type | $/month | Share |
|---|---|---|
| `EUW3-PublicIPv4:IdleAddress` | **3.64** | **17%** |

That line is `13.39.59.12`, the Elastic IP on `cv-project-drone`. The host has been stopped almost all month (2.3 hours of builds), and an EIP on a stopped instance bills as *idle* — **$3.64/month for an address used about 0.3% of the time.** It is the largest single saving available (see the savings table in T-012's decision record).

## Why it is not a one-line change

The EIP is load-bearing ([T-012](T-012-aws-endgame-decision.md) § A says so in terms): the GitHub webhooks and Drone's OAuth callback are registered against it. With on-demand start ([T-019](T-019-ci-host-on-demand.md)), an instance without an EIP gets a **different public IP on every start**, so anything that addresses the box by IP breaks.

Candidate designs — **decide at H1, do not assume:**
1. **A DNS name updated on boot** (a record the host rewrites at start via its instance role). Costs a hosted zone (~$0.50/month) unless an existing zone is reused. [T-033](T-033-ci-host-tls.md) needs a DNS name for TLS anyway, so this is also its prerequisite.
2. **Route the webhook through T-019's start-on-push front door** and address the host only through it. Read T-019 to see what already receives GitHub's webhook before designing anything new.
3. **Keep the EIP** and record why. A legitimate outcome if 1 and 2 cost more attention than $3.64/month is worth — write the number down.

## Scope

- Choose and implement one design; remove `aws_eip` for the CI host if 1 or 2 is chosen.
- Re-register whatever pointed at the old IP (GitHub webhooks on the Jenkins/Drone repos, Drone's `DRONE_SERVER_HOST` and GitHub OAuth app callback) — **list every consumer before changing anything**; the Drone EIP has consumers outside Terraform.

## Added scope 2026-09-25 — wire Drone to the doorbell (was owned by nobody)

**The cold-start AC below cannot pass today, whatever design is chosen.** `cv-admin-react`'s Drone webhook still targets the raw EIP (`http://13.39.59.12/hook`), and Drone is **not wired to [T-019](T-019-ci-host-on-demand.md)'s doorbell**: only `cv-domain-service` and `cv-database` were re-pointed. So a push to `cv-admin-react` neither builds nor wakes the stopped host (T-019 ruling 5; the warning sits in [T-301](T-301-admin-cv-sections-crud.md)). This task already re-registers every webhook that points at the old IP, so the Drone path belongs here and not in a new task:
- Route `cv-admin-react`'s GitHub webhook through the doorbell (or whatever front door the chosen design uses), so a push **wakes the host and then reaches Drone**.
- Record the result in T-301, whose "CI green" definition of done depends on it.

Also: **settle [T-033](T-033-ci-host-tls.md)'s TLS decision at this task's H1**. Design 1's DNS name is its option (b)'s prerequisite, with the same hosted zone.

## Acceptance criteria

- [ ] A push to `cv-admin-react` **while the host is stopped** wakes it and produces a green Drone build (added 2026-09-25, see above).
- [ ] Every consumer of `13.39.59.12` enumerated in the PR (in Terraform and outside it).
- [ ] A cold start from stopped: a push to a Jenkins repo and to `cv-admin-react` (Drone) both trigger builds that go green, **after** a stop/start cycle has changed the public IP.
- [ ] Drone's GitHub login still works after the same cycle.
- [ ] `aws ec2 describe-addresses` shows no idle address on the CI host — or, under design 3, the decision recorded with its cost.
- [ ] The saving recorded against [T-020](T-020-cost-model-correction.md)'s model.

## Watch-outs

- **Serialize with every other cv-infra apply** (T-007 before, T-014 after) — one root module, local state; a merged-but-unapplied change rides the next apply of any task.
- **Couples with [T-033](T-033-ci-host-tls.md)** (TLS needs a stable name) — if design 1 is chosen, say whether T-033 now builds on it.
- Verification needs the CI host started, at ~$1.23/day while up — keep the window short.

## dev-loop notes

- **Developer:** `infrastructure-engineer`. **Reviewers:** `/code-review` + `/security-review` (network exposure, CI config).
- ⚖ Only worth doing because T-012 chose **A**; under B or C this saving would not outlive the stack.

## Finding 2026-09-27 — the reaper has no post-start grace, and cannot see Drone

Observed during [T-301](T-301-admin-cv-sections-crud.md)'s stage 3:
- **~00:45Z:** the driver started the CI host by hand (the lane's T-301 workaround).
- **00:49:04Z:** the push reached Drone, and builds #33/#34 were queued.
- **00:49:15Z:** the reaper logged `cpu quiet: peak 7.5% over 20 min across 1 datapoints`.
- **00:49:18Z:** it stopped the host. The builds sat at `pending` with the host down.

Two gaps:
1. **No grace after a start.** A single post-boot CloudWatch datapoint (low boot CPU) counts as "20 idle minutes". The same stop happened at 00:34 after T-114's Jenkins build, where it was correct.
2. **Drone activity is invisible.** The reaper checks the Jenkins executor and CPU, and has no view of Drone's queue or running builds. A Jenkins doorbell start is covered by the busy executor; a Drone build is covered only by CPU.

**Add to this task's scope** (it already owns wiring Drone to the doorbell): a minimum uptime after any start (e.g. ≥ 20 min of datapoints before "idle" can be true), and a Drone busy check (the Drone API's running/pending builds) beside the Jenkins one. The cold-start AC for `cv-admin-react` cannot pass reliably without both.
