---
id: T-302
title: "cv-admin-react section/skills stores: rare load-vs-write interleavings leave a wrong list, notice or error on screen until reload"
repo: cv-admin-react
status: todo
owner:
branch: fix/admin-store-read-races
pr:
depends_on: [T-301]
risk: normal
security_review: false
---

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
