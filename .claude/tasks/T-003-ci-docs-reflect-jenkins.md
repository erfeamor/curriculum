---
id: T-003
title: Correct the CI documentation to match reality (Jenkins)
repo: cv-project (meta)
status: todo
owner:
branch: docs/ci-reflect-jenkins
pr:
depends_on: [T-002]
risk: trivial
security_review: false   # added 2026-08-20 (hygiene): the key was missing entirely while `risk` was set. Value per adapter §5 — the diff touches none of its security paths; A1 forces /security-review anyway if the real diff disagrees, so this is a stage-0 default, not a ruling.
---

## ⚠️ RE-SCOPE THIS AT H1 — most of the task below has been overtaken by events (added 2026-08-24)

**Three of this task's four scope bullets are already satisfied or unreachable.** Verified against the working tree on 2026-08-24, not inferred:

| Original scope item | State today |
|---|---|
| `docs/architecture.md` names a Jenkins that does not exist | **Premise dead.** T-002 landed 2026-08-09, so Jenkins *does* exist — and separately, `grep -i jenkins docs/architecture.md` returns **nothing at all**. The file never named it. |
| `README.md`'s CI attribution | **Already correct.** The CI table (`:161`–`:172`) and the roadmap line (`:268`) name Jenkins ×2 / GitHub Actions ×3 / DroneCI ×1 / Vercel ×1, matching reality. |
| `.claude/dev-loop-adapter.md` § 3 | **Not fixable by a PR in this repo.** The adapter is **gitignored** (`.gitignore:10`) — it binds a checkout to an engine installed only in `~/.claude`. This is the same trap [T-029](T-029-code-review-cannot-see-worktrees.md) and [T-028](T-028-qa-env-generator-worktree-build-context.md) both hit: a task cannot deliver a change to a file the repo does not track. Whoever refines this should drop the bullet and note the adapter is the human's to edit locally. |
| Free Tier exception / instance sizing | **Partly done, and the surviving instance is not where this task looks** — see below. |

**What genuinely survives, and this task does not name it:** `docs/architecture.md:39` still asserts

> *"all AWS resource choices stay within Free Tier limits (EC2 t2/t3.micro …)"*

That is the exact claim [T-010](T-010-aws-credit-runway.md) disproved and [T-020](T-020-cost-model-correction.md) corrected — this account is on the **post-July-2025** Free Tier (a finite credit pot plus a 6-month window, no 750 h/month EC2 allowance), so every instance-hour bills. Both `CLAUDE.md` files were corrected; **this third location was never in anyone's scope** and still reads the old rule. It also names `t2/t3.micro` while the CI host is a **`t3.small`** (T-002's deliberate resize for Maven headroom).

**So the honest shape of this task is now: one line in one file** — plus whatever the H1 decides about the adapter bullet.

### Recommended: fold into T-023 and close this task (2026-08-24, on the human's instruction)

[T-023](T-023-meta-docs-stale-bff-smoke-path.md) is the same shape — meta repo, docs-only, `risk: trivial`, `security_review: false` — and touches none of the same files. Running both separately spends two branches, two PRs and two gate pairs to change five lines of prose.

**Recommendation: T-023's PR carries `docs/architecture.md:39`, and this task closes as absorbed**, recording where the line went. That keeps board rule 2 (*"one branch per task"*) intact, which the alternative — two tasks sharing one PR — does not.

**This is a recommendation for H1, not a decision taken here**, because closing a task is a scope call. What *is* settled is the re-scope above: three of the four original bullets are dead or undeliverable, so whoever refines this is deciding what to do with one line, not with the task as originally written. See T-023's bundle note for the two options in full.

## Why this exists

Split from **T-002** at refinement: that task touches `cv-infra`, this one touches the meta repo, and every task leaving stage 0 must target exactly one repo.

~~`docs/architecture.md` and `.claude/dev-loop-adapter.md` § 3 both name **Jenkins** as the authoritative CI for `cv-domain-service` and `cv-database`. Until T-002 lands, that is false — Jenkins is provisioned nowhere, and T-101's PR #3 demonstrated the consequence (`gh pr checks` → "no checks reported", zero webhooks on the repo).~~ **Struck 2026-08-24 — see the re-scope block above.** T-002 landed on 2026-08-09, and `docs/architecture.md` turns out never to have mentioned Jenkins. The consequence described (PR #3 with no checks) was real when written and was fixed by T-002 itself.

## Depends on T-002

~~Sequenced deliberately: **document what was actually built, not what was planned.**~~ **Satisfied — T-002 is `done` (merged 2026-08-09).** The sequencing argument was correct and has expired; the dependency is kept for the record rather than as a gate.

## Scope

- **`docs/architecture.md:39`** — correct the Free Tier assertion to match the post-July-2025 model already documented in both `CLAUDE.md` files, and stop naming `t2/t3.micro` as the sizing when the CI host is a `t3.small`. **This is the one surviving item.**
- ~~`docs/architecture.md` — describe where Jenkins actually runs…~~ **Struck: the file makes no Jenkins claim to correct.**
- ~~`.claude/dev-loop-adapter.md` § 3~~ **Struck: gitignored, not deliverable by a PR here.** Decide at H1 whether to note it for the human or drop it entirely.
- ~~Record the **Free Tier exception** and its actual monthly cost wherever the workspace's "AWS resources stay within Free Tier" rule is stated~~ — **superseded by [T-020](T-020-cost-model-correction.md)**, which replaced the "exception to a free allowance" framing entirely: there is no allowance here to except. Quote T-020's `readings:` block, not this bullet.

## Acceptance criteria

- [ ] `docs/architecture.md:39` no longer asserts the legacy Free Tier rule, and no longer implies the CI host is a `micro`. **(The one criterion that survives re-scope.)**
- [ ] ~~No document asserts a Jenkins deployment that does not exist.~~ **Already true, verified 2026-08-24 — `docs/architecture.md` makes no Jenkins claim and `README.md`'s CI table is accurate.** Re-verify at H1 rather than assuming this note is still current.
- [ ] ~~The Free Tier exception is written down with its cost and its rationale.~~ **Superseded by T-020** — the framing itself was wrong.
- [ ] ~~The adapter's § 3 CI table matches the deployed reality.~~ **Not deliverable from this repo — the adapter is gitignored.**
- [ ] No change to any file outside the meta repo.

## Definition of done

PR open against `master` from `docs/ci-reflect-jenkins`, task updated. Docs-only, so the `trivial` fast-path applies: light gates, H1/H2 as one-line confirms.
