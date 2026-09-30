---
id: T-042
title: "The doorbell wakes the CI host for branch deletions — a push event with nothing to build"
repo: cv-infra
status: todo
owner:
branch: fix/doorbell-skip-deleted-refs
pr:
depends_on: [T-034]
risk: low
security_review: false   # narrows what the doorbell acts on; the HMAC check and allowlist are untouched
---

## Why

Found 2026-09-30 during [T-034](T-034-release-ci-host-idle-eip.md) phase 2's cold-start tests. Deleting the throwaway branch `ci/cold-start-test-2` on `cv-admin-react` at ~21:43Z sent a GitHub `push` event with `"deleted": true`. The doorbell treated it as a push, started the stopped CI host, and ran the full wake-and-redeliver task, with nothing to build. The host then sat idle until someone stopped it (at least the reaper's 15-minute post-start grace, ~$0.01 each time). The same applies to the Jenkins repos, whose hooks also point at the doorbell.

Workaround in use: delete branches only while the host is already up, so the doorbell sees "already running".

## Scope

- In `lambda/ci_doorbell/index.py`, answer a verified `push` event whose payload has `"deleted": true` (or `after` = forty zeros) with 2xx and **don't** start the host. Log it.
- A red-first unit test with a real deletion payload shape, plus one showing a normal push still wakes the host.

## Acceptance criteria

- [ ] A branch deletion on `cv-admin-react` while the host is stopped leaves it stopped (live check, CloudTrail shows no `StartInstances`).
- [ ] A normal push still wakes it (the existing cold-start path, unchanged).
