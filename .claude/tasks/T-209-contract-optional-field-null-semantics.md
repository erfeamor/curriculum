---
id: T-209
title: "Contract: say whether an optional field arrives as null or absent — three repos currently hold three different answers, and one of them cites the contract for a rule it does not contain"
repo: cv-project (meta) + cv-bff-node + cv-public-react
status: todo
owner:
branch: docs/contract-optional-null-semantics
pr:
depends_on: []   # the contract amendment leads; the two type fixes follow it
risk: normal
security_review: false   # no runtime behaviour change; this is a specification gap and two type corrections
---

## The gap

`docs/api-contract.md` shows optional fields in its JSON examples and marks which fields are required — but it **never says what an optional field looks like on the wire when it has no value.** Absent key, or present with `null`? Every consumer has had to guess, and they guessed differently.

**Three repos, three answers, all live today:**

| Repo | Belief | Evidence |
|---|---|---|
| `cv-domain-service` | **emits `null`** | Binds JPA entities directly, declares **no** `@JsonInclude(NON_NULL)` anywhere in `src/main/java`, sets no `spring.jackson.default-property-inclusion` — so Jackson's default `ALWAYS` applies |
| `cv-bff-node` | **key absent** | [T-207](T-207-public-types-derived-from-domain-interfaces.md) transcribed the optionals as `string \| undefined` |
| `cv-public-react` | **always present AND non-null** | `src/domain/cv.ts` types `Skill.category: string` and `Project.startDate: string` — required, not nullable |

`cv-domain-service` is right about its own behaviour; the other two are wrong, in **opposite** directions.

## The part that makes this a contract task and not two bug reports

**`cv-domain-service`'s tests cite the contract for a rule the contract does not contain.**

`EducationControllerTest.java:176` justifies its assertion with — *"contract (\"absent optionals serialize as null\"). Confirmed against live MySQL during stage-4 QA: the body is `{\"fieldOfStudy\":null,...,\"endDate\":null}`"* — and `SkillControllerTest.java:113` says *"category is optional, and an omitted optional serializes as null."*

**Grep `docs/api-contract.md` for that rule and it is not there.** The contract mentions `null` only for `endDate` semantics ("`endDate: null` means current") and for the NULL-placement sort keys in § Ordering. The behaviour is real, it is tested, it was verified live — and it is written down **only in the tests of the repo that implements it**, while being attributed to a document that never stated it.

That is this board's recurring shape one level up: not a green check that measures nothing, but a **specification everyone believes exists**. Compare [T-023](T-023-meta-docs-stale-bff-smoke-path.md), [T-017](T-017-docs-drift-rds-to-selfhosted.md) and [T-003](T-003-ci-docs-reflect-jenkins.md) — docs disagreeing with reality — except here the doc is not wrong, it is *silent*, and three repos filled the silence differently.

## Why it is not merely cosmetic

`cv-public-react` declares `Project.startDate: string` and will receive `null` for any undated project. The contract's § Ordering **explicitly** calls `project.start_date` *"the only nullable date of the three"* and mandates undated projects sort last — so the null case is not hypothetical, it is a case the contract already reasons about elsewhere while leaving its wire representation unstated. A `null` reaching a `string`-typed field is an unchecked runtime lie that TypeScript cannot warn about, in the repo that renders the public CV.

## Scope

**Part 1 — the contract (leads; the others depend on it).** State the rule explicitly in `docs/api-contract.md`, near the design rules where a reader will find it before writing a consumer:

- Whether an optional field is emitted as `null` or omitted. **Ratify what cv-domain-service actually does** (`null`) unless there is a reason to change the producer — changing the producer is a bigger decision and would need its own task.
- Make it explicit that this differs from **required-but-nullable** (`endDate`), which the contract already handles well and which should be named as the contrasting case.
- Say what a consumer may assume: key always present, value possibly `null`.

**Part 2 — `cv-bff-node`.** **Correct the `Domain*` interfaces**, which are the actual root of the imprecision: they spell the optionals `location?: string`, claiming the key may be **absent**, when Jackson `ALWAYS` guarantees it is **present and possibly `null`**. They should read `location: string | null`.

This part was widened after [T-207](T-207-public-types-derived-from-domain-interfaces.md)'s review round 1 (2026-08-27). T-207 typed its `Public*` optionals `string | null | undefined` rather than the intended `string | null`, because `string | null` **does not compile** while `Domain*` says `?: string` — verified: `TS2322: Type 'string | undefined' is not assignable to type 'string | null'`, ×7. T-207 could not fix it (H1 ruling 2 put `Domain*` out of its scope) and correctly declined to improvise. **Once `Domain*` is corrected here, `Public*` can tighten from `string | null | undefined` to `string | null`** — do that in the same PR, and T-207's guard will prove nothing else moved.

**Part 3 — `cv-public-react`.** Correct `src/domain/cv.ts`: `Skill.category` and `Project.startDate` are not required non-null strings. Check every other field in that file against the amended contract at the same time — these two were found by inspection, not by an exhaustive pass.

**Out of scope:** adding `@JsonInclude(NON_NULL)` to cv-domain-service. That would change the producer's wire format and break consumers written against today's behaviour; if anyone wants it, it is a separate task with its own migration.

## Acceptance criteria

- [ ] `docs/api-contract.md` states the optional-field wire rule explicitly, and distinguishes it from required-but-nullable.
- [ ] `cv-domain-service`'s test comments no longer cite the contract for something it does not say — either the citation is now accurate, or it is corrected. **This is the criterion that closes the actual defect**; the rest is consequence.
- [ ] `cv-bff-node`'s `Public*` types match the ratified rule (verify against T-207's merged state first).
- [ ] `cv-public-react`'s `src/domain/cv.ts` matches, with a test or type-level check covering a `null` optional.
- [ ] Each repo's own gates pass (adapter §3); the contract PR lands **first**.

## Watch-outs

- **The contract wins, but here it is silent rather than wrong** — so this is an amendment, not a correction, and no consumer is currently "in violation". Say so, so nobody reads the amendment as blame.
- Amending the contract means a PR against `docs/api-contract.md` **plus** sign-off in the consuming tasks (adapter §4). Sequence it first via `depends_on`.
- `endDate` is already correct everywhere and must not be disturbed.

## dev-loop notes

- **Cross-repo: split at stage 0** per adapter §2. Part 1 is `tech-product-owner` (contract), part 2 `fullstack-developer`, part 3 `fullstack-developer` + `frontend-architect` as reviewer (`cv-public-react` is its review surface).
- `risk: normal`, `security_review: false` — no runtime behaviour changes; the producer is untouched.

## Provenance

Found by `/code-review` (effort `high`) during [T-207](T-207-public-types-derived-from-domain-interfaces.md)'s review round 1, 2026-08-27, as its finding 3 — that T-207's `string | undefined` transcription is unsound because the upstream sends `null`. The driver verified the producer's behaviour in cv-domain-service's tests and config, confirmed `cv-public-react`'s conflicting types, and then found the further fact that makes it a contract task rather than a type fix: **the contract does not contain the rule the producer's tests attribute to it.** T-207 fixes its own half under review; this task closes the specification gap and the third repo.
