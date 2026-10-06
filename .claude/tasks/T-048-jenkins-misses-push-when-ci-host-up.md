---
id: T-048
title: "A push to a Jenkins repo while the CI host is already running never reaches Jenkins — the doorbell says 'already running; nothing to do'"
repo: cv-infra
status: in_progress
owner: tech-product-owner
branch: fix/jenkins-push-when-host-up
pr:
depends_on: []
risk: normal   # Lambda code only (doorbell + reaper) plus an ignore_changes tag
security_review: true   # webhook targets / doorbell behaviour on the CI host — adapter §5 CI-config path
checkpoint:
  stage: implement   # stage 0 + H1 done 2026-10-06 (the human at 75% usage); implementation starts in a fresh window
  repo: cv-infra
  branch: fix/jenkins-push-when-host-up
  worktree: none
  commit:
  pr:
  developer: infrastructure-engineer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a   # live Lambdas + CI host
  updated: 2026-10-06T11:30:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 0
    spawns: 0
    status: soft   # the human reported 75% usage: H1 only this window
    checked: 2026-10-06T11:30:00+02:00
---

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

- [ ] A push to cv-domain-service **while the CI host is up** gets a Jenkins build and a commit status within a few minutes (proven live).
- [ ] A push while the host is **stopped** still wakes it and builds (no regression).
- [ ] T-112's deploy chain works for a master push in both cases.
