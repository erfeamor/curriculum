# Task manager — agent team protocol

File-based task board for agents (and humans) working on cv-project. Lives in the meta repo so every agent sees the same state; the actual work happens in the sibling product repos.

## Layout

```
.claude/tasks/
  README.md     ← this protocol
  TASKS.md      ← the board: one line per task, always current
  T-NNN-*.md    ← one file per task (frontmatter = state, body = spec)
```

Task IDs are grouped by layer: `T-0xx` design/meta · `T-1xx` cv-domain-service · `T-15x` cv-database · `T-2xx` cv-bff-node · `T-3xx` cv-admin-react · `T-4xx` cv-public-vanilla · `T-5xx` cross-repo integration.

## Task lifecycle

`todo → in_progress → in_review → done` (plus `blocked` from anywhere, with a reason).

- **todo**: unowned, free to claim. A task is claimable only when every ID in `depends_on` is `done` (or the task file explicitly says work can start against the contract).
- **in_progress**: owned; branch exists in the target repo.
- **in_review**: PR is open; `pr:` field filled in.
- **done**: PR merged into `master`.

## Rules for agents

1. **Claim atomically.** Before starting, set `owner:` and `status: in_progress` in the task file AND update the board line in `TASKS.md`. If `owner:` is already set, pick another task — never reassign someone else's task except from `blocked`.
2. **One branch per task** in the target repo, named as the task file's `branch:` field says. Never commit to `master` — it is protected everywhere; all changes land by PR.
3. **The task's acceptance criteria are the definition of scope.** Anything beyond them goes in a new task file, not in your PR.
4. **The contract wins.** API-shaped tasks implement [docs/api-contract.md](../../docs/api-contract.md) exactly; if you believe the contract is wrong, set the task `blocked` and open a PR against the contract instead of improvising.
5. **Before opening the PR**: the repo's own tests and lint pass locally (each repo's CLAUDE.md documents the commands), and the repo's CI pipeline file covers your new code path.
6. **On PR open**: set `status: in_review` and paste the PR URL into `pr:`. **On merge**: set `status: done`.
7. Board-state edits (status/owner flips) are working-tree edits in the meta repo — batch-commit them via a `chore/board-sync` PR periodically or when a milestone completes; don't open a PR per status flip.

## Current milestone

**M2 — Complete the domain model end-to-end** (`experience`, `education`, `skill`, `project` from database to public site). Tasks T-101…T-501. The database schema for all four already exists (`cv-database/sql/migrations/V1__init_schema.sql`); nobody needs to touch the schema for this milestone.
