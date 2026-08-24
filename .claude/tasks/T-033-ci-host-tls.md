---
id: T-033
title: "The CI host serves Jenkins admin login and Drone OAuth over plain HTTP on a scanned public IP"
repo: cv-infra
status: todo
owner:
branch: feat/ci-host-tls
pr:
depends_on: []
risk: normal
security_review: true   # stage-0 default, and it is not a guess: any implementation touches listener/ingress config and the OAuth callback, both adapter §5 paths. A1 re-checks against the real diff.
---

## Why this exists

**Nobody owned this, and it was handed off once.** [T-002](T-002-jenkins-on-drone-host.md)'s `/security-review` recorded the CI host under continuous untargeted internet scanning and ended its finding with *"carry to T-005 as an argument for scheduling TLS."* [T-005](T-005-ci-secret-blast-radius.md) never picked it up — its scope is IMDS and parameter-path splitting, and TLS appears nowhere in its acceptance criteria. T-002's own § out-of-scope also names it: *"TLS/ACM in front of Jenkins (the SG already anticipates 443 but Drone runs `DRONE_SERVER_PROTO=http` today — a separate task)."*

**That separate task was never filed.** Found 2026-08-24 in a board review; this file is it. Nothing here is new information — it is the same finding, given an owner and a decision point.

## What is actually exposed

Everything on the CI host is served over plain HTTP on port 80 at a public EIP:

| Credential in flight | Path | Today |
|---|---|---|
| Jenkins admin password | `http://<eip>/jenkins/` form login | **plaintext over the wire** |
| Drone OAuth flow | `http://<eip>/login` → GitHub → callback | `DRONE_SERVER_PROTO=http` |
| GitHub webhook deliveries | `http://<eip>/hook`, `http://<eip>/jenkins/github-webhook/` | HMAC-signed (T-019 ruling 4) but unencrypted |

And the environment it sits in, measured rather than assumed — from T-002's proxy-log review of 1,161 lines:

- Steady untargeted scanning from multiple sources (117 requests from one host, 98 from another, 85 from a third).
- **Raw TLS ClientHello bytes being sent to the plain-HTTP :80 listener** — i.e. scanners are already probing this IP expecting TLS.
- Vulnerability probes (`/geoserver/web/` and similar).

**Be precise about the severity, because T-002 already was.** Nothing is *reachable* that should not be: Jenkins returns 403 to anonymous callers on every path, `:8080`/`:50000` are refused at both the SG and host layers, and Drone is gated by OAuth plus `DRONE_USER_FILTER`. The 200 on `/geoserver/web/` is Drone's SPA catch-all, not a leak. **The exposure is confidentiality in transit, not an open door** — an attacker positioned on the network path, not merely scanning it, can read the Jenkins admin password as it is submitted. On a single-developer demo the practical likelihood is low; the point of this task is that "low" should be a recorded decision rather than an unexamined default.

## The decision this task exists to take — settle at H1, do not improvise

**A public CA certificate cannot be issued for a bare IP address.** That is the whole reason this has no obvious implementation, and it is why it must be decided rather than assumed:

| Option | What it costs | What it breaks |
|---|---|---|
| **(a) Accept the risk, record it, close this task** | Nothing | Nothing. A legitimate outcome — say so explicitly and give the reasoning, per the standard [T-004](T-004-terraform-state-hardening.md) §3 sets for rotation decisions. |
| **(b) Domain name + ACM/Let's Encrypt** | A registered domain, a Route 53 hosted zone (~$0.50/mo), plus registration — **real money against a finite credit pot**, see [T-012](T-012-aws-endgame-decision.md) | Both GitHub webhooks and the Drone OAuth callback are registered against the **EIP** and must be re-pointed; `DRONE_SERVER_PROTO` must move to `https` or the callback breaks |
| **(c) CloudFront in front of the CI host** | Distribution config; reuses the existing pattern | Same webhook/callback re-point; adds an origin the prefix-list work in [T-025](T-025-verify-requests-come-from-our-cloudfront.md) would then also want to cover |
| **(d) Self-signed certificate** | Nothing | **Rejected up front:** GitHub will not deliver webhooks to an untrusted certificate, so it trades a confidentiality gap for a broken CI trigger. Recorded so it is not rediscovered as an idea. |

**The cost question is the sharp edge.** Option (b) is the textbook answer and it spends real credits on a demo whose runway is already the subject of a dated decision (T-012, due **2026-11-01**). A reviewer who reaches for "just add TLS" without pricing it against the runway is making T-012's decision by accident. If the answer is (a), this task closes having produced a recorded decision — which is the same outcome T-010 reached on trimming, and it was the right one there.

## Coordination — not dependencies

- **[T-005](T-005-ci-secret-blast-radius.md)** touches the same instance's network surface (`metadata_options`, IAM). No shared acceptance criterion, but if both are in flight, sequence them so two applies do not race on one box. **This task does not gate T-005 and T-005 does not gate this.**
- **[T-012](T-012-aws-endgame-decision.md)** — if option (b) or (c) is chosen, its recurring cost belongs in T-012's model rather than being absorbed silently.
- **[T-019](T-019-ci-host-on-demand.md)** — the host is stopped most of the time, which reduces the exposure *window* but not the exposure: the credentials cross the wire precisely when someone is using it.

## Acceptance criteria

- [ ] A decision is recorded — (a), (b) or (c) — **with its reasoning and its recurring cost**, whichever way it goes. "Accept" is a valid outcome and must be written down as a decision, not left as a silence.
- [ ] If the decision is **accept**: T-002's `scanning_note` and this file both point at the recorded decision, so the finding is closed rather than re-raised by the next reviewer who reads the proxy log.
- [ ] If the decision is **implement**: Jenkins login and the Drone UI are served over TLS; `DRONE_SERVER_PROTO=https`; **both GitHub webhooks re-registered** and a delivery verified `200` afterwards — the webhook re-point is the step most likely to be forgotten, and [T-019](T-019-ci-host-on-demand.md) ruling 5 already records one webhook left pointing at a stale target for days.
- [ ] If implemented: the OAuth login flow is re-tested end to end (`/login` → GitHub → callback), per T-002's own §3a warning that a proxy change can mangle `Host` or the path prefix.
- [ ] `terraform fmt -check -recursive`, `terraform validate`, `terraform test` pass; `/security-review` clean.

## Definition of done

Either a PR from `feat/ci-host-tls` with TLS applied and both webhooks verified, **or** this task closed with the accept-the-risk decision and its reasoning recorded here. Both are complete outcomes.

## dev-loop notes

- **Developer:** `infrastructure-engineer`. **Reviewers:** `/code-review` + `/security-review` (adapter §5 — ingress and an auth callback).
- **`risk: normal`, not `high`** — nothing is currently reachable that should not be (T-002 verified this), so this is transport hardening rather than closing an open door. It is **not** `trivial`: the option-(b)/(c) paths re-point live webhooks and an OAuth callback on the box that gates two repos' CI.
- **H1 must produce a decision, not a survey.** Every option above is priced; refinement picks one and records why the others lost.

## Provenance

Filed 2026-08-24 from a board review. The finding is [T-002](T-002-jenkins-on-drone-host.md)'s (`checkpoint.security_review.scanning_note`, 2026-08-13), handed to [T-005](T-005-ci-secret-blast-radius.md) in prose and never absorbed into its acceptance criteria — the same lost-hand-off shape the 2026-08-17 sweep filed four tasks for, and the reason board rule 3 exists. Filed as its own task rather than widened into T-005 because TLS is not in T-005's acceptance criteria and adding it there would repeat the error, not fix it.
