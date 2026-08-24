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

> **The thesis was vindicated within one day — 2026-08-24.** This task was filed on the argument that *live use surfaces what synthetic rounds cannot*. It did, before the task could start: real board edits produced **five dead links and four materially wrong titles in `TASKS.md`, with `board-check.py` reporting `clean` throughout**. Three review rounds and 34 synthetic findings had not touched that class. See the link-integrity section below; it is now part of this task's scope.
>
> **A tension worth naming, since the date rule above is load-bearing:** the link-integrity check needs **no** elapsed data and could be built today, while the re-review genuinely needs the week. They are bundled here because a check belongs with the tool's review and because filing it separately was the alternative the human declined. **If it is wanted sooner, it is cleanly separable** — it shares no code path with the review and its fixtures stand alone. Do not let the 2026-08-30 date become the reason a buildable check waits.

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

## The eighth blind spot has already been found: LINK INTEGRITY (added 2026-08-24, on the human's instruction)

**Item 2 above asks for "every board defect it MISSED" and predicts an eighth blind spot. One arrived before this task could even start, and it is not hypothetical — it was live on the board and the validator reported `clean` the whole time.**

### What happened

During the 2026-08-24 TASKS.md/HISTORY.md split, the driver rewrote the public-path deployment table and **invented five task filenames that do not exist**:

| Link written into TASKS.md | The file that actually exists | Title the driver invented | The real title |
|---|---|---|---|
| `T-015-bff-container-registry.md` | `T-015-docs-reflect-deployed-bff.md` | "Set up image registry and CD for the BFF" | *Correct the meta docs that claim the BFF is deployed* |
| `T-403-cloudfront-caching-for-bff-aggregate.md` | `T-403-public-vanilla-deploy.md` | "CloudFront: cache the BFF's aggregate endpoint" | *Public site (vanilla): deploy + point at the deployed BFF* |
| `T-203-auto-redeploy-on-domain-changes.md` | `T-203-bff-ci-deploy-stage.md` | "Auto-redeploy the BFF's public sites" | *BFF CI: push to ECR and roll the container on master* |
| `T-404-cloudfront-gateway-to-bff-aggregate.md` | `T-404-public-react-point-at-deployed-bff.md` | "CloudFront: `/cv` aggregate route" | *Public site (React): point Vercel's `BFF_URL` at the deployed BFF* |
| `T-204-validate-path-params-before-interpolation.md` | `T-204-bff-validate-person-id-param.md` | (close enough) | *BFF: validate the person id before the upstream call* |

**`board-check.py` reported `clean` on every run**, including the run in the same session that introduced it. It was caught by a hand-written shell loop (`for f in ...; do [ -f "$f" ] || echo MISSING; done`), not by the tool.

### Why it passed — the mechanism, which is the useful part

**Check 2 matches rows to files by task ID, never by the link target or the title.** `| [T-015](T-015-bff-container-registry.md) | Set up image registry… |` satisfies it perfectly: the row's ID is `T-015`, a file with `id: T-015` exists, one row each. The **href** and the **title** are unvalidated free text.

**This is the [T-028](T-028-qa-env-generator-worktree-build-context.md) shape one level up: a check that agrees with itself.** Board-check confirmed the ID column against the frontmatter and pronounced the board consistent, while the part a human actually clicks was broken and the part a human actually reads was wrong.

### Why it is worth a check rather than a note

**The board's entire correction mechanism is inter-file links.** Every sweep, every hand-off note, every superseded marker, and the whole 2026-08-24 review — whose central fix was *"write the warning into the file the implementer actually reads"* — depends on `[T-xxx](T-xxx-slug.md)` resolving. Task files cross-reference each other heavily. **A single `git mv` breaks every inbound link silently**, and nothing on this board would notice: not the tool, not CI (there is none in this repo), and not a reader who trusts a green `board-check`.

Note also that the wrong **titles** were the more dangerous half. A dead link fails loudly when clicked; a plausible-but-wrong title is read and believed. Three of the five above materially misdescribed what the task does, and the driver's own simplification analysis in that session **was reasoned from the invented titles** and reached a correct conclusion on false evidence. That is this board's signature failure, produced by the board's own summary of itself.

### The check to build

**Primary — link resolution.** Every markdown link matching `](T-\d+[^)]*\.md)` in `TASKS.md`, `HISTORY.md`, `README.md` and every `T-NNN-*.md` resolves to a file that exists in `.claude/tasks/`. Report file, line and the dead target. Cheap, deterministic, offline.

**Secondary — ID/target agreement.** A link whose visible text names one task while its target names another (`[T-015](T-014-….md)`) is unambiguously wrong and worth failing on. Note this catches a *different* bug from the primary check: that link resolves fine.

**MANDATORY: skip inline code spans and fenced blocks — learned by prototyping, 2026-08-24.** A throwaway version of this check was run against the live board before this section was written. It returned **three** findings:

- **One real dead link**, in `T-201`'s brand-new [T-204](T-204-bff-validate-person-id-param.md) cross-reference — written *in the same session*, using one of the invented filenames from the broken table, and not noticed by the driver or `board-check`. **The check caught a live defect within minutes of being imagined**, which is the strongest available argument for building it.
- **Two false positives — both inside backticks, both in this very file**, where the incident is documented using examples like `` `| [T-015](T-015-bff-container-registry.md) | … |` ``. Those are illustrations of broken links, deliberately quoted.

**This is not an edge case; it is the normal shape of this board.** The strike-don't-delete convention means files routinely quote wrong links to explain why they were wrong, and a check that fires on documentation *of* a defect would make every such write-up trip the validator. Per T-031's own finding that one confirmed false positive is *fatal to adoption*, code-span handling is a correctness requirement, not a refinement.

**Explicitly NOT in scope, and each for a reason:**
- **Do not validate link *text* against the target's `title:` frontmatter.** Board rows deliberately shorten and annotate titles (`done (**A1 + stage-4 QA + review**)`), and the strike-don't-delete convention leaves superseded titles in place on purpose. A title-equality check would fire constantly on correct content — and T-031 already establishes that a validator which cries wolf gets switched off, which is worse than not having it.
- **Do not check external URLs** (GitHub PR links, the Jenkins host). That needs the network, makes the validator non-deterministic and non-offline, and would fail on a private repo or a stopped CI host. `board-check.py` is read-only and offline; keep it that way.
- **Do not check anchors** (`#section`). Markdown headings churn constantly in these files and the failure is harmless.

**Fix the board if it fires today**, per T-031's H1 ruling 2 — but note the five links above were repaired on 2026-08-24, so the expected result on the current board is **zero findings**. If it finds more, that is a live defect and a second data point for this task's verdict.

**Scope note, since this adds a check to a re-review task:** T-031's seven checks all trace to a recorded incident, and this now has one. It is an acceptance criterion below rather than loose prose deliberately — the 2026-08-24 review found three hand-offs that lived in prose and were held by no task's criteria, and the fix for that is not to create a fourth. If the re-review's verdict turns out to be *"the approach is wrong"* (AC5's third option), split this into its own task rather than building it into something being retired.

## One passenger, added 2026-08-24 on the human's instruction

**[T-019](T-019-ci-host-on-demand.md)'s billing-week criterion should be read in this session.** It is the last thing standing between T-019 and a fully-ticked acceptance list, and it needs one Cost Explorer read. Its billing week (automation applied 2026-08-19) completes **2026-08-26** — before this session's earliest start on 08-30 — with real builds through the automation on 2026-08-20/21/22. *(A first draft of this note claimed the week had "already" elapsed on 08-24; it had not — corrected the same day, see T-019.)* This session is meta-repo, read-only and applies nothing, which is exactly the shape that can carry it.

**The check:** the measured daily rate across a window containing those build days is at or near **$0.6837/day**; a higher sustained rate means the reaper is not stopping the box after builds. Record it against [T-020](T-020-cost-model-correction.md)'s model — **not** T-010's, which is superseded — and tick the criterion on T-019.

**This is a passenger, not a dependency.** It does not gate this task's own verdict and must not shape it. If it turns up something interesting, file it; do not absorb it (board rule 3).

## Acceptance criteria

- [ ] At least **7 days** of real board edits have elapsed since `ae343eb` (2026-08-23).
- [ ] Every finding the tool produced in that window is classified **true / false positive**, with the false positives reproduced.
- [ ] A deliberate attempt to find an **eighth duplicate-key** blind spot is made and its result recorded either way — "none found" is a valid and useful outcome, but only if it was actually looked for. **(Distinct from the link-integrity criteria below: that is a blind spot in a different check. Finding one does not discharge the hunt for the other.)**
- [ ] The mutation check is re-run and every mutant dies.
- [ ] **Link integrity is checked** — every `](T-NNN-*.md)` target in `TASKS.md`, `HISTORY.md`, `README.md` and every task file resolves to a file that exists. Offline, deterministic; no external URLs, no anchors.
- [ ] **ID/target agreement is checked** — a link whose visible text names one task and whose target names another fails. This is a *different* defect from a dead link and needs its own fixture; the link in question resolves.
- [ ] **Regression fixtures reproduce the 2026-08-24 incident specifically** — a row linking `T-015` to a non-existent `T-015-bff-container-registry.md`, and a row linking `[T-015]` to an existing `T-014-*.md`. Both must be confirmed **red before the check exists**, per this board's standing practice and T-031's own precedent of reproducing the four real shadowing incidents.
- [ ] **Links inside inline code spans and fenced blocks are skipped**, with a fixture proving it — this file quotes broken links on purpose to document them, and a prototype produced **two false positives here** before this rule was added. T-031 calls one confirmed false positive fatal to adoption.
- [ ] **The new check does not fire on the current board** — the five real dead links and the one in T-201 were repaired on 2026-08-24, so the expected result is zero. Anything it finds is live drift: fix it in the same PR (T-031 H1 ruling 2) and record it as a second data point for the verdict.
- [ ] **No title-equality check was added**, and the reason is recorded. Board rows deliberately shorten and annotate titles, and strike-don't-delete leaves superseded ones in place — a title check would fire on correct content, and a validator that cries wolf gets switched off.
- [ ] A written verdict: **converged**, **needs another round**, or **the approach is wrong**. The third is a real option and must not be excluded by sunk cost.

## Definition of done

PR open from `chore/board-check-re-review` with the verdict recorded on this task, or — if nothing is found — this task closed with the evidence that nothing was found. **Note there is no CI in this repo**; A1 and QA carry the whole weight.

## Provenance

**Link-integrity scope added 2026-08-24 on the human's instruction**, after the board split introduced five dead links and four wrong titles that `board-check.py` passed as clean. Worth recording precisely, because the shape matters more than the incident: **the driver introduced the defect, the validator missed it, and a hand-written shell loop caught it** — the same three-part pattern as the T-104/T-151 shadowing that motivated [T-031](T-031-board-frontmatter-validator.md) in the first place, one check-class over.

Filed 2026-08-23 at T-031's H2 gate. The human accepted the merge **and** asked for this, rather than choosing between accepting and blocking — the reasoning being that shipping it starts it catching real drift immediately, while the unconverged finding rate still deserves an answer that only live use can give.
