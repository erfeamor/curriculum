---
id: T-029
title: "/code-review returns nothing on a worktree, so the adapter mandates a reviewer the pipeline cannot run"
repo: cv-project (meta)
status: todo
owner:
branch: fix/code-review-on-worktrees
pr:
depends_on: []
risk: normal
security_review: false   # tooling/process change in the meta repo; no adapter §5 security path
---

## Goal

`/code-review` was invoked **twice** against the [T-152](T-152-mysql-84-parity-cv-database.md) worktree on 2026-08-22 and both times returned an **empty result after ~5 seconds and a single tool call**. It does not review a target outside the session's own repository.

That is not a clean review. It is a pass that did not happen, and the danger is that its output is indistinguishable from "no findings".

## Why this is not a one-off annoyance

**Every dev-loop task in this workspace runs on a worktree outside the meta repo.** The adapter's §6 environment isolation and the engine's wave rules both require it, and [T-028](T-028-qa-env-generator-worktree-build-context.md) exists precisely to make the QA stack follow the worktree rather than `master`. So the affected set is not one task — it is `T-1xx`, `T-15x`, `T-2xx`, `T-3xx`, `T-4xx`: every code task the board has left.

Meanwhile adapter §7 makes `/code-review` **mandatory for every risk level** — it is the *only* reviewer for `trivial`, and half the set for `normal`. So the pipeline currently mandates a reviewer that silently no-ops on the exact shape of change it is meant to review.

**Concretely, [T-104](T-104-project-resource.md) is next**, and it is the task whose `@Query` NULL-ordering is the sharpest thing on the board. It would get a specialist lens and a no-op general pass, and nothing in the transcript would say so unless someone checked the timing.

## The failure class, which this board has now seen four times

A green-looking signal that measured nothing:

| | The signal | What it actually measured |
|---|---|---|
| [T-107](T-107-post-id-cross-person-write.md) | a passing test named `clientSuppliedIdInThePostBodyIsIgnored` | the mock's return value, not the code |
| [T-028](T-028-qa-env-generator-worktree-build-context.md) | a green stage-4 QA bring-up | `master`, not the branch under test |
| [T-026](T-026-first-build-after-cold-start-fails.md) | `gh pr checks` reporting `pass` | the latest status, with a failure hidden behind it |
| **this** | `/code-review` returning no findings | nothing — it never read the diff |

## Scope

1. **Establish the actual cause.** Do not fix on this task file's premise — reproduce it. Is it cwd-relative, git-repo-relative, or does it reject a path argument? Try: invoking from inside the worktree, passing a PR number, passing a branch, and passing an absolute path.
2. **Pick a remedy that fails loudly rather than silently.** Ranked by preference: (a) an invocation form that works and is documented in the adapter; (b) if none exists, the driver runs the general pass inline and the adapter says so explicitly, so the reviewer set is honest; (c) worst case, a documented "cannot run here" that the pipeline records on the task rather than skipping quietly.
3. **Update `.claude/dev-loop-adapter.md` §7** so the reviewer set states what actually runs.

## Acceptance criteria

- [ ] The cause is reproduced and stated, not inferred.
- [ ] A working invocation is documented, or its absence is documented with the fallback the pipeline uses instead.
- [ ] **An empty/no-op result is distinguishable from a genuine "no findings"** — this is the real deliverable. A remedy that leaves those two indistinguishable has not fixed the defect, only this instance of it.
- [ ] Adapter §7's reviewer table matches what the pipeline can actually execute.

## Watch-out

The adapter file is **gitignored on this machine** (it is the per-project binding, and its budget calibration is machine-specific). Confirm where the change should land before assuming it rides in a normal PR — this may be a local-only edit plus a note in the board.

## Provenance

Found at [T-152](T-152-mysql-84-parity-cv-database.md)'s stage 2, 2026-08-22. The driver stopped after two attempts rather than retrying a third time, did the general pass inline, and recorded that `/code-review` had not run rather than reporting its empty result as clean. Filed at T-152's H2 gate.
