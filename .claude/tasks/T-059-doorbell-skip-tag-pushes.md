---
id: T-059
title: "Doorbell: ignore tag pushes, so a release tag doesn't wake the CI host"
repo: cv-infra
status: todo
owner:
branch: fix/doorbell-skip-tag-pushes
pr:
depends_on: [T-504]
risk: normal   # Lambda logic + terraform apply of the doorbell function
security_review: true   # the doorbell is the CI host's public entry point
---

## Why

Filed at [T-504](T-504-m2-release-tag-all-repos.md)'s H1 (2026-11-03). The doorbell skips deleted refs and non-build PR actions (T-042), but a **new** tag is a `push` with `ref: refs/tags/…`, so it starts the CI host. Nothing builds a tag:
- Drone triggers only on `push` and `pull_request` (a tag push is Drone's `tag` event).
- Both Jenkins jobs use branch discovery only.

The host therefore idles until the reaper stops it, about 35 minutes and ~$0.02. T-504 accepted that one wake for `M2`; this fixes it before `M3`.

## Scope

- In `lambda/ci_doorbell/index.py`'s skip logic (beside `deleted ref`), ignore a `push` whose `ref` starts with `refs/tags/`, before both wake paths. Keep the log line and the `202 ignored:` response shape.
- Unit tests in `lambda/test_ci_doorbell.py`: a tag push is ignored (no start and no async redelivery), and a branch push still wakes the host.
- Apply, then prove it live by pushing a throwaway **non-`M*`** tag to cv-database (the ruleset makes `M*` tags permanent), confirming the host stays stopped, then deleting the tag.

## Acceptance criteria

- [ ] A tag push returns `202 ignored: tag push` and neither starts the host nor schedules a redelivery.
- [ ] Branch pushes and PR events behave exactly as before (existing tests stay green).
- [ ] Live: a tag push to a doorbell repo leaves the CI host stopped.
