---
id: T-302
title: "cv-admin-react section/skills stores: rare load-vs-write interleavings leave a wrong list, notice or error on screen until reload"
repo: cv-admin-react
status: in_progress
owner: tech-product-owner
branch: fix/admin-store-read-races
pr:
depends_on: [T-301]
risk: normal
security_review: false
checkpoint:
  stage: 1   # H1 accepted 2026-09-27
  repo: cv-admin-react
  branch: fix/admin-store-read-races
  worktree: /home/erfeamor/work/cvdl-worktrees/T-302
  pr:
  developer: fullstack-developer
  reviewers: [code-review, frontend-architect]
  risk: normal
  security_review: false
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: 1
  updated: 2026-09-27T12:00:00+02:00
  budget:
    turns: 514   # --since 2026-09-25T12:49:25.700Z (session-wide)
    total_tokens: 115504286
    subagent_tokens: 0
    spawns: 1   # quality-assurance (shared T-302/T-115 plan)
    status: ok
    checked: 2026-09-27T12:00:00+02:00
---

## H1 — accepted by the human, 2026-09-27

- **Writes during a load:** forms and write buttons are disabled while `loading`. The store **also rejects** a write that arrives mid-load, with a distinct error (not a silent no-op), so a UI bug surfaces.
- **Notices split per list:** `skillsStore` gets `catalogNotice` + `assignmentsNotice`; each is cleared **only** by a successful re-read of its own list. `sectionStore` keeps one notice with the same rule. Writes that do not re-read never clear a notice.
- **Test plan:** QA's 9 cases (4 fail-first scenarios, UI-disabled check, 3 regressions, exploratory race probe). The runner is **Jest**, not Vitest.

## The gap

[T-301](T-301-admin-cv-sections-crud.md) re-reads a section's list after each write, so the list shows the server's order. The review rounds 1–2 hardened that with per-person guards and sequence counters. `/code-review` round 3 (the review cap, 2026-09-27) found four remaining **display-only** interleavings, all in `src/application/sectionStore.ts` / `skillsStore.ts` at `65c8650`:

1. **A save during a person-switch load discards the load's rows.** Forms are not disabled while `loading`. If the save's re-read then fails, the page shows only the saved row and none of the person's other entries. (`sectionStore.ts:89`; `skillsStore.ts:73`, including the catalog after `createSkill`.)
2. **The "reload to see server order" notice is cleared by writes that do not re-read the list.** Examples: deleting another row, an in-place re-assign, an unassign. (`sectionStore.ts:122`; `skillsStore.ts:111`, `:141`.)
3. **The skills catalog and the assignments share one notice.** A catalog re-read clears an assignments-order notice, and vice versa. (`skillsStore.ts:91`, `:118`.)
4. **A superseded load's failure still shows the blocking error** over a list that a newer re-read already refreshed. (`sectionStore.ts:91`; `skillsStore.ts:77`.)

Nothing is lost or corrupted on the server, and a reload always shows the truth. The PO ruled them non-blocking at T-301's review cap.

## Direction (settle at refinement)

**Prefer simplification to more counters:** disable the forms (and write buttons) while a load is in flight. That removes 1 and 4 at the source. Then give each list its own notice (2, 3), cleared only by a successful re-read of **that** list.

## Acceptance criteria

- [ ] Each of the four scenarios has a test that fails at `65c8650` or later master.
- [ ] Writes cannot start while a load is in flight (or the chosen alternative is recorded).
- [ ] `npm test`, `typecheck`, `lint`, `build` and `build-storybook` pass.

## Provenance

Filed by the driver, 2026-09-27, from T-301's round-3 `/code-review` on commit `65c8650`.
