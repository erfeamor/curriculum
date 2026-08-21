---
id: T-028
title: "The QA stack builds master, not the worktree under test"
repo: cv-project (meta)
status: todo
owner:
branch: fix/qa-env-worktree-build-context
pr:
depends_on: []
risk: normal          # small diff, but it fails in the direction of a FALSE PASS
security_review: false   # no adapter §5 security path — local tooling only
---

## The defect

`docker-compose.dev.yml:50` builds the domain service from a **fixed relative path**:

```yaml
  domain-service:
    build: ./cv-domain-service
```

`./cv-domain-service` is the **main checkout**, which sits on `master`. But the dev-loop runs every task on a **git worktree** under `~/work/cvdl-worktrees/<task-id>`. So the documented stage-4 bring-up — the exact command the adapter's §6 prints — builds `master` and exercises **none of the code under test**.

`scripts/qa-env-override.py` does not close this. It isolates `COMPOSE_PROJECT_NAME`, host ports and named volumes, which is what it was written for; the build context was simply never part of its model.

## Why this is `normal` and not `trivial`

**It fails toward a false pass.** Two outcomes, and only one is loud:

- The endpoints under test don't exist on `master` → everything 404s → QA reports a false failure and someone burns a bounce-back round chasing it.
- The task **modifies** behaviour that already exists on `master` (a fix, a retrofit, an ordering change) → the stack answers plausibly on every endpoint, the old behaviour passes the old assertions, and **QA signs off on a binary that does not contain the change**. Nothing in the run looks wrong.

The second is the dangerous one and it is the shape of most non-greenfield tasks. [T-105](T-105-experience-ordering-retrofit.md) is precisely it: an ordering retrofit whose endpoints all exist on `master` today and whose stage-4 QA would happily verify the *unretrofitted* order.

## How it was caught, and how nearly it wasn't

T-103's stage-4 run, 2026-08-21. The driver noticed `build: ./cv-domain-service` while preparing the bring-up and added a third compose file by hand:

```yaml
# docker-compose.override.cvdl_t-103.build.yml
services:
  domain-service:
    build: /home/erfeamor/work/cvdl-worktrees/T-103
```

QA then **proved its own provenance** rather than assuming it: `GET /api/v1/skills` answered `200` on bring-up, and that endpoint does not exist on `master` at all, so its presence is positive evidence the right tree was built. That check only works for a **new** resource — T-103 was greenfield and got lucky. A modifying task has no such tell, which is the argument for fixing the generator rather than repeating the manual workaround.

## Scope

1. **Teach `scripts/qa-env-override.py` the build context.** It already takes `--task`; give it the worktree path (derive from the task id, or accept `--worktree`, and fall back to the main checkout when the task is not on a worktree). Emit the `build:` override into the file it already generates — one file, not two.
2. It must handle **any** buildable service, not just `domain-service` — `cv-bff-node` has the identical exposure and the JS/TS tasks (T-201, T-203, T-204) will hit it.
3. **Print a provenance check** alongside the up/down/smoke commands it already prints: something QA can run to prove which tree it built. A commit SHA exposed by the service, or at minimum an instruction to verify rather than assume.
4. Cross-reference from the adapter's §6. **Note the adapter file is gitignored**, so §6 itself cannot be fixed by a PR in this repo — this task's own body is the durable record, and the adapter should be edited locally to point here.

## Acceptance criteria

- [ ] `qa-env-override.py --task <id> --slot <s>` produces a stack that builds **the worktree**, verified by a bring-up whose service reports code only present on the branch.
- [ ] Works for a **modifying** task, not just an additive one — prove it on a change to an existing endpoint, since that is the case the current tell cannot catch.
- [ ] Falls back cleanly to the main checkout when no worktree exists (single-task, non-wave runs).
- [ ] Covers every buildable compose service, `bff` included.
- [ ] The generator prints a provenance check.
- [ ] [T-104](T-104-project-resource.md), [T-151](T-151-dev-seeds-cv-sections.md) and [T-105](T-105-experience-ordering-retrofit.md) cross-linked, as the next tasks exposed.

## Definition of done

PR against `master` in the meta repo from `fix/qa-env-worktree-build-context`, with the manual `*.build.yml` workaround retired.

## Provenance

Found 2026-08-21 during T-103's stage 4 and worked around by hand for that run. Filed rather than left in the checkpoint because the workaround lives in a **gitignored** generated file that vanishes with the next cleanup — exactly the hand-off-that-lands-nowhere this board keeps having to re-file.
