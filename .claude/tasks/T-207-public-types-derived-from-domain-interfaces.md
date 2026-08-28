---
id: T-207
title: "BFF: the aggregate's Public* types are derived from the Domain* interfaces they exist to distrust — the allowlist's compile-time guarantee fails in both directions"
repo: cv-bff-node
status: done
owner: fullstack-developer
branch: fix/public-types-from-contract
pr: https://github.com/erfeamor/cv-bff-node/pull/9
depends_on: [T-205]   # T-205 writes the allowlists this bounds. The finding is about the types those rebuilds are checked against.
risk: normal
security_review: true   # same reasoning as T-205: the route is ANONYMOUS by contract (T-013), and the leak direction below lands on it
checkpoint:
  stage: done
  repo: cv-bff-node
  branch: fix/public-types-from-contract
  pr: https://github.com/erfeamor/cv-bff-node/pull/9
  commit: dc21c27   # squash-merged to master 2026-08-28; c210610 was the branch head
  superseded_commit: 71283f6   # pushed, no PR. A1 green: lint 0, typecheck 0, test 73/73, build 0. Both type directions driver-verified.
  developer: fullstack-developer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  updated: 2026-08-28
  merged: dc21c27
  budget:
    turns: 482
    total_tokens: 91720000
    subagent_tokens: 0
    spawns: 0
    status: ok
    checked: 2026-08-28
    session_note: "THIRD session on this task. Cumulative, NOT reset per references/budget.md: parked session 432 turns/88.6M (its own checkpoint block said 345/59M -- written mid-session and never refreshed, so it UNDERSTATED by ~87 turns; corrected here from the transcript). Resumed session 3 adds 50 turns/3.1M through stage-4 QA. Zero subagent spawns across all three sessions -- every review, probe and gate was run inline by the driver, which is why this task cost a fraction of the calibration run."
---

## Goal

`src/routes/cv.ts:66-69` defines the four public types by subtracting from the domain ones:

```ts
type PublicExperience = Omit<DomainExperience, 'id'>;
type PublicEducation  = Omit<DomainEducation, 'id'>;
type PublicSkill      = Omit<DomainSkillAssignment, 'skillId'>;
type PublicProject    = Omit<DomainProject, 'id'>;
```

So `tsc` checks T-205's field-by-field rebuilds against the **domain** shape — the very shape this code exists to stop trusting. Spell the four `Public*` types as standalone interfaces transcribed from `docs/api-contract.md` instead, so the compiler checks the public payload against the contract rather than against the upstream.

## Why this is worth a task

**T-205 made the runtime an allowlist. The types are still a denylist**, and its comment overstates what the compiler enforces: *"the cost is that a new CONTRACT field needs an edit in this file"*. Neither direction actually holds. Both were confirmed empirically against `b6fd1f6` during T-205's review round 1, by the reviewer and again by the driver:

- **Leak direction.** Adding a required `personId: number` to `DomainSkillAssignment` makes `PublicSkill` *require* it too, and the build fails:
  `src/routes/cv.ts(115,64): error TS2741: Property 'personId' is missing in type '{ name: string; category: string | undefined; proficiency: string; }' but required in type 'PublicSkill'.`
  The error points at `stripSkill`, and the path of least resistance under compiler pressure is to add `personId: s.personId` — **reintroducing exactly the disclosure T-205 removed, on the anonymous route, with a green build.** T-205's own premise is that someone will eventually update the domain interfaces to match what cv-domain-service really sends, so this is a *scheduled* event, not a hypothetical.
- **Drop direction.** Adding an *optional* `techStack?: string` to `DomainProject` typechecks **clean** with `stripProject` unchanged — the newly contracted field is silently absent from the public payload, with no compile error and no failing test. Every optional field in these sections (`location`, `description`, `fieldOfStudy`, `category`, `repoUrl`, project `startDate`) sits in that same blind spot.

This is the board's recurring **"green check that measures nothing"** shape once more — the compiler looks like it is guarding the public payload and is in fact guarding conformance to the upstream. Related: [T-205](T-205-bff-allowlist-section-normalizers.md) (the runtime half, merged), [T-107](T-107-post-id-cross-person-write.md), [T-109](T-109-ordering-tiebreak-unevidenced-siblings.md), [T-028](T-028-qa-env-generator-worktree-build-context.md).

## Scope

- Replace the four `Omit<Domain*, …>` aliases with standalone `interface` declarations whose fields are transcribed from `docs/api-contract.md` §§ Experience, Education, Projects, Skills — **not** from the `Domain*` interfaces above them.
- Correct the comment T-205 added so it describes the guarantee the code actually keeps.
- **Add a type-level regression guard** so the leak direction cannot come back silently: a test (or a `tsd`-style compile assertion, or a deliberate `// @ts-expect-error`) proving that an undeclared field added to a `Domain*` interface does **not** propagate into the corresponding `Public*` type.

**Out of scope:** the runtime normalizers themselves — T-205 already made them allowlists and this task must not change their behavior. The four leak tests and the sparse test it added must pass unchanged.

## Acceptance criteria

- [x] The four `Public*` types are standalone interfaces spelled from the contract; no `Omit<Domain*, …>` remains in `src/routes/cv.ts`.
- [x] Adding a required field to any `Domain*` interface produces **no** error in the corresponding `strip*` function (proving the public type no longer tracks the domain one). Demonstrate this in the PR the way T-205 demonstrated its red-before-green.
- [x] A newly added optional **contract** field is a compile error until the matching `strip*` copies it — the drop direction is closed.
- [x] The public payload is byte-identical: T-205's four leak tests, its sparse test, and T-201's contract-shape and no-leak tests all pass **unchanged**.
- [x] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass.

## Watch-outs

- The `Domain*` interfaces stay as they are — they describe the upstream and that is their job. Only the `Public*` side is transcribed from the contract.
- Do not weaken T-201's contract-shape test to make the new types fit; if they disagree, the contract wins and the types are wrong.

## dev-loop notes

- **Developer:** `fullstack-developer` (adapter §2 — `cv-bff-node`). Gates: the `cv-bff-node` row of adapter §3. Authoritative CI: **GitHub Actions**.
- `risk: normal`. Small diff, but it is the compile-time guard on an anonymous public payload.

## Provenance

Raised by `/code-review` (effort `high`) during [T-205](T-205-bff-allowlist-section-normalizers.md)'s review round 1, 2026-08-27, as a **LOW, explicitly non-blocking** finding. Both directions were then re-verified independently by the driver before filing. Filed rather than absorbed into T-205 per board rule 3: T-205's scope note says *"Keep the public types as they are — they already describe the intended shape correctly"*, and its acceptance criteria are its scope. That scope note is precisely what this task revisits — the types describe the intended shape, but they are **derived** in a way that does not hold it.

---

## H1 rulings — 2026-08-27

**Ruling 1 — AC3 was UNACHIEVABLE as written, and the fix is to change the field declarations, not the criterion.**

AC3 requires that a newly added optional contract field be a compile error until the matching `strip*` copies it. **With ordinary optional fields (`location?: string`) that is impossible** — an object literal may omit them freely. So the obvious reading of this task (transcribe the contract using `?:`) would close the **leak** direction and leave the **drop** direction exactly as open as it is today, *while appearing to satisfy AC3*. That is this board's signature failure mode — a green check that measures nothing — reproduced inside the task written to fix it. Caught at refinement rather than at review.

**Resolution: declare every contract field as a required KEY with a possibly-undefined VALUE** — `location: string | undefined`, not `location?: string`. Verified by the driver before ruling:

```
interface OptA { a: string; b?: string }              const f = (): OptA => ({ a: 'x' })  // NO error
interface ReqU { a: string; b: string | undefined }   const g = (): ReqU => ({ a: 'x' })  // TS2741
JSON.stringify({ a: 'x', b: undefined })  ->  {"a":"x"}
```

So omission becomes a compile error **and the wire payload is byte-identical**, because `JSON.stringify` drops undefined-valued keys. [T-205](T-205-bff-allowlist-section-normalizers.md)'s QA plan already established that second half — its `toEqual`/`toStrictEqual` ruling rests on exactly this behaviour — so the two tasks interlock rather than merely coexisting.

`endDate` stays `string | null` (required key, nullable value): it is required-but-nullable in the contract, which is a different thing from optional, and T-205 already settled that distinction.

**Ruling 2 — the `Domain*` interfaces are not touched.** They describe the upstream and that is their job. Only the `Public*` side is transcribed from `docs/api-contract.md`. AC2 is the proof that the two have been decoupled: adding a required field to a `Domain*` interface must produce **no** error in the corresponding `strip*`.

**Ruling 3 — budget: this task is expected to PARK at A1/review, not merge.** Started at 86% of a session-wide `ceiling_turns` with ~55 turns to HARD; the cheapest task this session cost ~65. Approved at H1 to drive through implementation and A1 and then stop at a checkpoint. **Resume at `checkpoint.stage`; do not restart.**

**Reviewers (for the resuming session):** `/code-review` + `/security-review`, as skills — same reasoning as T-205, T-206 and T-204.

---

## Stage 1 + A1 complete — PARKED 2026-08-27

**Branch `fix/public-types-from-contract` @ `71283f6`, pushed to origin, no PR.** A1 green: lint 0, typecheck 0, **73/73 tests** (7 suites), build 0. **No existing test was edited** — T-205's four leak tests and its sparse test, and T-201's contract-shape and no-leak tests, all pass unmodified. The public payload is byte-identical, as ruling 1 predicted.

### Both directions verified by the driver, not taken from the report

| probe | before (`d74d200`) | after (`71283f6`) |
|---|---|---|
| **Leak** — required `personId` added to `DomainSkillAssignment` | `TS2741` at `stripSkill` — compiler pressure toward `personId: s.personId` | **`exit=0`, no error.** Not copied, cannot leak |
| **Drop** — `techStack` added to the **contract** type | clean typecheck, field silently absent | **`TS2741` at `stripProject`** + the guard's own key-set assertion fires |
| **Drop, upstream-only** — `techStack` on `DomainProject` alone | — | `exit=0` — correct: an upstream-only field is not a contract field and must be a no-op |

The two comment references to `Omit<Domain*, 'id'>` that remain in the file are **prose recording what was replaced**, not declarations. AC1 is satisfied.

### The developer caught a weakness in its own guard, and it is worth keeping

Its first guard version **did not catch a single field regressing from `| undefined` to `?:`** — one `@ts-expect-error` covering an omission of two fields stays "used" while *either* remains required, so the directive never goes unused and the regression passes. It was strengthened to a per-type `NoOptionalKeys<T>` assertion before proceeding.

**That is this task's own failure mode appearing inside the guard written to prevent it** — a check that passes for a reason unrelated to what it claims to measure. Recorded because the weak version passed every other probe, so nothing else in the pipeline would have caught it.

### Resume instructions

**Re-enter at `checkpoint.stage: review`.** Stage 1 and A1 are done and verified; do **not** restart them. What remains:

1. **Review round 1** — `/code-review` + `/security-review` against the branch **as an explicit target** (T-029: without one it reviews the meta repo).
2. Open the PR, GitHub Actions green.
3. Stage 4 — assess whether a live stack adds anything. It probably does not: this is a **compile-time** change with a byte-identical runtime payload, and T-206's H1 ruling 2 is the precedent for arguing that in the PR rather than skipping silently.
4. H2, then merge.

**One review item to raise deliberately:** the types are now `export`ed so the guard can import them. That widens the module's public surface, and [T-206](T-206-person-id-guard-numeric-overflow.md)'s finding 2 was *exactly* about an export that outlived its justification. Ask whether the guard can assert without the export, or record why the export is justified — do not let it pass unexamined.

---

## Review round 1 — 2026-08-27 (resumed session)

### The flagged `export` question — examined, and the answer is that it is NOT T-206's finding 2

Parking notes flagged the new `export`s deliberately, because [T-206](T-206-person-id-guard-numeric-overflow.md)'s finding 2 was exactly about an export that had outlived its justification. **Examined, and the two cases are materially different.**

T-206's `PERSON_ID_PATTERN` was a **runtime value**: an importer could call it and receive the weaker of two checks. `export interface` is a **type-only** construct with no runtime existence, the guard imports it with `import type`, and there is no weaker sibling to reach for by mistake — the types *are* the contract, so importing them is correct usage rather than a footgun.

Verified rather than argued: **the emitted `dist/routes/cv.js` contains zero occurrences** of `PublicExperience`/`PublicEducation`/`PublicSkill`/`PublicProject`, and the module's only runtime export is `exports.default = router`. The export widens nothing that exists at runtime.

### The runtime is provably unchanged — read off the build, not inferred from tests

`npm run build` on `master` and on `71283f6`, then `diff` of the compiled `dist/routes/cv.js`:

**Every single difference is a comment line.** No executable statement differs. TypeScript carries comments into the emitted JS, so the diff is entirely the new explanatory block above the interfaces.

This is stronger evidence than "73/73 tests pass unmodified", which was the parking note's basis: the tests show no *observed* behaviour changed; the build diff shows **no code changed at all**. AC4 ("the public payload is byte-identical") is therefore satisfied by construction rather than by sampling.

### `/security-review` — no findings

A compile-time-only change with a zero-byte runtime delta cannot introduce a runtime vulnerability. It strictly **strengthens** the compile-time guard standing in front of an anonymous payload (T-013), closing the direction where a future domain-model edit would have applied compiler pressure to reintroduce a leak with a green build.

### `/code-review` — three findings, all applied at `c210610`

**Finding 1, MEDIUM — the guard covered four fifths of the payload.** `normalizePerson` had **no declared return type**, so its result was inferred and spread into `body`, and spread-in properties from a non-fresh type get no excess-property check. Driver-verified: adding `email: person.email` typechecked **clean at exit 0** and the field would have shipped — the one field this repo's `CLAUDE.md` ranks a hard blocker, while the four section normalizers *were* protected (`id: e.id` on `stripExperience` is `TS2353`).

Fixed by annotating the return as an exported `PublicPerson`. **Re-verified after the fix: the same edit is now `TS2353`.** Pinned by a `@ts-expect-error` case naming `email` explicitly.

**Finding 2, LOW — `PublicCv`'s own optionals still used `?:`**, uncovered by the guard, while the new comment stated the rule for "a `Public*` interface" without qualification. A reader would have believed it already applied. Now under the same rule and both guard families.

**Finding 3, MEDIUM — the transcription was unsound: the upstream sends `null`, not an absent key.** cv-domain-service declares no `@JsonInclude(NON_NULL)` and no `default-property-inclusion`, so Jackson's `ALWAYS` applies; its own tests assert it and record it confirmed against live MySQL. So `string | undefined` described a shape production never produces. Note the *conclusion* of T-205's comment still held — the payload genuinely is unchanged — but the stated *reason* was wrong, which matters on a task whose premise is that comments must describe what the code actually guarantees.

#### Deviation on finding 3 — ACCEPTED: `string | null | undefined`, not `string | null`

The instruction was `string | null`. **That does not compile, and the developer stopped and asked rather than improvising.** Driver-verified:

```
src/routes/cv.ts(143,5): error TS2322: Type 'string | undefined' is not assignable to type 'string | null'.
  Type 'undefined' is not assignable to type 'string | null'.        ... x7
```

The cause is one layer up: `Domain*` spells these `location?: string`, so `e.location` is `string | undefined`. The three ways out were (a) correct the `Domain*` optionals — **contradicts H1 ruling 2**, (b) `?? null` in the normalizers — **changes runtime behaviour**, or (c) widen to `string | null | undefined`.

**(c) is right, and it is sound rather than merely convenient:** it permits everything that can actually occur, forbids omission (required key, no `?:`), and leaves both guard directions intact — all re-verified. The imprecision is **inherited from `Domain*`, not introduced here**.

**And `Domain*` is itself wrong for the same reason:** `location?: string` claims the key may be absent, when Jackson `ALWAYS` guarantees it is present and possibly `null`. That is this task's own defect one layer up. It is out of scope by H1 ruling 2, so it is **not lost — [T-209](T-209-contract-optional-field-null-semantics.md) part 2 now owns it**, and once `Domain*` is corrected `Public*` can tighten from `string | null | undefined` to `string | null`.

### AC4 verified by construction, twice

`diff` of the compiled `dist/routes/cv.js` against `master`, non-comment lines only: **empty**. Zero executable difference. The public payload is unchanged not because 74 tests sample it, but because **no code changed at all**.

### Gates

lint 0 · typecheck 0 · **74/74 tests** (7 suites) · build 0. **No existing test moved** — only `src/routes/cv.ts` and the new `test/public-types.test.ts` differ from `master`. T-205's four leak tests and sparse test, and T-201's contract-shape and no-leak tests, all pass unmodified.

---

## Stage 4 — Exploratory QA — 2026-08-28 (resumed session)

**No live stack was brought up, and the argument for that is evidence rather than convenience** — made explicitly here rather than skipped silently, following [T-206](T-206-person-id-guard-numeric-overflow.md)'s H1 ruling 2.

### Why a stack would have measured nothing

Both trees were compiled with `tsc --removeComments`, so the emitted JavaScript can contain **only executable code**, and the two outputs were diffed:

```
npx tsc -p tsconfig.build.json --removeComments --outDir <tmp>   # on origin/master
npx tsc -p tsconfig.build.json --removeComments --outDir <tmp>   # on c210610
diff <master>/routes/cv.js <branch>/routes/cv.js   ->   IDENTICAL (97 lines each)
```

Review round 1 had diffed the *commented* build and observed "every difference is a comment line". This is the stronger form of the same check: with comments stripped at the compiler, the outputs are byte-identical. A live stack exercises the runtime, and **there is no runtime delta to exercise** — so a green stage-4 smoke here would have been this board's signature failure mode one more time, a check passing for a reason unrelated to what it claims to measure.

### What was actually exercised instead — the compiler, because that IS the change

The four guard directions were re-run by the driver against `c210610`, each by editing the file, running `tsc --noEmit`, and reverting. **Not taken from the developer's report or from review round 1.**

| # | probe | expected | observed |
|---|---|---|---|
| 1 | **Leak** — required `personId: number` added to `DomainSkillAssignment` | no error | **exit 0, typecheck CLEAN.** Not copied, cannot leak |
| 2 | **Drop** — `techStack` added to the **contract** type `PublicProject` | error until `stripProject` copies it | **`TS2741` at `cv.ts:203`**, *plus* the guard's own key-set assertion firing at `test/public-types.test.ts:38` |
| 3 | **Drop, upstream-only** — `techStack?: string` on `DomainProject` alone | no error | **exit 0, CLEAN** — correct: an upstream-only field is not a contract field and must be a no-op |
| 4 | **Person half** — `email: person.email` added to `normalizePerson` | error | **`TS2353` at `cv.ts:142`** — "'email' does not exist in type 'PublicPerson'" |

Probe 4 is the one review round 1 added (finding 1) and is the one that matters most: `email` is the field this repo's `CLAUDE.md` ranks a hard blocker, and before the fix that same edit typechecked clean and would have shipped on the anonymous route.

Working tree verified byte-identical to the CI-tested commit after all four reverts (`git diff` empty at `c210610`).

### Gates re-confirmed locally at `c210610`

lint **PASS** · typecheck **PASS** · **74/74 tests, 7 suites** · build **PASS**. GitHub Actions (authoritative CI, adapter §3) green on both jobs — `test` and `docker`. `origin/master` is still `d74d200`, the branch's own parent, so **no rebase is required** and the green is not stale.

**QA verdict: PASS, 0 defects, 0 bounces.**

---

## H2 accepted · MERGED 2026-08-28 — `dc21c27`

Squash-merged to `master` as [`dc21c27`](https://github.com/erfeamor/cv-bff-node/commit/dc21c27) via [#9](https://github.com/erfeamor/cv-bff-node/pull/9); branch `fix/public-types-from-contract` deleted. `origin/master` had not moved since `d74d200` (the branch's own parent), so the stage-5 rebase-and-rerun rule was satisfied without a rebase and the CI green was not stale.

**Merge mechanics, recorded because the classic branch-protection API misreports it.** `GET /branches/master/protection` returns **404 "Branch not protected"**, which is wrong as a description of this repo: protection is enforced by a **ruleset** (`Protect main branch`, id `18825342`, `enforcement: active`) requiring 1 approving review, linear history and signatures, with a `RepositoryRole` bypass at `bypass_mode: always`. GitHub forbids self-approval, so a solo-owner repo can only land a PR through that bypass — `gh pr merge --squash --admin`. Check `repos/<owner>/<repo>/rulesets` before concluding a branch is unprotected here.

### All five acceptance criteria met

| AC | Evidence |
|---|---|
| 1 — standalone interfaces, no `Omit<Domain*, …>` | Four `interface` declarations transcribed from the contract. The two surviving `Omit` mentions are **prose recording what was replaced**; the one live `Omit` is `PublicPerson = Omit<PublicCv, …>`, which derives from the **public** type, not a domain one |
| 2 — required domain field is a no-op | `personId: number` on `DomainSkillAssignment` → **exit 0, CLEAN** |
| 3 — new contract field is a compile error | `techStack` on `PublicProject` → **`TS2741` at `cv.ts:203`** + the guard's own key-set assertion at `test/public-types.test.ts:38` |
| 4 — payload byte-identical | `tsc --removeComments` output **identical, 97 lines**, master vs branch. Proven by construction, not sampled by tests |
| 5 — gates | lint · typecheck · **74/74** · build, all green locally and on GitHub Actions |

No existing test was modified: T-205's four leak tests and its sparse test, and T-201's contract-shape and no-leak tests, all pass unchanged.

### Cost — the useful datapoint for adapter §7

**Three sessions, 482 turns, ~91.7M tokens, and ZERO subagent spawns.** Every refinement ruling, review pass, guard probe and gate was run inline by the driver. Against the adapter's calibration run (~800 turns and **7 spawns** on one task) this is the cheaper shape, and adapter §7's own rule applies to reading it: **one datapoint, not a licence.** What it does support is the engine's standing instruction not to spawn for work the driver can do inline — the two `/code-review`-shaped passes here were the expensive-looking part and cost nothing extra.

The parked checkpoint recorded `turns: 345` for a session the transcript shows ended at **432** — it was written mid-session and never refreshed, understating by ~87 turns. Corrected from the transcript rather than carried forward. **Refresh `budget:` when the stage closes, not when it starts**, or a resumed run inherits a number that flatters it.

### What this leaves open

[T-209](T-209-contract-optional-field-null-semantics.md), filed from review round 1 and now the direct follow-up. The `Public*` optionals read `string | null | undefined` rather than the intended `string | null` **only** because `Domain*` spells them `?: string` and H1 ruling 2 put those out of scope; `string | null` does not compile until that is fixed (`TS2322`, ×7). T-209 part 2 owns the `Domain*` correction and should tighten `Public*` in the same PR — the guard added here will prove nothing else moved.
