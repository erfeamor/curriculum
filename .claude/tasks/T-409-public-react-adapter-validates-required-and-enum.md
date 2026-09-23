---
id: T-409
title: "cv-public-react's adapter defends the nullable half of the payload and trusts the rest — required fields, the `proficiency` enum, and an absent `endDate` all pass through an unchecked cast"
repo: cv-public-react
status: todo
owner:
branch: fix/adapter-runtime-validation
depends_on: [T-407]   # T-407 establishes the boundary this extends
risk: normal
security_review: false   # no auth or exposure change; a malformed upstream payload degrades this page only
---

## The gap

[T-407](T-407-public-react-tocv-null-invariant.md) made `BffCvRepository` a real anti-corruption layer for **nullable** fields: thirteen `?? null`, four element mappers, the domain invariant established at the boundary. Its doc comment now says so.

**That comment overclaims.** `getCv` still does:

```ts
return toCv((await response.json()) as CvDto);
```

An unchecked cast. Everything *not* nullable is still trusted, and the mappers copy it straight through. So the file reads as though the boundary is covered when only half of it is — which is worse than an obviously unguarded adapter, because the next reader stops looking.

## Three concrete instances

### 1. Required fields are undefended while optional ones are

`company`, `role`, `startDate`, `institution`, `degree`, `name` are copied through and typed non-nullable `string`. If a producer drops `startDate` on one experience, the domain object holds `undefined` in a `string`-typed field, and the first `new Date(startDate)` or `.slice(0, 4)` downstream yields `Invalid Date` or throws — **far from the boundary that was supposed to catch it.**

This is the same defect T-407 fixed, in the fields T-407 did not cover. The asymmetry is now *inside* the anti-corruption layer rather than between it and the domain.

### 2. `proficiency` is an unvalidated enum passthrough

`SkillDto.proficiency: Proficiency` is a claim made **only** by the cast. Nothing checks it at runtime.

If `cv-database` adds a fifth `person_skill` enum value and the domain service emits `"MASTER"`, it lands in a field TypeScript guarantees is one of four literals. A later exhaustive `switch`, or a `Record<Proficiency, …>` lookup — a proficiency-to-bar-width map is the obvious next feature — returns `undefined` **with no type error to warn.**

This is the one field where a value can be **wrong**, not merely missing. Every other gap here is an absence; this one is a lie with a plausible shape.

### 3. An absent `endDate` is indistinguishable from a deliberate "current"

T-407 normalizes all three `endDate` fields with `?? null`, and that was the right call for the domain invariant — but it has a cost that only runtime validation can remove.

`null` means different things across the thirteen fields. For the ten rule-7 optionals it is the *empty* value, so coercing an absent key to it is neutral. For `endDate`, rule 3 gives `null` the positive meaning **"current"** — so coercing an absent key asserts *"this role is ongoing."*

**Concretely:** a producer regresses and drops `endDate` on a finished 2020–2022 role. Once sections render, that role displays as **"Present"** — a wrong fact on a public CV, not a blank field or a loud failure.

T-407 accepted this deliberately and recorded it in-file. **Accepting it was correct; leaving it undetectable is what this task closes.** Validation at the boundary can tell "key absent" (a producer bug, should be loud) from "key present and null" (a current role, should render "Present") — the normalization cannot, because by then the information is gone.

## Why T-407 did not fix it

Board rule 3, and T-407's scope says it outright: *"Out of scope: adding a validation library (zod &c.) — this is normalization, not schema validation, and a dependency is a separate decision with its own bundle cost."*

Raised by the T-407 developer unprompted in its hand-back, and independently by `/code-review` as two of its three findings. Filed rather than absorbed.

## The decision this task must make first

**Validation library, or hand-written guards?** Both are defensible and they have different costs:

- **A library (zod, valibot):** declarative, one schema replaces the DTO interfaces, gives precise parse errors. Costs a runtime dependency and bundle weight on a site whose whole point is being statically generated and fast. `cv-public-react` currently ships **zero** runtime dependencies beyond Next/React — check this before assuming.
- **Hand-written guards:** no dependency, keeps the explicit field-by-field style the repo prefers and that `frontend-architect` endorsed in T-407's review. Costs more lines and drifts from the DTO types unless carefully written.

**Recommendation: hand-written guards**, on the strength of the bundle argument and the repo's stated preference for explicit framework-free domain code — but **settle it at refinement with the bundle numbers in hand**, not by assertion.

## Scope

- Validate required fields are present and of the right primitive type before mapping.
- Validate `proficiency` against the four literals; decide and record what happens on an unknown value (reject the skill, reject the payload, or map to a fallback — **not** silently pass through).
- Distinguish an **absent** `endDate` from a **present-and-null** one, so the "current" assertion is never fabricated. Decide what an absent one does — most likely fail loudly, since it is a contract violation.
- **Narrow or correct the adapter's doc comment** so it describes what the boundary actually guarantees.

**Out of scope:** any change to `cv-bff-node` or the domain service; the contract itself (the producers are compliant today — this is defence against regression, not a contract dispute); re-litigating T-407's thirteen-field normalization.

## Acceptance criteria

- [ ] A malformed payload missing a required field fails at the adapter boundary with a typed, actionable error — not at a `new Date()` call three layers up.
- [ ] An unknown `proficiency` value cannot reach the domain model; the chosen behaviour is tested and its reasoning recorded.
- [ ] An **absent** `endDate` is distinguishable from a present `null`, and does not silently render as "current". A test covers both.
- [ ] The adapter's doc comment describes the boundary's real guarantees.
- [ ] Tests for each case **fail against `master`** before the fix — the standard T-407 and T-406 were held to.
- [ ] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass.

## Watch-outs

- **Do not weaken the domain types to express validation state.** They describe a valid CV; the adapter's job is to guarantee the value is one.
- **Do not undo T-407.** The thirteen `?? null` stay. This adds a check *before* them, it does not replace them.
- **Retire the three `endDate` assertions from T-407's anonymous list when you change this path.** They currently sit inside a thirteen-way `describe.each` in `BffCvRepository.test.ts`, so the behaviour *is* pinned — a silent revert goes red today. What is missing is **intent**: an editor who breaks one sees `becomes null, not undefined, at experiences[0].endDate`, a generic-looking case, with no signal that this field is qualitatively different or that this task exists to revisit it. Replace them with **named** tests stating the trade-off directly (e.g. `rejects a payload with endDate absent, rather than silently asserting "current"`), so the next reader gets the intent from the test rather than from a source comment that goes stale the moment the behaviour it describes changes. **Deliberately not done in T-407** — writing a pinning test there and rewriting it here would be two write cycles over the same three lines. Recommended by `quality-assurance` at T-407 stage 4, 2026-09-22.
- Validating at the boundary is not the same as validating at build time — this site fetches under ISR background revalidation, so a producer regression arrives on a **live** site with no build to fail. Whatever "fail loudly" means here must be a thing the running page can do.

## dev-loop notes
- **Blocks [T-402](T-402-public-react-cv-sections.md)** (edge added 2026-09-23, board review): T-402 renders `endDate: null` as "Present", so it should land on an adapter that already tells absent from null — otherwise the wrong-"Present" instance above ships the day sections render.

- **Developer:** `fullstack-developer`. **Reviewer:** `frontend-architect` (adapter §2). Authoritative CI: **Vercel**.
- `risk: normal`. A live stack cannot exercise this any more than it could T-407 — the real BFF is contract-compliant, so the malformed payloads only exist in fixtures. Expect a unit-level test plan plus, at most, a piggybacked happy-path smoke.

## Provenance

Filed by the driver, 2026-09-22, during [T-407](T-407-public-react-tocv-null-invariant.md)'s review round 1. Three sources converged on the same boundary from different directions: the T-407 developer flagged the unchecked cast unprompted in its hand-back; `/code-review` raised the required-field gap and the `proficiency` passthrough as separate findings; and the `endDate` fabrication risk came out of `/code-review`'s first finding, which also corrected the driver's own H1 reasoning — the ruling had treated all thirteen nullable fields as carrying the same meaning of `null`, and three of them do not.

Verified by reading `BffCvRepository.ts` at `6b1eae2`, not inferred.
