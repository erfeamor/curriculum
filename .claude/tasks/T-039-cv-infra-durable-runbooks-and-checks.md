---
id: T-039
title: "cv-infra: turn the task-named T-007/T-008 runbooks and check scripts into durable, task-neutral ones"
repo: cv-infra
status: in_review
owner: tech-product-owner
branch: chore/durable-runbooks-and-checks
pr: https://github.com/erfeamor/cv-infra/pull/25
depends_on: [T-007, T-008]
risk: normal
security_review: false   # docs and offline check scripts only; A1 re-checks the real diff
---

## Why

Raised by the human at T-007's H2 (2026-09-29). T-007 and T-008 left **task-numbered** artifacts in cv-infra that mix durable procedure with one-off history:

| File | Durable part | One-off/history part |
|---|---|---|
| `scripts/check-t008-static.sh` | Checks that no output leaks the deploy key and that the Lambdas read only their specific SSM ARNs | The policy **hash pin**, which any legitimate policy change has to update |
| `scripts/check-t007-static.sh` | Checks that `ignore_changes` keeps `ami`/`CIKeepAlive`, the Lambda `INSTANCE_ID` wiring, the DB secret on every drone-server run, and the cloud-init wait's placement | — |
| `docs/drone-host-backup-and-cutover.md` | Drone rebuild and deploy-key rotation | The "rehearsal" narrative and review-round asides |
| `docs/t007-ci-host-replace-runbook.md` | Replacing the CI host (AMI bumps, resizes), the `CIKeepAlive` pause, post-replace checks | The encryption transition, first-apply-only resources, review-round asides |

History already lives in the task files and PR descriptions. The repo should carry only current procedure and the checks that protect it.

## Scope

- **One `scripts/check-static.sh`** covering both scripts' invariants, sourcing `scripts/lib/extract-block.sh`. Replace the policy hash pin with a semantic check (the policy's actions and resources), or drop it and justify why.
- **`docs/runbooks/drone.md`:** rebuild and key rotation.
- **`docs/runbooks/ci-host-replace.md`:** a generalised replace procedure.
- Delete the old files, update every reference (CLAUDE.md gate list, README, template comments), and keep `drone-reseed-secrets.sh` and its tests unchanged.

## Acceptance criteria

- [x] No task-numbered file names remain under `cv-infra/scripts` or `cv-infra/docs`.
- [x] Each invariant from both old scripts is still enforced, shown by a red-first mutation per check.
- [x] Both runbooks are task-neutral: no review-round or "rehearsal" narrative, and each step is valid for the *next* use.
- [x] `terraform fmt`, `validate` (`-backend=false`), `terraform test`, `check-static.sh`, `bootstrap/check-static.sh` and the reseed harness all pass. CLAUDE.md's gate list names the new script.

## Provenance

Filed by the driver at T-007's H2, 2026-09-29, on the human's instruction ("merge #24, then follow-up task").

## Implementation — 2026-09-29 (outside the dev loop, on the human's instruction: docs and scripts only, with the premise and H1 already settled at T-007's H2)

[cv-infra#25](https://github.com/erfeamor/cv-infra/pull/25):
- **`scripts/check-static.sh`** holds all 7 invariants. The policy hash pin is now a **semantic least-privilege check**.
- **`docs/runbooks/drone.md`** and **`docs/runbooks/ci-host-replace.md`** are written from what worked live.
- **Evidence:** 8 mutations in scratch copies, each red with the right message. The full offline gate is green, and the real `terraform plan` shows **No changes**.
- **Known leftover:** `templates/jenkins-provision.sh` still names the old script in two comments. Editing even a comment there re-provisions Jenkins on the live host, so those references ride that template's next real change.
