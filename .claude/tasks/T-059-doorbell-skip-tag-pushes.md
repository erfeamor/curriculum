---
id: T-059
title: "Doorbell: ignore tag pushes, so a release tag doesn't wake the CI host"
repo: cv-infra
status: done
owner: tech-product-owner
branch: fix/doorbell-skip-tag-pushes
pr: https://github.com/erfeamor/cv-infra/pull/47
depends_on: [T-504]
risk: normal   # Lambda logic + terraform apply of the doorbell function
security_review: true   # the doorbell is the CI host's public entry point
---

## ✅ DONE 2026-11-06 ([cv-infra#47](https://github.com/erfeamor/cv-infra/pull/47), `c37f836`)

- **Change:** a `push` with a `refs/tags/` ref returns `202 ignored: tag push`, beside T-042's deleted-ref skip. 10 new tests, red first, and the guard was mutation-checked. Gates: fmt, validate, check-static, `terraform test` (28), lambda tests (109).
- **Review:** `/code-review` found nothing. The infrastructure-engineer's `/security-review` found no blockers, plus three nits accepted with no change:
  - a later push's redelivery sweep may re-send a failed Drone *tag* delivery, which is harmless because Drone builds nothing for `tag` events;
  - a future tag-triggered build would be skipped, an assumption the docstring records;
  - `ref` is read for every event type, which is harmless.
- **Apply:** the plan was 1 in-place update (`aws_lambda_function.ci_doorbell`), applied from the branch before merge.
- **Live proof:** at 17:16:58Z `t059-probe` was pushed to cv-database with the CI host stopped. The doorbell logged `ignored: repo=erfeamor/cv-database event=push reason=tag push`, GitHub recorded delivery status `202`, and the host stayed `stopped`. The human deletes the probe tag.

## H1 — approved 2026-11-06

- **Change:** a `push` whose `ref` starts with `refs/tags/` returns `202 ignored: tag push`, beside T-042's `deleted ref` skip (after HMAC and the allowlist, before both wake paths). The driver implements it.
- **Stage 0:** the doorbell's hooks subscribe to `push` and `pull_request` only, so a `create` event never reaches it. Drone's own hook (`create,delete,…`) goes to Drone directly, and Drone doesn't build tags.
- **Review:** `/code-review` plus the infrastructure-engineer running `/security-review` as the specialist lens.
- **Deploy:** `terraform apply`, expected to update only `aws_lambda_function.ci_doorbell` in place. It stays in "ask".
- **Live proof:** push the throwaway tag `t059-probe` (not `M*`) to cv-database with the host stopped, and confirm `ignored: tag push` in the doorbell log and the host still stopped. **The human deletes the tag** afterwards.

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

- [x] A tag push returns `202 ignored: tag push` and neither starts the host nor schedules a redelivery.
- [x] Branch pushes and PR events behave exactly as before (existing tests stay green).
- [x] Live: a tag push to a doorbell repo leaves the CI host stopped.
