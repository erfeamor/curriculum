---
id: T-209
title: "Contract: say whether an optional field arrives as null or absent — three repos hold three different answers, and one of them cites the contract for a rule it does not contain"
repo: cv-project (meta)
status: done
owner: tech-product-owner
branch: docs/contract-optional-null-semantics
pr: https://github.com/erfeamor/curriculum/pull/83
depends_on: []   # leads. T-210 and T-405 consume the rule this ratifies.
risk: normal
security_review: false   # documentation only; no code and no runtime behaviour change
checkpoint:
  stage: done
  repo: cv-project (meta)
  branch: docs/contract-optional-null-semantics
  pr: https://github.com/erfeamor/curriculum/pull/83
  developer: tech-product-owner   # driven INLINE by the driver -- docs-only; a spawn would cold-start to rediscover the refinement it just did
  reviewers: [code-review]
  risk: normal
  security_review: false
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  updated: 2026-08-28
  merged: 2230f59
  budget:
    turns: 128
    total_tokens: 10500000
    subagent_tokens: 0
    spawns: 0
    status: ok
    checked: 2026-08-28
    session_note: "Same session that merged T-207 (which ended at ~109 turns). H1 approved all three of T-209/T-210/T-405 in one run."
---

## The gap

`docs/api-contract.md` shows optional fields in its JSON examples and marks which are required (`Required: company, role, startDate.`) — but it **never says what an optional field looks like on the wire when it has no value.** Absent key, or present with `null`? Every consumer has had to guess, and they guessed differently.

**Three repos, three answers, all live today** (re-verified at refinement, 2026-08-28):

| Repo | Belief | Evidence |
|---|---|---|
| `cv-domain-service` | **emits `null`** | Binds JPA entities directly; **no** `@JsonInclude` anywhere in `src/`, no `spring.jackson.default-property-inclusion` in `application.yml` — so Jackson's default `ALWAYS` applies. Asserted by four tests |
| `cv-bff-node` | **key may be absent** | `Domain*` spells them `location?: string`; `Public*` reads `string \| null \| undefined` ([T-207](T-207-public-types-derived-from-domain-interfaces.md)) |
| `cv-public-react` | **always present AND non-null** | `src/domain/cv.ts` types `Skill.category: string` and `Project.startDate: string` — required, not nullable |

`cv-domain-service` is right about its own behaviour; the other two are wrong, in **opposite** directions.

## The part that makes this a contract task and not two bug reports

**`cv-domain-service`'s tests cite the contract for a rule the contract does not contain.**

Grep `docs/api-contract.md` for that rule and it is not there. The document mentions `null` in exactly two places, neither of them this: design rule 3 (`endDate: null` means "current") and § Ordering's NULL-placement sort keys. The behaviour is real, it is tested four times over, and it was verified against live MySQL — but it is written down **only in the tests of the repo that implements it**, while being attributed to a document that never stated it.

That is this board's recurring shape one level up. Compare [T-023](T-023-meta-docs-stale-bff-smoke-path.md), [T-017](T-017-docs-drift-rds-to-selfhosted.md), [T-003](T-003-ci-docs-reflect-jenkins.md) — docs disagreeing with reality — except here the doc is not wrong, it is **silent**, and three repos filled the silence differently.

## Scope — the contract amendment ONLY

State the rule explicitly in `docs/api-contract.md`, in § Design rules where a reader meets it before writing a consumer:

- An optional field with no value is emitted as **`null`, with the key present** — never omitted. **Ratify what cv-domain-service already does.**
- Distinguish it from **required-but-nullable** (`endDate`), which the contract already handles well and which must be named as the contrasting case.
- Say what a consumer may assume: **key always present, value possibly `null`** — and correspondingly, that absence must not be treated as the empty case.
- Add the amendment to the header's amendment list, in the established format.

**Out of scope:** every line of code. `cv-bff-node` is [T-210](T-210-bff-domain-types-null-not-absent.md); `cv-public-react` is [T-405](T-405-public-react-null-optionals.md). Adding `@JsonInclude(NON_NULL)` to cv-domain-service is out of scope **permanently** — it would change the producer's wire format and break consumers written against today's behaviour; if anyone wants it, it is a separate task with its own migration.

## Acceptance criteria

- [x] `docs/api-contract.md` § Design rules states the optional-field wire rule explicitly: key always present, empty value is `null`.
- [x] The rule explicitly contrasts itself with required-but-nullable `endDate`, and says `endDate`'s `null` carries a *meaning* ("current") that an optional's `null` does not.
- [x] The amendment is recorded in the header amendment list.
- [x] **The four cv-domain-service test comments that state or cite this rule now resolve** — a reader following "the contract's *absent optionals serialize as null*" finds it. Verified by grepping the amended contract for the phrase those comments use. **This is the criterion that closes the actual defect.**
- [x] The text says plainly that this is an **amendment to a silence**, not a correction — no consumer was in violation.

## Watch-outs

- **The contract wins, but here it is silent rather than wrong.** Say so, so nobody reads the amendment as blame — and so the two follow-up tasks are understood as adopting a new rule, not fixing a breach.
- `endDate` is already correct everywhere and must not be disturbed.
- Do not describe the *producer's implementation* (Jackson, `@JsonInclude`) in the contract. The contract specifies the wire, not how Spring achieves it — naming the mechanism would make the document stale the moment the producer changes libraries.

## dev-loop notes

- **Owner:** `tech-product-owner` — the contract is this role's surface (adapter §2, cross-repo split note).
- `risk: normal` despite being docs-only: it is the **ratification two other tasks type themselves against**, so a wrong word here propagates into code twice. Not `trivial`.
- Gates: none automated (markdown). Review is `/code-review` on the prose plus a driver grep proving AC4.

## Provenance

Found by `/code-review` (effort `high`) during [T-207](T-207-public-types-derived-from-domain-interfaces.md)'s review round 1, 2026-08-27, as its finding 3 — that T-207's `string | undefined` transcription was unsound because the upstream sends `null`. The driver verified the producer's behaviour, confirmed `cv-public-react`'s conflicting types, and then found the fact that makes it a contract task rather than a type fix: **the contract does not contain the rule the producer's tests attribute to it.**

---

## Stage 0 — refinement, cross-repo split and H1 rulings — 2026-08-28

### The split

Filed as one task spanning three repos; decomposed at stage 0 per adapter §2 into dependency-ordered single-repo tasks, contract first:

| | task | repo | depends_on |
|---|---|---|---|
| 1 | **T-209** (this file) | meta — `docs/api-contract.md` | — |
| 2 | [T-210](T-210-bff-domain-types-null-not-absent.md) | `cv-bff-node` | T-209 |
| 3 | [T-405](T-405-public-react-null-optionals.md) | `cv-public-react` | T-209 |

**T-210 and T-405 are independent of each other** and may run in parallel or in either order once T-209 lands. Neither changes runtime behaviour, so no deployment ordering applies.

### Ruling 1 — the part-4 that isn't: cv-domain-service needs NO code change, and the original AC named the wrong tests

The filed task said the citation defect lives in `EducationControllerTest:176` and `SkillControllerTest:113`. Refinement grepped all four repos' worth of test comments. The actual population is **six comments, of which only two are citations**:

| file:line | text | citation? |
|---|---|---|
| `ProjectControllerTest:171` | *"would break the contract's \"absent optionals serialize as null\""* | **YES** — and the original task **missed this one** |
| `EducationControllerTest:176` | *"the contract (\"absent optionals serialize as null\")"* | **YES** |
| `ExperienceControllerTest:168` | *"omitted optionals serialize back as JSON null, not as missing keys"* | no — states the rule, attributes it to nobody |
| `SkillControllerTest:113` | *"category is optional, and an omitted optional serializes as null"* | no — and the original task **named this one as a citation** |
| `EducationControllerTest:161` | *"omitted optionals must serialize as JSON null, not be dropped"* | no |
| `ProjectControllerTest:217` | *"PUT replaces … so omitted optionals become null"* | no — and it is about **requests**, the case rule 7 explicitly does not govern |

So the filed task was wrong in both directions: it missed a real citation and it flagged a non-citation.

**The resolution is that none of them needs editing.** Both real citations use the identical phrase *"absent optionals serialize as null"*. **The amendment adopts that phrasing**, so the citations resolve and become accurate — which is exactly what the original AC2 offered as its first branch (*"either the citation is now accurate, or it is corrected"*). Correcting the comments instead would be strictly worse: it would delete a phrase two repos already agree on to replace it with a synonym.

*Corrected during review round 1: this table first listed **four** comments and claimed to be the exhaustive grep. It was not — it missed `EducationControllerTest:161` and `ProjectControllerTest:217`. Ruling 1's whole point is that the filed task was imprecise in both directions, so an imprecise correction was worth fixing rather than quietly leaving. `ProjectControllerTest:217` also earned rule 7 its request-side carve-out.*

**This is load-bearing on the amendment's wording**, so it is promoted from a note into AC4 with a grep as its evidence. Writing the rule in different words would satisfy every other criterion and leave the actual defect open — this board's signature failure mode, and the reason it is spelled out here.

### Ruling 2 — tightening `Domain*` to `string | null` is legitimate ONLY because this task ratifies it, and that is not a formality

The sharpest question in the whole item, surfaced at refinement rather than at review.

`cv-bff-node`'s `Domain*` interfaces exist **to describe an upstream the route is designed to distrust** — that is the entire premise of [T-205](T-205-bff-allowlist-section-normalizers.md) and [T-207](T-207-public-types-derived-from-domain-interfaces.md). Retyping them `location: string | null` asserts *the key is always present*, which is a claim **about that distrusted upstream**. On its face that reverses the posture those two tasks established.

**It is nonetheless correct, for one specific reason: after this task the claim is no longer an observation, it is the contract.** T-207 typed to *observed* behaviour and said so in a comment ("THE CONTRACT IS SILENT on null-vs-absent"). Once T-209 lands, `string | null` types to a **ratified specification**, which is what `Domain*` should always have been describing. The distrust that T-205/T-207 institutionalised is about **fields the contract never declared** — a new upstream column, a relation that lost its `@JsonIgnore` — and the allowlist normalizers still handle that completely, untouched.

**The runtime stays defensive regardless**, which is what makes this safe rather than merely arguable: T-205's route-level sparse test (`test/cv.test.ts:475`) feeds fixtures with keys genuinely omitted, and it **passes unchanged** under the refinement probe below. Types moved; the code's tolerance did not.

### Ruling 3 — verified at refinement: the type change compiles, and the real work is the guard test

Not assumed. The probe was applied to `cv-bff-node` @ `dc21c27` and reverted:

```
Domain*:  `?: string`                  ->  `: string | null`
Public*:  `string | null | undefined`  ->  `string | null`
```

**`src/routes/cv.ts` typechecks completely clean** — zero errors in the source. **All three errors land in `test/public-types.test.ts`**, T-207's own guard:

| line | error | cause |
|---|---|---|
| 75 | `TS2578` unused `@ts-expect-error` | the fixture below it no longer errors the way the directive expects |
| 81 | `TS2322` `undefined` not assignable to `string \| null` | `description: undefined` in the omission fixture |
| 117 | `TS2322` same | the `it()` whose entire premise is that `\| undefined` exists |

`npm test`: **72 pass, 1 suite fails to compile** — and the 72 include T-205's four leak tests and its sparse test. **The guard is doing exactly the job T-207 built it for**: it refused to let the type surface move silently. T-210 inherits this as its specification, not as a surprise.

### Ruling 4 — `test/public-types.test.ts`'s second `it()` is REFRAMED, never deleted

Its premise (*"drops an undefined-valued key, so `| undefined` is wire-identical to `?:`"*) dies with `| undefined`. Deleting it is the tempting move and it is wrong: it pins the **runtime** fact that an absent upstream key degrades to an absent wire key rather than to a literal `undefined`, which stays true and stays worth having precisely because the types now say it cannot happen. Keep it with an explicit cast and a comment saying the contract now forbids the input while the runtime still tolerates it. **Weakening or removing a guard to make a type change fit is a review blocker** on T-210.

### Ruling 5 — cv-public-react is 11 fields wrong, not 2, and its test suite cannot see any of them

The filed task named `Skill.category` and `Project.startDate`, flagging them as found "by inspection, not by an exhaustive pass". The exhaustive pass was done at refinement. **All ten optionals in `src/domain/cv.ts` are wrong**, in one of two ways:

- **Required non-null, will receive `null`** (the unchecked lie): `Skill.category`, `Project.startDate`.
- **`?:`, claiming the key may be absent** when it is always present: `Person.headline`, `location`, `summary`; `Experience.location`, `description`; `Education.fieldOfStudy`; `Project.description`, `repoUrl`.

All ten become `string | null` (eight `?:` plus the two bare-`string` ones; the count read "eleven" until review round 1 corrected it). `endDate: string | null` is already correct in all three places and is not touched.

Two facts sharpen the risk assessment in opposite directions:

- **Nothing crashes today.** `PersonHeader` guards with truthiness (`person.headline ? … : null`), so `null` renders correctly, and the section types are **typed but unrendered** — [T-402](T-402-public-react-cv-sections.md) is still `todo`. The defect is latent.
- **Which is exactly why now is the cheap moment.** T-402 will render these fields and will be written against whatever these types say. Fixing them after T-402 means fixing T-402's components too.

**And the suite would not catch it either way**: `BffCvRepository.test.ts`'s payload fixture populates **every optional with a real string**, and `BffCvRepository` casts the response (`as CvDto`) with no runtime validation. So a `null` reaches a `string`-typed field entirely unobserved — one more green check measuring nothing. T-405 therefore requires a **null-bearing fixture**, not merely corrected types.

---

## Review round 1 — 2026-08-28 — 11 findings, all valid, all applied

`/code-review` (effort `medium`) against `docs/contract-optional-null-semantics`. **Every finding was verified by the driver against the actual repos before being applied** — none taken on the reviewer's word. Three of them were counting errors in text written at refinement that same hour.

### The one that mattered most was a sentence added *during* refinement

> `docs/api-contract.md` — **"The rule holds end-to-end"** asserts a guarantee nothing in the BFF enforces.

The driver added that paragraph after self-review, reasoning that without it T-405 would again be typing cv-public-react against inference. **The reasoning was right and the sentence was wrong.** The BFF's normalizers copy `e.location` verbatim; an upstream key that is genuinely absent yields `undefined`, and `JSON.stringify` **drops it from the wire** — behaviour deliberately pinned by T-205's sparse test and one that [T-210](T-210-bff-domain-types-null-not-absent.md) explicitly forbids "fixing" with `?? null`. Written as an unqualified guarantee, a consumer would type `category` as a required key on the strength of it and call `.toLowerCase()` on a missing field the day the producer adds `@JsonInclude(NON_NULL)`.

**This board's signature failure mode, produced by the driver, inside the task written to close a specification gap** — a sentence that looks like a guarantee and measures nothing. Rewritten as *"End-to-end by inheritance, not by enforcement"*, which states plainly that the guarantee rests on the producer and that the BFF neither adds nor removes nulls.

### The rest

| # | severity | finding | resolution |
|---|---|---|---|
| 2 | medium | *"`endDate` is **required** and nullable"* contradicts the document's own `Required:` lists, which omit it — a backend reader adds `@NotNull` and starts 400-ing a current role | Recast: `endDate` is **absent from every `Required:` list** but **always emitted**, and is named as *the one field rule 7 does not govern*; rule 3 keeps ownership |
| 3 | medium | Rule 7 said *"every field **a section** declares"*, but the **person head** fields are declared by no section — and both dependents retype exactly those | Widened to "section resources, the person head, and the BFF's payloads alike"; `/bff/api/v1/people/:id` now named explicitly |
| 4 | medium | **T-210's AC1 was unsatisfiable as filed** — repo-wide wording, `cv.ts`-only scope, while `src/routes/people.ts` holds a *second* `DomainPerson` and a `PublicPerson` with `?:` keys | Verified. T-210 scope + ACs widened to `people.ts`; see its "Why `people.ts` joined the scope" |
| 5 | medium | Nothing stopped [T-402](T-402-public-react-cv-sections.md) being claimed **before** T-405 — the exact expensive ordering T-405's own rationale warns against | `T-405` added to T-402's `depends_on`, file and board row |
| 6 | low-med | cv-public-react has **ten** optionals, not eleven; the `?:` group is **eight**, not nine | Corrected in T-405 (×4) and in ruling 5 above |
| 7 | low | T-210 said "six `Public*` optionals"; there are **ten** (seven section-level + three head) | Corrected, and the scope line now matches AC1 rather than undercounting it |
| 8 | low | The bare bolded *"Absent optionals serialize as null"* read as self-contradictory beside "never as a missing key" — "absent" meaning *value* in one clause and *key* in the other | Marked explicitly as the phrase the producer's tests cite, so it reads as the cross-reference it is (which is its only job — AC4) |
| 9 | low | *"must not treat a missing key as the empty case"* was unqualified, but **requests** are the opposite: `PUT` replaces, so an omitted optional in a request body *is* the empty case | Rule 7 now carves requests out explicitly, citing § Non-goals |
| 10 | low | Ruling 1 above claimed an exhaustive grep found **four** comments. There are **six** | Corrected, with the two additions in the table. `ProjectControllerTest:217` is what earned finding 9 its carve-out |
| 11 | low | `cv-public-react/src/domain/cv.ts`'s header cites `GET /api/v1/people/:id/cv`; the ratified public path has been `/bff/…` since T-013 | Folded into T-405's scope — that comment is being rewritten anyway |

**Findings 4, 6, 7 and 10 were each re-counted by the driver against the source** (`people.ts` read in full; `grep -c` on both type files and on the cv-domain-service test comments) rather than accepted. All four confirmed, including the three that contradicted the driver's own refinement.

### Acceptance criteria re-verified after the rewrite

| AC | evidence |
|---|---|
| 1 — rule stated in § Design rules | rule 7 present |
| 2 — contrasts required-but-nullable | `endDate` paragraph, recast per finding 2 |
| 3 — amendment recorded in header | `**2026-08-28 — T-209** (optional fields: `null`, key always present)` |
| 4 — **the citations resolve** | `grep "absent optionals serialize as null" docs/api-contract.md` → **1 hit** (was **0** on `HEAD`, driver-verified red-before-green); the two citing tests use that exact phrase |
| 5 — amendment-to-a-silence, not blame | closing italic paragraph |

**Open findings: 0.**
