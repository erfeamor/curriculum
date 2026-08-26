---
id: T-109
title: "The `id ASC` tiebreaker is asserted by tests that cannot go red — every ordered collection except experience"
repo: cv-domain-service
status: todo
owner:
branch: test/ordering-tiebreak-evidence
pr:
depends_on: [T-105]   # PATTERN dependency, not a code one: T-105 introduces the StatementInspector harness (CapturedSql) that is the candidate remedy here, and there is no SQL-capture test anywhere in this repo today. Doing this first means inventing the same harness twice. No file collision — T-105 touches only the experience package.
risk: normal
security_review: false   # test-only change in the domain service; no adapter §5 path (no auth, secrets, IAM, CI). A1 re-checks against the real diff.
---

## Why this exists

**Every ordered collection in `cv-domain-service` is correct, and in four of five the `id ASC` tiebreaker is protected by nothing.** This task is about the *evidence*, not the implementations — all five queries match the contract today. Delete the secondary sort key from any of the four below and the suite stays green.

### The mechanism, proven rather than argued

Established during [T-105](T-105-experience-ordering-retrofit.md)'s implementation and independently reproduced by two reviewers in its review round 1 (2026-08-26), by probe:

> **No row-order assertion in a `@DataJpaTest` can go red against a missing `id ASC` secondary key.** H2 stores rows in a primary-key B-tree, so a tie group is walked in `id`-ascending order *whatever the query says* — under `ORDER BY start_date DESC` alone, and under **no `ORDER BY` at all**. InnoDB usually does the same for a small unindexed scan.

The corollary is the part that bites: assigning ids out of insertion order does **not** rescue such a test. T-105 ratified exactly that fix at H1, and the developer then measured it failing to work — the tie test stayed green with no ordering whatsoever. Only an assertion against the **emitted SQL** discriminates a declared tiebreak from an incidental one.

### Confirmed instances — verified against `master` on 2026-08-26, not inferred

| Resource | Query | Tiebreak evidence today |
|---|---|---|
| `education` | derived `findByPersonIdOrderByStartDateDescIdAsc` | **none** — `EducationRepositoryTest:194` persists two tied rows normally (IDENTITY ⇒ ids monotonic in insertion order), so its tie assertion cannot fail. Its `startDate DESC` half *is* genuinely covered. |
| `project` | `@Query` `findByPersonIdOrdered` | **none** — the `ORDER BY` is literal in source, but no test goes red if `p.id ASC` is dropped |
| `person_skill` | `@Query` `findByPersonIdOrdered` | **none** — tiebreak is `skill_id`, same shape (the table has no `id` column, hence the `@Query`) |
| `skill` | derived `findAllByOrderByNameAscIdAsc` | **none** — same mechanism on the `name` tie |
| `experience` | derived, retrofitted by T-105 | **`declaresTheIdTiebreakerInTheGeneratedSql`** — a `StatementInspector` capture, confirmed red by probe |

`grep -rln StatementInspector src/` returns **nothing** on `master`: T-105 introduces the first SQL-capture evidence in this repo. That is what makes this a repo-wide pattern gap rather than one forgotten file.

**Why it matters concretely.** The contract calls the tiebreak *"mandatory, not decorative"* (§ Ordering) because ties are what make an order deterministic across consumers — and [cv-public-react's ISR **caches** whichever order won a render](T-402-public-react-cv-sections.md), freezing a divergent order into a served page. A regression that drops a secondary key produces a CV whose section order quietly differs between the admin UI and the two public sites, with a fully green build.

## The honest counter-argument, recorded so it is not re-derived

**This is a regression risk, not a live defect, and the four resources are not equally exposed.** `project` and `person_skill` carry their `ORDER BY` *literally in an `@Query` string*, so a reviewer reading the diff sees the sort keys directly — the derived-name resources (`education`, `skill`) hide the ordering in a method name, where a rename reads as harmless. If H1 wants to narrow this, the derived-name pair is the higher-value half and the `@Query` pair is the cheaper thing to decline.

**None of these is urgent.** Nothing is broken today, and this task should not be allowed to grow into a test-harness project.

## Decide at H1

1. **Is per-resource SQL capture the right remedy, or is there one structural check?** Copying T-105's `CapturedSql` into four test classes works but duplicates the harness five times. A single shared test utility, or one test that asserts the emitted `ORDER BY` for all five collections, may be better — decide before writing, because the duplicated form is what everyone reaches for first.
2. **Or is the cheaper answer to stop relying on row order entirely?** An assertion on the repository *declaration* (derived name / `@Query` text) is weaker but nearly free. T-105 rejected declaration-only assertions as a *substitute* and accepted them as an *addition* — re-decide here rather than inheriting that.
3. **Scope: all four, the derived-name pair, or education alone?** See the counter-argument above.

## Acceptance criteria

- [ ] For every collection in scope, dropping its tiebreaker from the query makes **at least one test go red** — demonstrated by actually removing it and reporting the failure, not asserted.
- [ ] The harness is introduced **once**, not copy-pasted per package, or the duplication is a recorded decision with its reasoning.
- [ ] **No production query changes.** All five orderings are correct today; this task adds evidence. Any implementation defect found goes in its own task (board rule 3), not into this diff.
- [ ] Whatever is left out of scope is named here with its reasoning, so the next reader does not re-discover it as a gap.
- [ ] `mvn -B test` and `mvn -B checkstyle:check` pass.

## Definition of done

PR open against `master` from `test/ordering-tiebreak-evidence`, Jenkins green, merged.

## dev-loop notes

- **Developer:** `backend-developer` (adapter §2). **Reviewers:** `/code-review` + `backend-developer` specialist lens. `risk: normal` — test-only, but it is the kind of change that can quietly assert nothing, which is the whole subject.
- **[T-026](T-026-first-build-after-cold-start-fails.md) applies** — the first Jenkins build after idle may fail spuriously. Re-run on the warm box; read the statuses API, not `gh pr checks`, which reports `pass` while a failed build sits in the history.

## Provenance

Filed 2026-08-26 from [T-105](T-105-experience-ordering-retrofit.md)'s review round 1. Raised by the `backend-developer` specialist lens as an explicitly out-of-scope observation (*"Education's implementation is correct; its evidence is not… that is a separate task, and I would not expand T-105's scope"*) — board rule 3 working as designed, the same boundary that produced [T-107](T-107-post-id-cross-person-write.md), [T-108](T-108-untransacted-update-read-modify-write.md) and [T-030](T-030-pr3-build1-success-then-error.md).

**The scope was widened by the driver before filing, on verification rather than on the report.** The reviewer named `education`; checking `master` directly found the same gap in `project`, `person_skill` and `skill`, and confirmed no SQL-capture harness exists anywhere in the repo. Recorded because this board has twice filed a task whose count was wrong at the moment of filing ([T-023](T-023-meta-docs-stale-bff-smoke-path.md) — two, then three, then four; [T-017](T-017-docs-drift-rds-to-selfhosted.md) — five mentions that were already permitted), both times because the filer trusted a description instead of re-running the check.
