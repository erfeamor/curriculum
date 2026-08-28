---
id: T-405
title: "cv-public-react: two domain fields are typed required-non-null but will receive null, eight more claim a key may be absent that never is — and no fixture in the repo can see any of it"
repo: cv-public-react
status: done
owner: fullstack-developer
branch: fix/domain-null-optionals
pr: https://github.com/erfeamor/cv-public-react/pull/4
depends_on: [T-209]   # types to the rule T-209 ratifies
risk: normal
security_review: false
checkpoint:
  stage: done
  repo: cv-public-react
  branch: fix/domain-null-optionals
  pr: https://github.com/erfeamor/cv-public-react/pull/4
  commit: 2371eb1   # review-1 cleanup on top of aa596a8
  developer: fullstack-developer   # driven INLINE by the driver; reviewers are spawned
  reviewers: [code-review, frontend-architect]
  risk: normal
  security_review: false
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  updated: 2026-08-28
  merged: ffa5244
  budget:
    turns: 310
    total_tokens: 44500000
    subagent_tokens: 137410
    spawns: 2
    status: ok
    checked: 2026-08-28
    session_note: "Fourth task this session (T-207, T-209, T-210 merged). Baseline gates on cv-public-react master 2cc618b verified green BEFORE any edit: lint, typecheck, 9/9 tests, build."
---

## Goal

`src/domain/cv.ts` disagrees with what the BFF actually sends, in **both** directions. Retype all ten optionals to `string | null` per the rule [T-209](T-209-contract-optional-field-null-semantics.md) ratifies, and add fixture coverage that would have caught it.

## The two defects

**1 — required non-null, will receive `null`.** The unchecked lie:

```ts
export interface Skill   { name: string; category: string;   proficiency: Proficiency }
export interface Project { name: string; …; startDate: string; endDate: string | null }
```

`Skill.category` and `Project.startDate` are typed as required, non-nullable strings. Both are **contract-optional** and both arrive as `null`. The contract's § Ordering already reasons about exactly these two: `project.start_date` is called *"the only nullable date of the three"* with undated projects sorted **last**, and `skill.category` sorts *"uncategorized last"*. **The contract explicitly contemplates these being empty while this file declares they cannot be.**

**2 — `?:`, claiming a key may be absent that never is.** `Person.headline`, `location`, `summary`; `Experience.location`, `description`; `Education.fieldOfStudy`; `Project.description`, `repoUrl`. All eight are always present, valued `null`.

## Why TypeScript cannot warn about defect 1

`BffCvRepository.getCv` ends:

```ts
return toCv((await response.json()) as CvDto);
```

An **unchecked cast**, no runtime validation — and `toCv` copies the four section arrays through verbatim (`dto.skills ?? []`) without touching the objects inside them. So a `null` lands in a `string`-typed field with nothing between the wire and the domain type. This is *the* case a type system cannot catch by itself, which is why it needs a fixture.

## …and why no existing test would catch it

`BffCvRepository.test.ts`'s `payload` populates **every optional with a real string** — `category: 'Languages'`, `startDate: '2026-07-01'`, `fieldOfStudy`, `description`, `repoUrl`, all present and non-null. The suite passes identically whether these types are right or wrong. It is the board's recurring **green check that measures nothing**, and closing it is half this task.

## Latent today, expensive tomorrow — why now is the moment

Nothing crashes at present. `PersonHeader` guards with truthiness (`person.headline ? … : null`), so `null` renders correctly, and the four section types are **typed but never rendered** — [T-402](T-402-public-react-cv-sections.md) is still `todo`.

**That is the argument for doing it now, not for deferring it.** T-402 renders these fields and will be written against whatever these types claim. A component authored against `category: string` will index, `.toLowerCase()`, or sort on it without a guard, and the fix then costs T-402's components as well as this file.

## Scope

- All ten optionals in `src/domain/cv.ts` → `string | null` — the **eight** `?:` fields plus the **two** bare-`string` ones. `endDate: string | null` is already correct in all three interfaces and is **not** touched.
- Update the file's header comment on two counts: it says *"Optional head fields are optional here too"* — after T-209 the wrong word, they are **nullable**, not optional — and it cites `GET /api/v1/people/:id/cv`, when the ratified public path has been `/bff/api/v1/people/:id/cv` since [T-013](T-013-bff-public-edge-path.md). Both lines are being edited anyway.
- **Add a null-bearing fixture** to `BffCvRepository.test.ts` — a second payload with every optional `null`, asserting it maps through to the domain `Cv` intact. This is the coverage the current fixture cannot provide.
- Check `PersonHeader.test.tsx` covers a `null` head field; add the case if it does not. The component is already correct — this pins it.

**Out of scope:** rendering the section types ([T-402](T-402-public-react-cv-sections.md)), adding runtime schema validation to `BffCvRepository`, and any change to `toCv`'s mapping.

## Acceptance criteria

- [x] Every optional in `src/domain/cv.ts` reads `string | null`; no `?:` and no bare-`string` optional remains.
- [x] `Skill.category` and `Project.startDate` are nullable — the two the contract's § Ordering already treats as nullable.
- [x] A `BffCvRepository` test drives a payload with **every optional `null`** and asserts the mapped `Cv` carries them through as `null`. **It must fail against the current types** — demonstrate the red-before-green in the PR.
- [x] `PersonHeader` renders correctly with `headline`/`location`/`summary` all `null` (no empty elements, no literal "null" text).
- [x] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass.

## Watch-outs

- **Do not "fix" this with `?? ''` in `toCv`.** Empty string is not the same as "no value" and would erase the distinction the contract's ordering rules depend on — undated projects sort last, and `''` is not undated.
- Do not add a validation library. The task is to type the wire honestly, not to introduce runtime schema checking — that is a separate decision with its own bundle cost.
- `Proficiency` is a required enum and is **not** optional. Leave it.

## dev-loop notes

- **Developer:** `fullstack-developer` (adapter §2). **Reviewer: `frontend-architect`** — `cv-public-react` is its primary review surface. Authoritative CI: **Vercel**. Gates: the `cv-public-react` row of adapter §3.
- `risk: normal`. Small diff, but it is the type surface [T-402](T-402-public-react-cv-sections.md) will be built on.

## Provenance

Split from [T-209](T-209-contract-optional-field-null-semantics.md) at stage 0, 2026-08-28 (adapter §2). Originally T-209 "part 3", which named only `Skill.category` and `Project.startDate` and noted they were found *"by inspection, not by an exhaustive pass"*. **The exhaustive pass was done at refinement and found nine more** — every remaining optional in the file, wrong in the opposite direction. T-209's ruling 5 records it.

---

## Implementation + review round 1 — 2026-08-28

**Branch `fix/domain-null-optionals`, [#4](https://github.com/erfeamor/cv-public-react/pull/4).** Driven inline by the driver; **both** reviewers spawned per adapter §7 (`normal` → `/code-review` + the capability owner, `frontend-architect`, for whom this repo is the review surface).

**Baseline established before any edit** — `cv-public-react` @ `2cc618b`: lint, typecheck, 9/9 tests, build all green. So every gate result below is attributable to this change.

### Red-before-green (AC3) — ten errors, one per optional

Test written first. Against the **old** types the `Cv`-annotated fixture produced exactly ten errors, and the two distinct messages map onto the two defect classes:

```
BffCvRepository.test.ts(134,36): TS2322: 'null' not assignable to 'string'.              <- Skill.category
BffCvRepository.test.ts(136,63): TS2322: 'null' not assignable to 'string'.              <- Project.startDate
... x8                          TS2322: 'null' not assignable to 'string | undefined'.   <- the `?:` fields
```

**`frontend-architect` sharpened this and the correction is worth keeping**: the red lives in `npm run typecheck`, **not** in `npm test`. `jest.config.mjs` uses `next/jest`'s SWC transform, which strips types without checking them, so assigning `category: null` in a fixture is a runtime no-op and Jest would have passed against the old types. The claim "it must fail before the fix" is true of the **typecheck gate** — one of the four `vercel.json` runs — and stating it loosely would have been another green check measuring nothing.

### `/code-review` — 2 findings, both MEDIUM, both filed rather than absorbed

Neither is a defect in this diff; both are things the diff made visible.

**Finding 1 → [T-407](T-407-public-react-tocv-null-invariant.md).** `toCv` copies the scalars through with no `?? null`, so the types now assert "key always present" while nothing establishes it. **The adapter already defends the four section arrays with `?? []` and leaves every scalar undefended** — and copies section elements verbatim, so the six nested optionals get no normalization at all. If the producer omitted a key, `cv.headline` would be `undefined` in a `string | null` field and `=== null` — the comparison rule 7 invites — takes the wrong branch.

Filed, not fixed: T-405's scope says in as many words that *"any change to `toCv`'s mapping"* is out of scope. **Precedent is exact — [T-207](T-207-public-types-derived-from-domain-interfaces.md) was filed out of [T-205](T-205-bff-allowlist-section-normalizers.md) on the same rule.** It is a real instance of the board's shape one level up: **T-405 made a type stronger without making it true.**

The `?? null` there does **not** contradict [T-210](T-210-bff-domain-types-null-not-absent.md) forbidding it in the BFF: cv-bff-node is a pass-through where `?? null` would **fabricate data on the wire**; `BffCvRepository` is an anti-corruption layer where it normalizes into this app's own domain and nothing leaves the process. T-407 records the distinction in a table.

**Finding 2 → [T-406](T-406-public-react-bff-path-missing-prefix.md), already filed** by the driver before the review returned, from the same observation. Independent confirmation. `BffCvRepository` fetches `${BFF_URL}/api/v1/…` where cv-bff-node mounts only `/bff/api/v1`; the test asserts the wrong URL and `CLAUDE.md` documents it, so three sources agree and are wrong.

### `frontend-architect` — no blocking findings

Verified each of the ten retyped fields against the contract's `Required:` lists and § Ordering independently: `Experience.startDate`/`Education.startDate` correctly stay non-null (both are contract-required), `Project.startDate` correctly becomes nullable (*"the only nullable date of the three"*), `endDate` correctly untouched under rule 3. Hexagonal layering clean — `domain/` still imports nothing, no mapping logic leaked into infrastructure. `PersonHeader` accessible in the null case: no empty `<p>`, and the `📍` span cannot appear detached because it lives inside the truthy branch.

**One low, non-blocking note, applied:** the null-case test's three `queryByText('Backend Engineer' | 'Madrid' | 'Builds reliable systems.')` assertions check strings that exist only in the *other* test's fixture — they can never fail in this render path and add nothing over the `<p>` count. **Carried over unexamined from the original test**, which had the same weakness. Dropped, with a comment recording why: this task family exists because of checks that pass for reasons unrelated to what they claim to measure, so leaving three of them in a test being rewritten was not defensible.

**Re-probed after dropping them** — the guard is still pinned on all three fields:

| guard removed from | result |
|---|---|
| `headline` | **CAUGHT** |
| `location` | **CAUGHT** |
| `summary`  | **CAUGHT** |

(The first `location` run reported MISSED; that was a **probe artifact** — the regex did not match its multi-line JSX, so no edit was applied. Re-run with a matching pattern: caught. Recorded because "the probe did not fire" and "the test does not catch it" look identical in a log.)

### Gates

lint **PASS** · typecheck **PASS** · **10/10 tests**, 3 suites · build **PASS** — the same four commands `vercel.json` runs as its build command, so the deploy gate is these gates.

**Open findings: 0** (2 filed as follow-ups, 1 applied).

## Stage 4 — Exploratory QA — 2026-08-28

**No live stack, argued rather than skipped** — the third time in this run, and the cheapest to justify of the three.

The only non-test file this PR touches is `src/domain/cv.ts`, and it contains **no runtime construct at all** — `grep -E "^(export )?(const|let|var|function|class|enum)"` returns nothing. It is `export interface` and `export type` exclusively, both fully erased at compile time. There is no runtime delta to exercise, so a stack would measure nothing.

**A live stack would in fact have been actively misleading here**, which is worth recording. The Vercel preview deployment *is* a running instance, and it renders this site's `role="alert"` failure state — but for reasons that have nothing to do with this change: [T-406](T-406-public-react-bff-path-missing-prefix.md) (the fetch path the BFF does not serve) and [T-404](T-404-public-react-point-at-deployed-bff.md) (`BFF_URL` not yet pointed at a deployed BFF, which does not exist — the public deployment chain is still open). Reading that red as a verdict on T-405 would have been wrong in both directions: it is broken before the change and equally broken after.

What was verified instead is the surface that changed:

- **The typecheck gate**, which is where this change's red-before-green lives (`frontend-architect`'s correction — Jest's SWC transform does not type-check). Ten errors before, zero after.
- **The `<p>`-count assertion re-probed** after dropping three non-discriminating assertions: dropping `PersonHeader`'s truthiness guard on `headline`, `location` or `summary` each fails the test.
- **Vercel** (authoritative CI, adapter §3): `state: success`, *"Deployment has completed"*. Because `vercel.json` overrides the build command with `npm run lint && npm run typecheck && npm test && npm run build`, that green **is** all four gates re-run server-side, not merely a deploy.

`origin/master` is still `2cc618b`, this branch's own parent — no rebase, the green is not stale.

**QA verdict: PASS, 0 defects, 0 bounces.**
