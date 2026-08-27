---
id: T-207
title: "BFF: the aggregate's Public* types are derived from the Domain* interfaces they exist to distrust — the allowlist's compile-time guarantee fails in both directions"
repo: cv-bff-node
status: in_progress
owner: fullstack-developer
branch: fix/public-types-from-contract
pr:
depends_on: [T-205]   # T-205 writes the allowlists this bounds. The finding is about the types those rebuilds are checked against.
risk: normal
security_review: true   # same reasoning as T-205: the route is ANONYMOUS by contract (T-013), and the leak direction below lands on it
checkpoint:
  stage: review
  repo: cv-bff-node
  branch: fix/public-types-from-contract
  commit: 71283f6   # pushed, no PR. A1 green: lint 0, typecheck 0, test 73/73, build 0. Both type directions driver-verified.
  developer: fullstack-developer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  updated: 2026-08-27
  budget:
    turns: 345
    total_tokens: 59000000
    subagent_tokens: 0
    spawns: 0
    status: soft
    checked: 2026-08-27
    session_note: "FOURTH task this session (T-205, T-206, T-204 all merged first). Started at 86% of a session-wide ceiling_turns with ~55 turns to HARD, which is NOT enough to reach merge (prior tasks cost 65-140 turns). Started on the human's explicit instruction after a SOFT report. EXPECT THIS TASK TO PARK MID-PIPELINE -- resume from checkpoint.stage, do not restart."
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

- [ ] The four `Public*` types are standalone interfaces spelled from the contract; no `Omit<Domain*, …>` remains in `src/routes/cv.ts`.
- [ ] Adding a required field to any `Domain*` interface produces **no** error in the corresponding `strip*` function (proving the public type no longer tracks the domain one). Demonstrate this in the PR the way T-205 demonstrated its red-before-green.
- [ ] A newly added optional **contract** field is a compile error until the matching `strip*` copies it — the drop direction is closed.
- [ ] The public payload is byte-identical: T-205's four leak tests, its sparse test, and T-201's contract-shape and no-leak tests all pass **unchanged**.
- [ ] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass.

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
