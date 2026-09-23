---
id: T-407
title: "cv-public-react's domain types now assert `null`-not-absent, but `toCv` never establishes it — the adapter defends the arrays and leaves every scalar undefended"
repo: cv-public-react
status: done
owner: fullstack-developer
branch: fix/tocv-null-invariant
pr: https://github.com/erfeamor/cv-public-react/pull/6
depends_on: [T-405]   # T-405 declares the invariant; this makes it true at runtime
risk: normal
security_review: false
checkpoint:
  stage: done   # merged ff068e1 (squash of #6), 2026-09-22
  qa: pass
  pr: https://github.com/erfeamor/cv-public-react/pull/6
  repo: cv-public-react
  branch: fix/tocv-null-invariant
  developer: fullstack-developer
  commit: ff068e1   # squash merge on master (branch commit was cd63d08)
  reviewers: [code-review, frontend-architect]
  risk: normal
  security_review: false
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  ruling: "normalize all THIRTEEN string|null fields (10 rule-7 + 3 rule-3 endDate), not the AC's self-contradictory ten/six"
  filed_from_review: [T-409]
  live_stack: "skipped by design — live BFF verified to emit all 13 keys, so it cannot reproduce the defect; piggyback smoke on cvdl_t-406 only"
---

## The gap

[T-405](T-405-public-react-null-optionals.md) retyped all ten contract-optional fields to `string | null`, asserting **the key is always present**. Nothing establishes that at runtime:

```ts
return toCv((await response.json()) as CvDto);   // unchecked cast, no validation
```

and `toCv` copies the scalars straight through:

```ts
headline: dto.headline,        // no `?? null`
location: dto.location,
summary:  dto.summary,
experiences: dto.experiences ?? [],   // arrays ARE defended
```

**The adapter already defends the four section arrays with `?? []` and leaves every scalar undefended.** That asymmetry is the whole finding: the same author, in the same function, guarded one kind of absence and not the other.

Worse for the sections — `toCv` copies `dto.experiences ?? []` **verbatim**, never touching the objects inside, so `location`, `description`, `fieldOfStudy`, `category`, `repoUrl` and `startDate` get no normalization at all.

## Why it matters, concretely

If the producer ever omits a key, `cv.headline` is `undefined` while typed `string | null`. A consumer written **to the ratified contract** then takes the wrong branch:

- `person.headline === null` → `false` for `undefined`, so an absent value is treated as present.
- `project.startDate === null` → `false`, and the *"undated projects last"* rule (contract § Ordering) silently misclassifies the row.

Those are the exact comparisons contract rule 7 invites a consumer to write — the rule says *"a consumer may assume the key exists and must handle `null`"*.

## The distinction that makes this correct here and WRONG in the BFF

[T-210](T-210-bff-domain-types-null-not-absent.md) explicitly **forbade** `?? null` in `cv-bff-node`, and that ruling stands. The two are not in tension:

| | cv-bff-node | cv-public-react |
|---|---|---|
| role | **pass-through**: rebuilds the public payload from the upstream | **anti-corruption layer**: maps a wire format into a domain model |
| effect of `?? null` | **fabricates data on the wire** — invents a `null` the producer never sent, changing what every downstream consumer receives | **normalizes into this app's own domain invariant** — nothing leaves the process |
| what the contract says | rule 7 is *"inherited from the producer, not enforced by the BFF"* | a consumer *"may assume the key exists"* — this adapter is where that assumption is made safe |

`BffCvRepository`'s own doc comment already claims this role: *"this adapter still owns the mapping so the domain never depends on the wire format, and it defends against missing section arrays."* It should defend against missing scalars for the same reason and in the same place.

## Scope

- `toCv`: `?? null` on the three head scalars.
- **Per-section mapping** for the nested optionals — `location`, `description`, `fieldOfStudy`, `category`, `repoUrl`, `startDate`. This is the part that is not a one-liner: `toCv` currently does not map inside the arrays at all, so this adds four small element mappers.
- A test driving a payload with keys genuinely **omitted** (not null) and asserting the domain `Cv` comes back with `null` — the mirror of T-405's all-null fixture. It must fail before the change.

**Out of scope:** adding a validation library (zod &c.) — this is normalization, not schema validation, and a dependency is a separate decision with its own bundle cost. Also out of scope: any change to `cv-bff-node`, whose behaviour is correct and deliberate.

## Acceptance criteria

- [x] Every field the domain types declare `string | null` is `null`, never `undefined`, after `toCv` — for all **thirteen**: 3 head + 3 `Experience` + 2 `Education` + 1 `Skill` + 4 `Project`. (Wording corrected at implementation per the refinement ruling: "ten"/"six nested" undercounted — the three rule-3 `endDate`s are typed `string | null` too, and `description` occurs on both `Experience` and `Project`.)
- [x] A test feeds a payload with those keys **absent** and asserts `null` on each; it fails against `master` — one case per field, all thirteen red on `master` (`Received: undefined`), plus a two-element `experiences` case that catches an index-0-only fix.
- [x] The four `?? []` array defenses still work (guard before `.map`), and T-405's all-null fixture test passes unchanged.
- [x] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass.

## Watch-outs

- **`?? null`, not `|| null`.** `||` would collapse a legitimate empty string to `null`, erasing a real value — the same mistake [T-210](T-210-bff-domain-types-null-not-absent.md)'s head-route test was written to catch.
- Do not "fix" this by loosening the domain types back to `string | null | undefined`. That would restore the imprecision the whole T-209/T-210/T-405 line removed, and would push the null-check onto every future component instead of the one adapter.

## Consider doing this together with [T-406](T-406-public-react-bff-path-missing-prefix.md)

Both live in `src/infrastructure/BffCvRepository.ts`, both need the same live-stack verification, and T-406 is what makes this reachable in practice — while the fetch path is wrong the page never renders anything but its error state, so neither defect is observable end-to-end. Separate task files because they are separate defects (routing vs. mapping invariant), but one PR is defensible and cheaper.

## dev-loop notes

- **Developer:** `fullstack-developer`. **Reviewer:** `frontend-architect` (adapter §2). Authoritative CI: **Vercel**.
- `risk: normal`.

## Provenance

Raised by `/code-review` (effort `medium`) during [T-405](T-405-public-react-null-optionals.md)'s review round 1, 2026-08-28, as a **MEDIUM** finding. Filed rather than absorbed per board rule 3: T-405's scope says in as many words that *"any change to `toCv`'s mapping"* is out of scope. Direct precedent — [T-207](T-207-public-types-derived-from-domain-interfaces.md) was filed out of [T-205](T-205-bff-allowlist-section-normalizers.md) for exactly this reason, and revisiting the earlier task's scope note was the whole point of it.

The finding is nonetheless a real instance of the board's recurring shape, one level up from where T-405 found it: **T-405 made a type stronger without making it true.**

---

## Test plan (QA)

Authored by `quality-assurance` at refinement, 2026-09-22. Driver-verified where it makes factual claims.

### The count, settled — **thirteen**, not ten and not six

AC1 contradicts itself: *"every field the domain types declare `string | null` … for all ten, including the six nested."* Three different counts, three different sets. Resolved at refinement:

| Set | n | Fields |
|---|---|---|
| Rule-7 contract-optional | 10 | `Person.headline/location/summary`, `Experience.location/description`, `Education.fieldOfStudy`, `Skill.category`, `Project.description/repoUrl/startDate` |
| **+ rule-3 nullable** (`null` = *"current"*) | **+3** | `Experience.endDate`, `Education.endDate`, `Project.endDate` |
| **Total typed `string \| null`** | **13** | |

**Ruling: normalize all thirteen.** The invariant belongs to the domain type, not to the contract rule that motivated it. `endDate` is the sharpest case — `endDate === null` is how the UI decides to render *"Present"*, so an omitted `endDate` arriving as `undefined` silently stops a current role being marked current. Excluding it would leave the worst failure unguarded.

**"Six nested" is itself an undercount** — six *names* but seven *fields*, because `description` occurs on both `Experience` and `Project`. **Correct the AC checkbox to thirteen when ticking it**, or the next reader repeats the miscount.

### 1. Falsification — prove the new test fails on `master` first

Run the new test against `origin/master` in a throwaway worktree. **Expect all thirteen assertions to fail**, not three: `master` copies `dto.experiences ?? []` verbatim with no per-element mapping, so an omitted nested key stays `undefined` unconditionally. If fewer than thirteen fail, the fixture is wrong (most likely it sets a key it claims to omit) — fix the fixture before trusting any green run afterwards.

### 2. Omitted-key fixture — the mirror of T-405's `allNull`

Keys genuinely **absent** from the object literals: not `null`, not explicit `undefined`, actually missing — what `JSON.parse` yields from a producer that dropped a key. Assert with `toBeNull()` throughout, which fails on `undefined` too, so a partial fix cannot hide behind a looser matcher.

**Two `experiences` elements, deliberately** — the fix adds per-section element mappers, and two elements catch a fix that special-cases index 0 instead of genuinely mapping.

### 3. The `?? null` vs `|| null` trap

Separate fixture using **legitimate empty strings**, one per mapping site (the `Person` literal + four element mappers = five sites; `??` vs `||` is one boolean choice per site).

**Why `''` and not `null`:** `'' ?? null` is `''` but `'' || null` is `null` — the operators disagree on this input, which is the only property that makes the test meaningful. T-210's head-route test used `null` as its "legitimate value" and `null || null` is still `null`, so it passed whichever operator the code used and could not falsify the bug it existed for.

**This test is NOT expected to fail against `master`** — `master` does no scalar coercion at all, so `''` already survives there. It exists to fail against a plausible *wrong fix*. The only thing that proves it bites is the **mutation check**: after the fix lands, locally swap each `?? null` for `|| null`, confirm this test goes red, discard. Report it as a mutation check, not as falsification coverage.

### 4. Regression

- T-405's `allNull` fixture test must pass **unmodified** (`null ?? null` is `null` — low risk, but it is the AC's own wording).
- The four `?? []` guards must still hold. Adversarial shape to rule out: `dto.experiences.map(...) ?? []`, which evaluates `.map` **before** the guard and throws on `undefined`, versus the correct `(dto.experiences ?? []).map(...)`. The existing *"defaults missing section arrays to empty"* test likely covers this — **extend it in place rather than adding a near-duplicate**.

### 5. Live stack — **skip the dedicated stack, piggyback one smoke check**

**Verified by the driver against the running `cvdl_t-406` stack:** `GET :3010/bff/api/v1/people/1/cv` returns **all thirteen keys present on every element — zero rule-7 violations**.

So the live BFF **structurally cannot emit the payload this defect needs**. No stack, isolated or shared, can reproduce the bug or validate the fix against it, and the scope note rules out request-time validation, the only thing that would change that. Standing up a dedicated stack would spend a slot on a check that cannot exercise the change under test.

That is what separates this from its two neighbours: **T-406** was a routing defect, live-reachable, live verification mandatory. **T-405** had zero runtime delta and skipped it. **T-407 has a real runtime delta, but only against payload shapes the live producer cannot emit.**

What the piggyback does buy: the first end-to-end reachability since T-406 merged. A happy-path smoke against real data, at near-zero marginal cost on an already-running stack. **The seed payload carries four genuine nulls** — `experiences[0].endDate`, `projects[0].endDate`, `projects[3].startDate`, `projects[3].endDate` — so real data does exercise the null path, including the *"current role"* case. (QA's report described the live fields as "present, non-null"; they are present, four of them null. The conclusion is unaffected — presence is what matters — but the nulls make the smoke worth more than QA credited it for.)

Report the smoke as a happy-path regression check, **not** as evidence for or against the defect.

> Genuine live coverage of the omitted-key case would need a BFF test double that violates rule 7 on purpose. That is a separate task, not a variant of this stack.

### 6. Full gate

```bash
cd /home/erfeamor/work/curriculum/cv-public-react
npm run lint && npm run typecheck && npm test && npm run build
```

---

## QA record — stage 4, 2026-09-22 (PASS)

Executed by the `quality-assurance` instance that authored the plan, against `cd63d08`. No defects, no bounce-back, `src/` untouched.

| Check | Result |
|---|---|
| §1 falsification (driver-run) | **13 distinct field failures** on `master` + the two-element case — 14 failed / 6 passed |
| §3 mutation, all 13 sites → `\|\| null` | **exactly one** failure: the empty-string test (`Expected: "" / Received: null`) |
| §3 mutation, per-site (5 sites) | each individually killed by that same one test |
| §4 T-405 `allNull` fixture | byte-for-byte unchanged, green |
| §4 guard-order trap | ruled out **empirically**, not by comment — see below |
| §5 piggyback smoke | happy path renders `Jane Doe` end-to-end through the real fix |
| A1 after amendment | lint/typecheck/test/build green, 25 tests |

**The guard-order check was done properly.** Rather than trusting the inline comment, QA confirmed out-of-repo that the wrong order (`dto.experiences.map(fn) ?? []`) *throws* on an absent section — so `getCv()`'s promise rejects and the un-try/caught `await` fails the test. The existing *"defaults missing section arrays to empty"* test therefore genuinely rules out the wrong shape as written. A comment cannot go red; this establishes that something can.

### Two corrections QA made to the driver's own framing

**1. The four seed nulls do not exercise this fix.** The driver asked QA to confirm `experiences[0].endDate`, `projects[0].endDate` and `projects[3].startDate/endDate` "render sanely". They cannot be shown rendering at all — `app/page.tsx` renders only `PersonHeader`, and the four section arrays are deliberate forward-typing (recorded on this repo's "don't flag" list). More importantly they are **present-and-null on the wire, not omitted keys**, so `null ?? null` is `null` with or without T-407. They are already covered by the `allNull` unit test. QA reported this instead of stretching the smoke into defect evidence it does not support.

**2. The `endDate` behaviour is already pinned — what is missing is intent, not coverage.** The three `endDate` cases sit inside the thirteen-way `describe.each`, so a silent revert goes red today. But they are folded anonymously among ten others: an editor who breaks one sees a generic-looking failure with no signal that this field carries a *positive* assertion rather than an empty value.

**Ruling: no pinning test in T-407.** [T-409](T-409-public-react-adapter-validates-required-and-enum.md)'s acceptance criteria replace this exact behaviour, so a test written here would be rewritten within one task — two write cycles over the same three lines. The recommendation is recorded on T-409 as a watch-out instead: when it changes this path, retire those three assertions into **named** tests that state the trade-off, so the intent lives in a test rather than in a comment that goes stale the moment the behaviour changes.
