---
id: T-042
title: "The doorbell wakes the CI host for events with nothing to build — branch deletions and non-build PR actions (widened at H1)"
repo: cv-infra
status: in_progress
owner: tech-product-owner
branch: fix/doorbell-skip-deleted-refs
pr:
depends_on: [T-034]
risk: low
security_review: false   # narrows what the doorbell acts on; the HMAC check and allowlist are untouched
checkpoint:
  stage: implement   # H1 decided 2026-10-01 (below); human /usage 40–75% → checkpoint BEFORE the live apply
  repo: cv-infra
  branch: fix/doorbell-skip-deleted-refs
  worktree: none   # main cv-infra checkout
  commit:
  pr:
  developer: infrastructure-engineer
  reviewers: [code-review]
  risk: low
  security_review: false
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a   # live Lambda + CI host
  updated: 2026-10-01T01:35:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 0
    spawns: 0
    status: ok   # human-reported /usage 40–75%
    checked: 2026-10-01T01:35:00+02:00
---

## H1 — decided by the human, 2026-10-01

Refinement found the same waste one step wider: the doorbell's synchronous path wakes the host for **every** `pull_request` action (closed, labeled, edited, assigned, review_requested…). Drone and Jenkins build only on opened/synchronize/reopened, and a merge-close is covered by the merge's own push to master.

1. **Scope widened:** skip (answer **202 "ignored: <reason>"**, log it, never start the host) a verified, allowlisted `push` with `"deleted": true` (branches and tags), and a `pull_request` whose `action` is not in **{opened, synchronize, reopened, ready_for_review}**. The skip sits after the HMAC and allowlist checks, which stay unchanged; `ping` is unchanged; the redelivery path for real pushes is unchanged.
2. **Red-first unit tests:** a deletion payload and a non-build PR action don't start the host or schedule the async task; a normal push and an `opened` PR still do.
3. **Live proof:** host stopped → delete a throwaway `cv-admin-react` branch → no `StartInstances` (CloudTrail eu-west-3) and an "ignored" doorbell log; then push a fresh branch → the host still wakes and redelivers; delete that branch (skipped), then stop. The PR-action skip is proven by unit tests only.
4. **Budget:** `/usage` 40–75% → implement and review, **checkpoint before the live apply**.

## Why

Found 2026-09-30 during [T-034](T-034-release-ci-host-idle-eip.md) phase 2's cold-start tests. Deleting the throwaway branch `ci/cold-start-test-2` on `cv-admin-react` at ~21:43Z sent a GitHub `push` event with `"deleted": true`. The doorbell treated it as a push, started the stopped CI host, and ran the full wake-and-redeliver task, with nothing to build. The host then sat idle until someone stopped it (at least the reaper's 15-minute post-start grace, ~$0.01 each time). The same applies to the Jenkins repos, whose hooks also point at the doorbell.

Workaround in use: delete branches only while the host is already up, so the doorbell sees "already running".

## Scope

- In `lambda/ci_doorbell/index.py`, answer a verified `push` event whose payload has `"deleted": true` (or `after` = forty zeros) with 2xx and **don't** start the host. Log it.
- A red-first unit test with a real deletion payload shape, plus one showing a normal push still wakes the host.

## Acceptance criteria

- [ ] A branch deletion on `cv-admin-react` while the host is stopped leaves it stopped (live check, CloudTrail shows no `StartInstances`).
- [ ] A normal push still wakes it (the existing cold-start path, unchanged).
