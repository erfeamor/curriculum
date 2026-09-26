---
id: T-034
title: "Release the CI host's fixed public IP — it bills $3.64/month while the box is stopped, a sixth of the whole account"
repo: cv-infra
status: todo
owner:
branch: chore/release-ci-host-eip
pr:
depends_on: [T-007]   # SERIALIZATION, not file-level: cv-infra is one root module with local state, so its applies run one at a time; T-007 replaces the CI host first (AMI swap + disk shrink), and this task then changes how that host is addressed
risk: normal
security_review: true   # changes the CI host's public addressing and the GitHub webhook / Drone OAuth callback targets — adapter §5 network-exposure and CI-config paths
---

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
