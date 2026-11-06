---
id: T-038
title: "Re-review board-check's check 8 (link integrity) after two weeks of real board edits — it did not converge in synthetic review"
repo: cv-project (meta)
status: in_review
owner: tech-product-owner
branch: chore/board-check-link-re-review
depends_on: [T-032]
risk: normal
security_review: false   # read-only tooling in the meta repo; no adapter §5 path
pr: https://github.com/erfeamor/curriculum/pull/128
checkpoint:
  stage: review
  h1: approved 2026-11-06
  branch: chore/board-check-link-re-review
  worktree: none   # meta repo, main checkout
---

## Verdict (2026-11-06): **converged**, after one bounded fix

**H1 (2026-11-06):**
- **Method:** only this session's transcript survives, so the live findings from the window (the hook's and the driver's runs) can't be recovered. The human accepted a replay instead: today's check 8 against every board commit since T-032 merged, with an independent miss-hunt over the same trees. Uncommitted intermediate states are not observable either way.
- **Fixes:** any real defect is fixed here, in one round at most.

| Item | Result |
|---|---|
| 1. Findings in the window | **107 trees** (a29e09c → f913230, 2026-09-28 → 11-06) replayed: **0 check-8 findings**, so **0 false positives**. Every run exited 0 or 1. The one non-check-8 finding was a historical `[pr]`, which is out of scope. |
| 2. Miss-hunt | A naive regex extractor (inline links plus reference definitions) over the same 107 trees found 2 dead task-file targets. Both are **inside code spans** in T-032's own write-up (`[T-015](T-014-….md)` quoted as an example), so check 8 is right to skip them. **No misses.** No task-shaped target fell outside `_TASK_TARGET_RE`'s shape. |
| 3. Line numbers | There were no real findings to check, so 6 dead links were planted in a copy of today's board as a positive control: a table row, a wrapped paragraph, a list item with `./` and an anchor, an ID mismatch, a reference-style link, and a link after a code span that crosses a line. All 6 were caught, and a link inside the code span was correctly skipped. **One defect:** a line break *inside* an inline code span made every later link in that paragraph report one line early, because markdown_it turns that break into a space, not a `softbreak`. **Fixed** (`_code_span_line_breaks`: each span is matched in order in the inline block's raw source and verified against the token's normalized content). It never affected a real edit: all **946** task links on the live board report their true line, before and after the fix. |
| 4. Mutation re-run | T-032's script was gone, so it was rebuilt from T-032's table (19 check-8 mutants), plus 5 for the fix. **22 of 24 killed.** **m24/m25 are equivalent, re-confirmed**: across 9,220 inline tokens (the live board plus a probe of headings, nested lists, blockquotes, table cells, setext headings, HTML blocks and reference definitions), no non-inline block has children and every inline token has a `map`. **m30's equivalence argument was wrong.** It considered only line numbers, but with the table rule off, a stray backtick in one row pairs with one in the next row and hides the dead link between them. It is now killed by a fixture. The fix's own t5 survivor (the one-space strip) is killed by a fixture too. |
| 5. Dependency health | markdown_it-py 3.0.0. Every board-check in this session (~30 runs: the hook, `test-all.sh`, direct) imported it fine. No failure is recorded anywhere. |

**Why "converged":** across five weeks of real edits there were zero false positives and zero misses. The defects found are a line-number off-by-one on a shape the board never produced and one mis-argued equivalent mutant. Both are fixed with RED-first fixtures, and neither changes which links are flagged on any tree in the window. That is the T-031/T-032 criterion: the finding rate fell to zero on real input. **Re-open** if a real board edit ever produces a check-8 false positive.

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

- [x] At least 14 days of real board edits have elapsed since T-032 merged (a29e09c, 2026-09-28).
- [x] Every check-8 finding in the window is classified, and any false positive is reproduced as a fixture.
- [x] A deliberate miss-hunt is run and its result recorded, even if it's "none found".
- [x] The mutation check is re-run, and the equivalent-mutant arguments are re-examined.
- [x] A written verdict for check 8: **converged**, **needs another round**, or **the approach is wrong**.

## Provenance

Filed by the driver on 2026-09-28 at T-032's H2, which the human accepted: "Merge + file T-038".
