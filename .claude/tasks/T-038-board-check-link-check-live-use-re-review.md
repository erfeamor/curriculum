---
id: T-038
title: "Re-review board-check's check 8 (link integrity) after two weeks of real board edits — it did not converge in synthetic review"
repo: cv-project (meta)
status: done
owner: tech-product-owner
branch: chore/board-check-link-re-review
depends_on: [T-032]
risk: normal
security_review: false   # read-only tooling in the meta repo; no adapter §5 path
pr: https://github.com/erfeamor/curriculum/pull/128
---

## ✅ DONE 2026-11-06 ([#128](https://github.com/erfeamor/curriculum/pull/128)): verdict **converged**, after one bounded fix

**H1 (2026-11-06):**
- **Method:** only this session's transcript survives, so the live findings from the window (the hook's and the driver's runs) can't be recovered. The human accepted a replay instead: today's check 8 against every board commit since T-032 merged, with an independent miss-hunt over the same trees. Uncommitted intermediate states are not observable either way.
- **Fixes:** any real defect is fixed here, in one round at most.

| Item | Result |
|---|---|
| 1. Findings in the window | **107 trees** (a29e09c → f913230, 2026-09-28 → 11-06) replayed: **0 check-8 findings**, so **0 false positives**. Every run exited 0 or 1. The one non-check-8 finding was a historical `[pr]`, which is out of scope. |
| 2. Miss-hunt | A naive regex extractor (inline links plus reference definitions) over the same 107 trees found 2 dead task-file targets. Both are **inside code spans** in T-032's own write-up (`[T-015](T-014-….md)` quoted as an example), so check 8 is right to skip them. **No misses.** No task-shaped target fell outside `_TASK_TARGET_RE`'s shape. |
| 3. Line numbers | There were no real findings to check, so 6 dead links were planted in a copy of today's board as a positive control: a table row, a wrapped paragraph, a list item with `./` and an anchor, an ID mismatch, a reference-style link, and a link after a code span that crosses a line. All 6 were caught, and a link inside the code span was correctly skipped. **One defect:** a line break *inside* an inline code span made every later link in that paragraph report one line early. markdown_it turns that break into a space, not a `softbreak`, so T-032's softbreak counting never saw it. It never affected a real edit: all **946** task links on the live board report their true line, before and after the fix. |
| 3a. Review round 1 | The first fix re-matched code spans in the raw text. `/code-review` found real shapes it still got wrong: an identical span in image alt text, a break inside alt text, a span right after an escaped backtick, and backticks inside a raw HTML attribute. It also named the cause: that fix re-derives markdown_it's grammar, which is T-032's own failure pattern. **Redesigned** (H1's one bounded fix round): the `link` and `image` inline rules are wrapped (`ruler.at`) to record each token's source offset, and the line is the block's first line plus the line endings before it. This is exact for every construct, and the softbreak bookkeeping and the heuristic are both gone (−57/+42 lines). All the reviewers' shapes, plus CRLF, a blockquote, a list item and an unclosed backtick, are now fixtures. 5 of them fail on the heuristic version and 13 of the class's tests fail on `master`. The QA lens confirmed that the change alters only line numbers, never which links are flagged. The replay over 107 trees still gives 0 findings. |
| 3b. Review round 2 | `/code-review` found **no correctness bug** (158 tests, probes on every shape) and 7 robustness items. Six were applied: an untagged link token now fails loudly (`meta["src_pos"]` indexed, not `.get()`); the internal-rule import got its own version message; `count("\n", 0, pos)` and a `range` loop replace two copies; two stale test comments and one test name were fixed. The seventh (alt-text links carry alt-relative offsets) is documented, since nothing reads image children. The mutation result, replay and control are unchanged. |
| 4. Mutation re-run | T-032's script was gone, so it was rebuilt from T-032's table. On the final code, after dropping the mutants of the removed softbreak code: 16 of T-032's check-8 mutants plus 6 for the position tracking. **19 of 22 killed.** **m24/m25 are equivalent, re-confirmed**: across 9,220 inline tokens (the live board plus a probe of headings, nested lists, blockquotes, table cells, setext headings, HTML blocks and reference definitions), no non-inline block has children and every inline token has a `map`. **p4 is equivalent**: a link pushes exactly one `link_open` and an image one `image`, so "first" and "last" are the same token. **m30's equivalence argument in T-032 was wrong.** It considered only line numbers, but with the table rule off, a stray backtick in one row pairs with one in the next and hides the dead link between them. It is now killed by a fixture. p2, p3 and p5 survived the first run, because every fixture's dead link sat alone on its paragraph's last line. Three position fixtures now kill them. |
| 5. Dependency health | markdown_it-py 3.0.0. Every board-check in this session (~30 runs: the hook, `test-all.sh`, direct) imported it fine. No failure is recorded anywhere. |

**Why "converged":** across five weeks of real edits there were zero false positives and zero misses. The defects found were a class of line-number errors on shapes the board never produced, plus one mis-argued equivalent mutant. The errors are now fixed at the root: line numbers come from the parser's own source positions instead of being re-derived. Every defect has a RED-first fixture, and none changes which links are flagged on any tree in the window. That is the T-031/T-032 criterion: the finding rate fell to zero on real input. **Re-open** if a real board edit ever produces a check-8 false positive.

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
