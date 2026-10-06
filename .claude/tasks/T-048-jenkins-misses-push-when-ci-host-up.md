---
id: T-048
title: "A push to a Jenkins repo while the CI host is already running never reaches Jenkins — the doorbell says 'already running; nothing to do'"
repo: cv-infra
status: in_review
owner: tech-product-owner
branch: fix/jenkins-push-when-host-up
pr: https://github.com/erfeamor/cv-infra/pull/38
depends_on: []
risk: normal   # Lambda code only (doorbell + reaper) plus an ignore_changes tag
security_review: true   # webhook targets / doorbell behaviour on the CI host — adapter §5 CI-config path
checkpoint:
  stage: h2   # applied 2026-10-06 (Lambdas + doorbell IAM); both paths proven live; awaiting human acceptance
  repo: cv-infra
  branch: fix/jenkins-push-when-host-up
  worktree: none
  commit: 2f34b12
  pr: https://github.com/erfeamor/cv-infra/pull/38
  developer: infrastructure-engineer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a   # live Lambdas + CI host
  updated: 2026-10-06T11:30:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 72636
    spawns: 1   # infrastructure-engineer (fresh)
    status: ok   # human-reported /usage under ~40% (2026-10-06, new window)
    checked: 2026-10-06T11:30:00+02:00
---

## Implement, review and live proof — 2026-10-06 (2f34b12, cv-infra#38)

- **Developer** (fresh infrastructure-engineer, ~73k tokens): doorbell `_mark_push_on_running_host` (a Jenkins repo + `running`/`pending` → `create_tags CILastPush=<UTC>`, best-effort, responses unchanged); reaper `within_push_grace` (after keepalive and post-start; a malformed **or future-dated** tag ignored with a warning); IAM `ec2:CreateTags` on the CI instance ARN only with `ForAllValues:StringEquals aws:TagKeys=[CILastPush]`; env `PUSH_TAG` on both Lambdas, `PUSH_GRACE_MINUTES = 10`; `ignore_changes += CILastPush`. Red first → 96 Lambda tests and `terraform test` 25/25 (18 s); check-static 4 + new 19 (mutation-checked).
- Driver-verified; **review round 1 (code + security): clean.** Applied: **0 added, 3 changed** (both Lambdas, the doorbell policy).
- **Live, host up past its post-start grace** (started 16:56:55 with CIKeepAlive, removed at 17:15): push to `ci/t048-proof` 17:15:14Z → the doorbell **tagged `CILastPush=2026-10-06T17:15:16Z`** (and still answered "already running") → the reaper at **17:17:27: "within 10-minute push grace … leaving instance running"** (the run that used to stop it) → Jenkins' scan `branch=pending` 17:18:55 → **`success` 17:19:57** (4 m 43 s after the push).
- **Regression, host stopped:** push 17:20:49Z → **the doorbell started the host at 17:20:52** → Jenkins built on boot → **`success` 17:25:00**.
- Cleanup: the throwaway branch deleted, the host stopped (the record flipped to `192.0.2.1`). The `CILastPush` tag remains on the instance and the branch still plans **No changes** (the ignore_changes works).

## Stage 0 — 2026-10-06: the root cause is a race, not a missing mechanism

- **Jenkins already scans every 5 minutes**: both multibranch jobs carry `periodicFolderTrigger { interval('5m') }` (`templates/jenkins-provision.sh`), and the CI host has the `github` + `github-branch-source` plugins.
- **The race, from CloudTrail + the reaper's log:** 10:01:43 the doorbell started the host (the PR build); **10:23:45** the master push, and the doorbell no-ops ("already running"); **10:27:29 the reaper stopped the host** (idle executor, quiet CPU, past its 15-min post-start grace), **3 m 44 s after the push, before the next 5-min scan**. The reaper runs every 5 minutes (`rate(5 minutes)`).
- So nothing tells the reaper a push is pending a scan.

## H1 — decided by the human, 2026-10-06

**The doorbell marks the push; the reaper waits.**
1. **Doorbell** (`lambda/ci_doorbell/index.py`): for a verified, allowlisted, buildable push or PR event on a **Jenkins repo** (not in `REDELIVER_REPOS`) when the instance is already **running** (or pending), tag the instance `CILastPush=<ISO-8601 UTC>` (`ec2:CreateTags` on that instance only, for that tag key only, e.g. via `aws:TagKeys`), then answer as today. A tagging failure is logged and must not fail the webhook.
2. **Reaper** (`lambda/ci_reaper/index.py`): don't stop the host while `now − CILastPush < 10 min` (a `PUSH_GRACE_MINUTES` env var, default 10, wired in Terraform with an assertion), alongside the existing post-start grace. Log the reason.
3. **Terraform:** `CILastPush` joins `CIKeepAlive` in `aws_instance.drone`'s `ignore_changes` (`tags["CILastPush"]`, `tags_all["CILastPush"]`), so no drift; the IAM grants scoped as above; tests.
4. **Unit tests** for both Lambdas (red first): a running host + Jenkins push → tagged; a stopped host → the existing wake path, no tag needed; the reaper within/after the window; a malformed tag → ignored, not a crash.
5. **Live proof:** with the host up and idle past its grace, push to a throwaway branch on cv-domain-service → the doorbell tags → the reaper logs "within push grace" → Jenkins scans and builds within ~5 min → the reaper stops the host only after it's idle again. Then a push with the host **stopped** still wakes it (no regression).
6. **Budget:** H1 recorded at 75% usage; implementation starts in a fresh window.

## Why this exists

Found live on 2026-10-06 while merging [T-112](T-112-domain-service-ci-ecr-deploy.md) (cv-domain-service#17 → master f487615 at 10:23:43Z):

- The CI host was **already running** (woken at 10:01 for the PR's Jenkins build).
- 10:23:45Z, the doorbell log: `i-0ee24b3d917501c4d already running for erfeamor/cv-domain-service; nothing to do`.
- **Jenkins never built master:** the Jenkins repos' only GitHub webhook points at the doorbell, and Jenkins discovers changes by **scanning when the host starts**. A push that arrives while the host is up is therefore invisible to Jenkins. The reaper then stopped the idle host.
- T-112's `wait-for-jenkins` kept waiting for a status that would never come. The driver unblocked it by starting the CI host by hand (Jenkins scans on boot).

This affects **every** Jenkins-built push (cv-domain-service, cv-database) that lands while the host is up, which is likely during any busy session. Since T-112, it also silently blocks domain-service deploys until the 30-minute wait expires.

## Options (decide at H1)

1. **A second GitHub webhook on each Jenkins repo** → `https://ci.erfeamor.com/jenkins/github-webhook/`, beside the doorbell hook (the cv-admin-react pattern: Drone hook + doorbell hook). When the host is up, Jenkins gets the push directly; when it's down, that delivery fails and the doorbell's wake + scan-on-boot covers it. Needs Jenkins' GitHub-hook trigger configured (JCasC) and the hook's secret; possibly the doorbell's redelivery extended to the Jenkins repos.
2. **The doorbell triggers a Jenkins scan when the host is already running** (call Jenkins' multibranch scan API with credentials from SSM). Keeps a single hook, but the doorbell now needs Jenkins credentials.
3. **A periodic multibranch scan** (e.g. every 5 min) while the host is up. The simplest, but adds latency and isn't event-driven.

## Acceptance criteria

- [x] A push to cv-domain-service **while the CI host is up** gets a Jenkins build and a commit status within a few minutes (proven live).
- [x] A push while the host is **stopped** still wakes it and builds (no regression).
- [x] T-112's deploy chain works for a master push in both cases.
