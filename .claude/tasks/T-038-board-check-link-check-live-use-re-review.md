---
id: T-038
title: "Re-review board-check's check 8 (link integrity) after two weeks of real board edits — it did not converge in synthetic review"
repo: cv-project (meta)
status: todo
owner:
branch: chore/board-check-link-re-review
depends_on: [T-032]
risk: normal
security_review: false   # read-only tooling in the meta repo; no adapter §5 path
pr:
---

## Goal

[T-032](T-032-board-check-re-review-after-live-use.md) shipped check 8 (link integrity, built on markdown_it) with a **split verdict**, recorded in T-032 §12: checks 1–7 **converged**, and check 8 **did not**.

| Round | Code under review | Findings |
|---|---|---|
| 1 · `/code-review high` | the regex version of check 8 | 10, several of them false positives |
| 3 · `/code-review high` (the cap) | the markdown_it rebuild, called converged the same day | 10 |

The human approved one bounded fix round past the cap, and the driver verified it with probes rather than a 4th review. The finding rate did not fall. That is the pattern T-032 was filed to answer for T-031, and the answer there was **live use, not another synthetic round**.

**Do not start before 2026-10-12.** Two weeks of real board edits are the input. Starting early would re-run round 3 and learn nothing new.

## What to look at

1. **Every check-8 finding in the window** (`link`, `link-id`, `link-html`): true or false positive. **One confirmed false positive outweighs ten true ones** (T-031: a validator that cries wolf gets switched off).
2. **Every dead or mismatched link it missed.** Sweep the window's commits with a naive link extractor, or by hand, and diff against what check 8 reported.
3. **Line-number accuracy** on real findings: table rows, wrapped paragraphs, list items.
4. **Mutation re-run** with T-032's script. Its check-8 mutants include 3 argued equivalent (m24, m25, m30); re-check those arguments.
5. **Dependency health:** did the markdown_it hard dependency ever block a run (hook or `test-all.sh`) on this machine?

## Acceptance criteria

- [ ] At least 14 days of real board edits have elapsed since T-032 merged (a29e09c, 2026-09-28).
- [ ] Every check-8 finding in the window is classified, and any false positive is reproduced as a fixture.
- [ ] A deliberate miss-hunt is run and its result recorded, even if it's "none found".
- [ ] The mutation check is re-run, and the equivalent-mutant arguments are re-examined.
- [ ] A written verdict for check 8: **converged**, **needs another round**, or **the approach is wrong**.

## Provenance

Filed by the driver on 2026-09-28 at T-032's H2, which the human accepted: "Merge + file T-038".
