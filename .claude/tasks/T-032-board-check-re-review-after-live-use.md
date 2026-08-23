---
id: T-032
title: "Re-review board-check.py after a week of real use — synthetic rounds found 34 defects and never converged"
repo: cv-project (meta)
status: todo
owner:
branch: chore/board-check-re-review
depends_on: [T-031]
risk: normal
security_review: false   # read-only tooling in the meta repo; no adapter §5 path. A1 re-checks against the real diff.
pr:
---

## Goal

[T-031](T-031-board-frontmatter-validator.md) shipped after **three review rounds and 34 findings**, which is the pipeline's maximum. Re-review `scripts/board-check.py` once it has run against **real board edits for at least a week**, on the explicit view — ratified by the human at T-031's H2, 2026-08-23 — that live use surfaces what synthetic rounds cannot.

**Do not start this before 2026-08-30.** Elapsed time carrying real edits *is* the input; running it early re-runs round 3 with a fourth reviewer and learns nothing new.

## Why this exists — the finding rate never fell

| Round | Scope | Findings |
|---|---|---|
| 1 · `/code-review high` | whole branch | 6 |
| stage-4 QA | behaviour + hook | 2 |
| 2 · `/code-review max` | `board-check.py` | 11 |
| 3 · `/code-review max` | **the test file** (never reviewed before) | 11 + 4 from the driver |

A falling rate would have argued convergence. **This one did not fall.** What changed instead was the *character*: round 3's findings were almost entirely fallout from round 2's fix — a dual-path dispatch the driver ruled for, which orphaned the fallback's entire test coverage and introduced three false positives. That path is now deleted, so the specific cause is gone; whether the *rate* was telling us something more general is the open question this task answers.

**The honest counter-argument, recorded so nobody re-litigates it from memory:** the code is now smaller than before that fix (966 → 740 lines), the fallback whose coverage was orphaned no longer exists, and 111 tests pass including four that read real historical incidents out of git. A green suite after removing the destabilising change is not the same as a green suite that never had one.

## What to actually look at — evidence, not another cold read

1. **Every finding it produced in the wild.** Was each one real? A false positive in check 1 is what T-031 itself calls *fatal to adoption* — the tool gets switched off, and then everyone believes the board is checked when it is not. **One confirmed false positive is a bigger result than ten true ones.**
2. **Every board defect it MISSED.** Diff the sweeps: run the checks a human sweep would have caught by eye against what the tool reported. Check 1 missed **seven** distinct YAML surface forms across T-031's three rounds. There is no reason to assume the eighth does not exist.
3. **Did anyone turn it off, work around it, or edit the board to silence it?** That is the adoption signal, and it is not visible from the code. Look for `--no-*` flags reached for, findings "fixed" by deleting the key rather than correcting it, and whether the opt-in hook is still registered in `settings.local.json`.
4. **The `/dev-loop` driver invocation.** Enforcement point (b) lives in the gitignored adapter and does **not** propagate. Did the driver actually run it at each checkpoint write? T-031's whole motivation is that *all four* of the most recent shadowing incidents were driver edits.
5. **Mutation-test the suite again.** Round 3's method — revert each fix, confirm a test dies — found 11 survivors that three prior passes missed. It is the highest-yield technique used on this task and it should be the first one reached for, not the last.

## Acceptance criteria

- [ ] At least **7 days** of real board edits have elapsed since `ae343eb` (2026-08-23).
- [ ] Every finding the tool produced in that window is classified **true / false positive**, with the false positives reproduced.
- [ ] A deliberate attempt to find an **eighth** duplicate-key blind spot is made and its result recorded either way — "none found" is a valid and useful outcome, but only if it was actually looked for.
- [ ] The mutation check is re-run and every mutant dies.
- [ ] A written verdict: **converged**, **needs another round**, or **the approach is wrong**. The third is a real option and must not be excluded by sunk cost.

## Definition of done

PR open from `chore/board-check-re-review` with the verdict recorded on this task, or — if nothing is found — this task closed with the evidence that nothing was found. **Note there is no CI in this repo**; A1 and QA carry the whole weight.

## Provenance

Filed 2026-08-23 at T-031's H2 gate. The human accepted the merge **and** asked for this, rather than choosing between accepting and blocking — the reasoning being that shipping it starts it catching real drift immediately, while the unconverged finding rate still deserves an answer that only live use can give.
