---
id: T-027
title: "Contract: the ordering note prescribes SQL syntax for a JPQL context"
repo: cv-project (meta)
status: todo
owner:
branch: docs/contract-ordering-jpql-note
pr:
depends_on: []
risk: trivial
security_review: false   # docs-only; touches no adapter §5 security path
---

## Goal

`docs/api-contract.md` § Ordering mandates a spelling that does not work in the place the same section tells you to write it. Two lines, read together:

- **Line 39:** *"Both must be expressed explicitly — `ORDER BY start_date IS NULL, start_date DESC, id ASC` and `ORDER BY category IS NULL, category ASC, name ASC, skill_id ASC`"*.
- **Line 41:** *"the nullable cases need `@Query`… **projects and person skills cannot** [use the derived form] and require an explicit `@Query`"*.

`@Query` is **JPQL** unless `nativeQuery = true`. `ORDER BY <expr> IS NULL` is SQL: a boolean predicate used as a sort key. The section therefore hands the implementer a SQL fragment and tells them to put it somewhere SQL does not go.

## Why this is worth a task rather than a shrug

**It already cost one implementation detour, and the next task to hit it is [T-104](T-104-project-resource.md).** T-103's implementer reached the contradiction, worked around it with the portable JPQL spelling

```
ORDER BY CASE WHEN s.category IS NULL THEN 1 ELSE 0 END, s.category ASC, s.name ASC, ps.id.skillId ASC
```

and verified identical semantics against real MySQL 8.4 (`Java(Backend), Ansible(Ops), Terraform(Ops), Bash(null), Vim(null)` — uncategorized last). That is the right answer and it shipped. But line 41 names **projects** in the same breath as person skills, so **T-104 will hit this exact wall**, and the failure mode is unhelpful: the literal spelling either fails to parse or silently changes meaning, in a task whose whole ordering requirement is "undated **last**".

This is the [T-006](T-006-contract-section-ordering.md) → T-101 shape repeating one level down: a rule stated correctly at the semantic level, expressed in a form its consumers cannot use, caught only when someone implements it.

## Scope

**Clarify the wording. Do not change any ordering semantics** — the order itself is ratified, correct, and now implemented and live-verified for skills. This task changes prose only.

1. Keep the SQL spelling where it is doing useful work (it states the intent precisely and reads well against the migration), but mark it as **semantics, not a code snippet**.
2. Add the JPQL form implementers should actually write, i.e. the `CASE WHEN … THEN 1 ELSE 0 END` key, with a pointer to `PersonSkillRepository` as the worked example once T-103 merges.
3. State the `nativeQuery = true` alternative and why the portable form is preferred (the repo's other queries are JPQL; mixing dialects in one repository is worse than one `CASE`).

## Verify before writing — do not inherit this task's own premise

**Confirm empirically whether Hibernate 6.5.2 accepts the literal `ORDER BY x IS NULL` in JPQL.** This task is filed on the implementer's report plus the fact that the working code uses `CASE`; nobody has run the literal form and watched it fail. If Hibernate accepts it as an extension, the note is *ambiguous* rather than *wrong*, the fix is one clarifying clause instead of a correction, and this task's framing should be corrected in place rather than quietly softened. Recording that distinction now because filing a task on an unverified premise is the failure this board keeps cataloguing.

## Acceptance criteria

- [ ] § Ordering distinguishes the **semantic** rule from the **JPQL** an implementer writes, for both nullable cases (projects, person skills).
- [ ] The empirical result above is recorded in the PR description, whichever way it lands.
- [ ] No ordering **semantics** change: the five-row table at `docs/api-contract.md:20-26` is untouched.
- [ ] [T-104](T-104-project-resource.md) is cross-linked, since it is the next consumer.

## Definition of done

Docs-only PR against `master` in the meta repo from `docs/contract-ordering-jpql-note`, H1/H2 as one-line confirms per the adapter's trivial fast-path.

## Provenance

Filed 2026-08-20 from T-103's implementation round. Out of scope for [T-103](T-103-skills-catalog-and-assignments.md) itself (board rule 3): that PR ships the correct JPQL and must not carry a contract edit.
