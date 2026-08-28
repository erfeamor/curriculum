---
id: T-210
title: "BFF: the Domain* interfaces say an optional key may be ABSENT when the upstream always sends it as null — and that imprecision is what forced T-207's Public* types to stay loose"
repo: cv-bff-node
status: done
owner: fullstack-developer
branch: fix/domain-types-null-not-absent
pr: https://github.com/erfeamor/cv-bff-node/pull/10
depends_on: [T-209]   # types to the rule T-209 ratifies; MUST NOT start before it lands
risk: normal
security_review: false   # no runtime change; the anonymous-route guard is strengthened, not relaxed
checkpoint:
  stage: done
  repo: cv-bff-node
  branch: fix/domain-types-null-not-absent
  pr: https://github.com/erfeamor/cv-bff-node/pull/10
  commit: 87251c7   # review-1 fixes on top of 51bef92
  developer: fullstack-developer   # driven INLINE by the driver: the refinement probe already produced this task's exact spec (the three guard errors), so a cold spawn would pay to rediscover it
  reviewers: [code-review]
  risk: normal
  security_review: false
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  updated: 2026-08-28
  merged: 005337b
  budget:
    turns: 220
    total_tokens: 25000000
    subagent_tokens: 83000
    spawns: 2
    status: ok
    checked: 2026-08-28
    session_note: "Third task this session (T-207 merged, T-209 merged). H1 approved T-209/T-210/T-405 as one run."
---

## Goal

`src/routes/cv.ts` spells every optional upstream field `location?: string`, claiming **the key may be absent**. cv-domain-service's Jackson default is `ALWAYS`, so the key is **present and possibly `null`** — [T-209](T-209-contract-optional-field-null-semantics.md) ratifies that into `docs/api-contract.md`. Correct every `Domain*` optional to `: string | null`, then tighten every `Public*` optional from `string | null | undefined` to `string | null` — **ten of each in `src/routes/cv.ts`**, plus a second, separately-declared pair in `src/routes/people.ts` (see scope).

## Why this exists as its own task

[T-207](T-207-public-types-derived-from-domain-interfaces.md) intended `string | null` and **could not have it.** `string | null` does not compile while `Domain*` says `?: string` — `TS2322: Type 'string | undefined' is not assignable to type 'string | null'`, ×7. Its three ways out were (a) fix `Domain*`, forbidden by its own H1 ruling 2; (b) `?? null` in the normalizers, which changes runtime behaviour; (c) widen to `string | null | undefined`. It took (c), recorded the imprecision as **inherited from `Domain*`, not introduced**, and filed this.

So this is not tidying. `Domain*` is the **root** of the imprecision, and `Public*` cannot be honest until it is fixed.

## The work, as measured — not estimated

The change was applied to `dc21c27` at T-209's refinement and reverted. **`src/routes/cv.ts` typechecks completely clean; all three errors are in T-207's guard**, `test/public-types.test.ts`:

| line | error | what it means |
|---|---|---|
| 75 | `TS2578` unused `@ts-expect-error` | the omission fixture no longer fails the way the directive expects |
| 81 | `TS2322` `undefined` not assignable to `string \| null` | `description: undefined` |
| 117 | `TS2322` same | the `it()` premised on `\| undefined` existing |

`npm test` under the probe: **72 pass, 1 suite fails to compile.** The 72 include T-205's four leak tests **and its route-level sparse test** (`test/cv.test.ts:475`), which feeds fixtures with keys genuinely omitted and passes unchanged. **The types move; the runtime's tolerance does not.**

## Scope

**`src/routes/cv.ts`** — the aggregate:

- The ten `Domain*` optionals → `: string | null` (`DomainPerson.headline/email/location/summary`, `DomainExperience.location/description`, `DomainEducation.fieldOfStudy`, `DomainSkillAssignment.category`, `DomainProject.description/repoUrl/startDate`).
- All ten `Public*` optionals → `string | null`: seven section-level (`PublicExperience.location/description`, `PublicEducation.fieldOfStudy`, `PublicSkill.category`, `PublicProject.description/repoUrl/startDate`) plus `PublicCv`'s three head fields.

**`src/routes/people.ts`** — `GET /bff/api/v1/people/:id`, **added at review round 1** (see below):

- Its own `DomainPerson` (four `?: string`) → `string | null`.
- Its own `PublicPerson` (`headline?`/`location?`/`summary?`) → **required keys** with `string | null` values — the `?:` spelling T-207 established as unsafe, still live on a second anonymous route.
- **Rework `test/public-types.test.ts` to the new surface** — this is the bulk of the task, not an afterthought.
- Correct T-207's comment block, which currently explains *why `| undefined` is kept* and says "THE CONTRACT IS SILENT on null-vs-absent". After T-209 the contract is not silent; cite the ratified rule instead.

**Out of scope:** the normalizers' runtime behaviour, the allowlist design, and any `?? null` coercion. The wire payload must not move.

### Why `people.ts` joined the scope

`/code-review` on [T-209](T-209-contract-optional-field-null-semantics.md) found that this task's **AC1 was unsatisfiable as filed**: it says *"no `?: string` remains in any `Domain*` interface"* — repo-wide — while the scope named only `cv.ts`. `src/routes/people.ts` declares a **second, independent** `DomainPerson` with the same four `?: string`, and a `PublicPerson` whose three optionals use `?:` keys.

Driver-verified. That second `PublicPerson` is the **drop direction still open**: an object literal may omit a `?:` key for free, so a newly contracted head field would vanish from `GET /bff/api/v1/people/:id` with a green build — precisely the hole T-207 closed on the aggregate and never on this route, which is **anonymous by contract** ([T-013](T-013-bff-public-edge-path.md)) just like the aggregate.

Widening rather than filing a follow-up, because the AC already covered it and because ratifying rule 7 while leaving the repo contradicting it **on a public route** would be the emptiest possible outcome.

## Acceptance criteria

- [x] No `?: string` remains in any `Domain*` interface **in either `cv.ts` or `people.ts`**; no `| undefined` remains in any `Public*` type.
- [x] `people.ts`'s `PublicPerson` has **no optional (`?:`) keys** — so omitting a head field from `normalize` is a compile error there too, as it already is on the aggregate.
- [x] **Both T-207 guard directions still hold, re-proved after the change**: a required field added to a `Domain*` interface produces **no** error in the matching `strip*`; a new field added to a `Public*` type is `TS2741` until the matching `strip*` copies it.
- [x] `NoOptionalKeys<T>` still holds for all five public types — no field regressed to `?:`.
- [x] The `email` excess-property guard still fires: `email: person.email` in `normalizePerson` is `TS2353`.
- [x] **The wire payload is unchanged, proved by construction**: `tsc --removeComments` output diffed against `master` is identical. (T-207 established this method; it is the strongest available evidence and it is cheap.)
- [x] T-205's four leak tests and its route-level sparse test pass **unmodified**.
- [x] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass.

## Watch-outs

- **`test/public-types.test.ts`'s second `it()` is reframed, not deleted** (T-209 ruling 4). Its premise dies with `| undefined`, but it pins the runtime fact that an absent upstream key degrades to an absent *wire* key rather than a literal `undefined` — which is worth *more* now that the types say it cannot happen, not less. Keep it with an explicit cast and a comment stating the contract forbids the input while the runtime still tolerates it.
- **Weakening or deleting a guard to make the type change fit is a review blocker.** The guard failing is the guard working; T-207 built it for exactly this transition.
- Do not add `?? null` anywhere. If a value arrives `undefined` at runtime despite the contract, `JSON.stringify` drops the key and the payload degrades gracefully — coercing to `null` would *change the wire*.
- `endDate: string | null` is already correct everywhere. Do not touch it.

## dev-loop notes

- **Developer:** `fullstack-developer` (adapter §2). Authoritative CI: **GitHub Actions**. Gates: the `cv-bff-node` row of adapter §3.
- `risk: normal`, `security_review: false`. The route is anonymous by contract ([T-013](T-013-bff-public-edge-path.md)) but this change **strengthens** its compile-time guard and cannot alter the payload; T-207 already carried the security review for this surface.

## Provenance

Split from [T-209](T-209-contract-optional-field-null-semantics.md) at stage 0, 2026-08-28 (adapter §2 — cross-repo items decompose into dependency-ordered single-repo tasks, contract first). Originally T-209 "part 2". The measurements above are from the refinement probe, driver-run against `dc21c27` and reverted.

---

## Implementation + review round 1 — 2026-08-28

**Branch `fix/domain-types-null-not-absent`, [#10](https://github.com/erfeamor/cv-bff-node/pull/10), `87251c7`** (review fixes on `51bef92`). Driven **inline by the driver** — the refinement probe had already produced this task's exact specification, so a cold spawn would have paid to rediscover it.

### The `people.ts` hole was real, and it was open

The scope widening was justified at refinement on the strength of a code read. Verified as red-before-green against `dc21c27`:

```
normalize() with `headline` omitted, on master  ->  CLEAN, exit 0
                                  after T-210  ->  TS2741: Property 'headline' is missing
```

A newly contracted head field would have vanished from `GET /bff/api/v1/people/:id` — **anonymous by contract** ([T-013](T-013-bff-public-edge-path.md)) — with a green build. That is T-207's drop direction, still open on the route T-207 never reached.

### Six probes, each applied and reverted

| probe | expected | observed |
|---|---|---|
| Leak — required `personId` on `DomainSkillAssignment` | no error | **CLEAN, exit 0** |
| Drop — `techStack` on `PublicProject` | error | **`TS2741`** |
| Regression — `PublicSkill.category` back to `?:` | error | **`TS2322`** |
| `email` into `normalizePerson` | error | **`TS2353`** |
| `people.ts` — `PublicPerson` back to `?:` | error | **`TS2322`** |
| `people.ts` — `normalize()` omits `headline` | error | **`TS2741`** |

**A harness bug destroyed the first probe run and is worth recording.** The runner reverted with `git checkout -- <files>`, which discarded the *uncommitted implementation* along with each probe edit — so after probe 1 the source was back at `HEAD`, the test file's import of `PublicPerson` broke, and probes 3/5/6 reported `TS2614` (a broken import) instead of their real results. Caught because `TS2614` is not an error any of those probes could legitimately produce. Re-run with scratchpad save/restore. **A probe harness that reverts with `git checkout` silently destroys uncommitted work; save the files instead.**

### Review round 1 — 2 findings, both valid, both applied at `87251c7`

**Finding 1, LOW — a stale instruction that would have reintroduced exactly what this task removes.** The allowlist comment block still read *"contract-optional fields, which is why those are declared `T | undefined` rather than `?:`"* — in the file whose comments **are** the transcription mechanism a future editor follows.

The deeper half is what makes it worth recording. **`NoOptionalKeys` does not catch that spelling**, verified by the driver rather than assumed:

```
interface Sneaky { name: string; imageUrl: string | undefined }
const a: NoOptionalKeys<Sneaky> = true;      // NO ERROR -- the existing guard passes
const b: NoUndefinedValues<Sneaky> = true;   // TS2322  -- the new one fires
interface Good   { name: string; imageUrl: string | null }
const c: NoUndefinedValues<Good> = true;     // NO ERROR -- no false positive
```

So a field spelled `string | undefined` passed **every** existing assertion — key set matched, no optional keys, the drop-direction directive still fired — and nothing in the suite failed. Fixing the comment alone would have left that open, because **a comment cannot fail a build**. `NoUndefinedValues<T>` now covers all six public types. Confirmed live: respelling `PublicProject.description` fires at `public-types.test.ts:96`.

**Finding 2, LOW — the head route had the type-level guarantee and not the runtime one.** `test/people.test.ts` only ever exercised a fully-populated person, so `headline: person.headline || null` would satisfy `PublicPerson`, typecheck clean, pass every test, and silently collapse an upstream empty string to `null` on an anonymous route.

**The first version of that test did not work, and this is the finding within the finding.** It used a *mixed* fixture — `headline: null`, `location: ''` — and `null || null` is still `null`, so it caught a coercion only on whichever single field happened to be `''`. **The probe that proved it caught `|| null` was itself the thing that showed it did not**: applying the coercion to `headline` left the test green.

**That is this task's own theme, in the test written to close it** — the third instance in the T-205→T-207→T-210 lineage. Rewritten as two cases with **uniform** fixtures (all-`null`, all-empty-string), which between them catch `|| null` and `?? ''` on any of the three fields. Verified across all four combinations; every one fails the suite.

### Gates

lint **PASS** · typecheck **PASS** · **76/76 tests**, 7 suites · build **PASS**.

**AC5 re-verified after the review fixes**: both trees compiled with `tsc --removeComments`, `diff -r` over the whole `dist` tree — **identical**. `routes/cv.js` 97 lines, `routes/people.js` 32 lines, byte-for-byte. Zero executable delta.

**T-205's four leak tests and its route-level sparse test are unmodified** — under `test/`, only `public-types.test.ts` and `people.test.ts` differ, and the latter only gains cases.

**Open findings: 0.**

## Stage 4 — Exploratory QA — 2026-08-28

**No live stack, and the argument is evidence rather than convenience** — same shape as [T-207](T-207-public-types-derived-from-domain-interfaces.md)'s stage 4, following [T-206](T-206-person-id-guard-numeric-overflow.md)'s H1 ruling 2 that this is argued in the open, never skipped silently.

`tsc --removeComments` on both trees, `diff -r` over the entire emitted `dist`: **identical**. There is no runtime delta to exercise, so a green smoke would have measured nothing.

What was exercised instead is the surface that actually changed — the compiler, and the runtime *coercion* behaviour the types cannot see:

- **Six type-level probes**, table above, each applied and reverted. All six as specified.
- **Four coercion probes** on the head route: `|| null` and `?? ''`, each on `headline`, `location` and `summary`. **All four fail the suite**, which is the point — the first draft of that test failed to catch any of them.

GitHub Actions (authoritative CI, adapter §3) green on `87251c7`: `test` **SUCCESS**, `docker` **SUCCESS**. `origin/master` is still `dc21c27`, this branch's own parent — no rebase needed, the green is not stale.

**QA verdict: PASS, 0 defects, 0 bounces.**
