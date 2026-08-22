---
id: T-029
title: "/code-review silently reviews the wrong thing when given no explicit target"
repo: cv-project (meta)
status: todo
owner:
branch: fix/code-review-on-worktrees
pr:
depends_on: []
risk: normal
security_review: false   # tooling/process change in the meta repo; no adapter §5 security path
---

> ## PREMISE CORRECTED 2026-08-22, HOURS AFTER FILING — worktrees were never the cause
>
> This task was filed as *"`/code-review` returns nothing on a worktree"*. **That diagnosis was wrong**, and it was wrong in the way this board keeps finding: a plausible cause inferred from two observations, written down, and nearly inherited.
>
> Disproved during [T-016](T-016-dev-prod-mysql-parity.md), which runs in the **meta repo on a branch — no worktree at all**. Bare `/code-review low` there returned the same empty result in ~7s. Then `/code-review 52` (the PR number) ran a **full, high-quality review**: 21 tool calls, ~6 minutes, four findings, with the reviewer independently re-running the empirical claims against local Docker images.
>
> **The actual behaviour:** with no explicit target it reviews the **uncommitted working-tree diff**. In every failing invocation that diff was board markdown under `.claude/tasks/` — so "no findings" was *correct*, it just answered a question nobody asked. The task's branch changes were committed and therefore invisible to it.
>
> **So this is a usage defect, not a tool defect** — and the harm is unchanged: an empty result is **indistinguishable from a clean review**, and the driver reported it as "did not run" only because the 5-second duration was implausible. Anyone less suspicious records a clean review that never happened.

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

~~1. Establish the actual cause…~~ **Done 2026-08-22, see the correction above.** The cause is a missing target argument, not worktrees.

1. **Document the working invocation in `.claude/dev-loop-adapter.md` §7:** `/code-review <PR-number>` after stage 3, or an explicit committed-diff target. Bare `/code-review` reviews uncommitted changes and will silently review the board instead of the task.
2. **Sequencing consequence worth stating in the adapter:** the general pass therefore belongs **after** the PR exists (stage 3), not at stage 2 as the engine's ordering implies. Either move it, or use a target form that works pre-PR — but do not leave the pipeline invoking it in a position where it cannot see the change.
3. **The real deliverable is making an empty result distinguishable from a clean one.** Both prior failures were caught only by noticing a ~5-second duration. If the harness cannot distinguish them, the pipeline must: record the invocation form and require the reviewer to state what it examined, so "no findings" is always attached to a scope.

## Acceptance criteria

- [x] The cause is reproduced and stated, not inferred. **Done 2026-08-22** — see the correction block.
- [ ] The working invocation (`/code-review <PR-number>`) is documented in the adapter, together with the stage-ordering consequence.
- [ ] **An empty/no-op result is distinguishable from a genuine "no findings"** — this is the real deliverable. A remedy that leaves those two indistinguishable has not fixed the defect, only this instance of it.
- [ ] Adapter §7's reviewer table matches what the pipeline can actually execute.

## Watch-out

The adapter file is **gitignored on this machine** (it is the per-project binding, and its budget calibration is machine-specific). Confirm where the change should land before assuming it rides in a normal PR — this may be a local-only edit plus a note in the board.

## Provenance

Found at [T-152](T-152-mysql-84-parity-cv-database.md)'s stage 2, 2026-08-22. The driver stopped after two attempts rather than retrying a third time, did the general pass inline, and recorded that `/code-review` had not run rather than reporting its empty result as clean. Filed at T-152's H2 gate.
