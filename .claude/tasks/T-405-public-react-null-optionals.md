---
id: T-405
title: "cv-public-react: two domain fields are typed required-non-null but will receive null, eight more claim a key may be absent that never is — and no fixture in the repo can see any of it"
repo: cv-public-react
status: todo
owner:
branch: fix/domain-null-optionals
depends_on: [T-209]   # types to the rule T-209 ratifies
risk: normal
security_review: false
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

- [ ] Every optional in `src/domain/cv.ts` reads `string | null`; no `?:` and no bare-`string` optional remains.
- [ ] `Skill.category` and `Project.startDate` are nullable — the two the contract's § Ordering already treats as nullable.
- [ ] A `BffCvRepository` test drives a payload with **every optional `null`** and asserts the mapped `Cv` carries them through as `null`. **It must fail against the current types** — demonstrate the red-before-green in the PR.
- [ ] `PersonHeader` renders correctly with `headline`/`location`/`summary` all `null` (no empty elements, no literal "null" text).
- [ ] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass.

## Watch-outs

- **Do not "fix" this with `?? ''` in `toCv`.** Empty string is not the same as "no value" and would erase the distinction the contract's ordering rules depend on — undated projects sort last, and `''` is not undated.
- Do not add a validation library. The task is to type the wire honestly, not to introduce runtime schema checking — that is a separate decision with its own bundle cost.
- `Proficiency` is a required enum and is **not** optional. Leave it.

## dev-loop notes

- **Developer:** `fullstack-developer` (adapter §2). **Reviewer: `frontend-architect`** — `cv-public-react` is its primary review surface. Authoritative CI: **Vercel**. Gates: the `cv-public-react` row of adapter §3.
- `risk: normal`. Small diff, but it is the type surface [T-402](T-402-public-react-cv-sections.md) will be built on.

## Provenance

Split from [T-209](T-209-contract-optional-field-null-semantics.md) at stage 0, 2026-08-28 (adapter §2). Originally T-209 "part 3", which named only `Skill.category` and `Project.startDate` and noted they were found *"by inspection, not by an exhaustive pass"*. **The exhaustive pass was done at refinement and found nine more** — every remaining optional in the file, wrong in the opposite direction. T-209's ruling 5 records it.
