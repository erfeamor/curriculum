---
id: T-210
title: "BFF: the Domain* interfaces say an optional key may be ABSENT when the upstream always sends it as null — and that imprecision is what forced T-207's Public* types to stay loose"
repo: cv-bff-node
status: todo
owner:
branch: fix/domain-types-null-not-absent
depends_on: [T-209]   # types to the rule T-209 ratifies; MUST NOT start before it lands
risk: normal
security_review: false   # no runtime change; the anonymous-route guard is strengthened, not relaxed
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

- [ ] No `?: string` remains in any `Domain*` interface **in either `cv.ts` or `people.ts`**; no `| undefined` remains in any `Public*` type.
- [ ] `people.ts`'s `PublicPerson` has **no optional (`?:`) keys** — so omitting a head field from `normalize` is a compile error there too, as it already is on the aggregate.
- [ ] **Both T-207 guard directions still hold, re-proved after the change**: a required field added to a `Domain*` interface produces **no** error in the matching `strip*`; a new field added to a `Public*` type is `TS2741` until the matching `strip*` copies it.
- [ ] `NoOptionalKeys<T>` still holds for all five public types — no field regressed to `?:`.
- [ ] The `email` excess-property guard still fires: `email: person.email` in `normalizePerson` is `TS2353`.
- [ ] **The wire payload is unchanged, proved by construction**: `tsc --removeComments` output diffed against `master` is identical. (T-207 established this method; it is the strongest available evidence and it is cheap.)
- [ ] T-205's four leak tests and its route-level sparse test pass **unmodified**.
- [ ] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass.

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
