---
id: T-205
title: "BFF: the aggregate's section normalizers are denylists — make them allowlists like every other normalizer in the repo"
repo: cv-bff-node
status: todo
owner:
branch: fix/allowlist-section-normalizers
pr:
depends_on: [T-201]   # T-201 introduces the code this changes. Not a scheduling nicety: the four normalizers do not exist until it merges.
risk: normal
security_review: true   # the route this protects is ANONYMOUS by contract (T-013) — the same reasoning that set T-201's flag
---

## Goal

`src/routes/cv.ts`'s four section normalizers strip **one named key** and pass everything else through:

```ts
const stripExperience = ({ id: _id, ...rest }: DomainExperience): PublicExperience => rest;
```

TypeScript interfaces are erased at runtime, so `...rest` carries **whatever the domain service actually returned**, not what `DomainExperience` declares. Make all four construct their output explicitly instead — the way `normalizePerson` does **in the same file**, and `normalize()` does in `src/routes/people.ts`.

## Why this is worth a task rather than a comment

**It is the only denylist in a codebase of allowlists**, and it sits on the one route with no authentication in front of it.

The real cost is a coupling that is enforced nowhere: **`cv-domain-service`'s entity shape is now the BFF's public anonymous payload.** That service binds JPA entities directly with no DTO layer — an accepted trade-off, documented in `Experience.java`'s own class comment — so a column added to an entity, or a relation someone forgets to `@JsonIgnore`, reaches unauthenticated public traffic with **no change in this repo, no review in this repo, and no test failure here**.

**The existing test cannot catch it either**, and that is the part worth being precise about. T-201's *"leaks no internal id, personId, skillId or email"* test asserts over the **serialized response** — which reads as strong — but the upstreams it asserts against are **mocked to the declared interface**. The mock can only contain fields the test author already thought of, so the test proves the normalizers strip the keys it knows about and is structurally incapable of proving they strip the ones nobody declared. That is this board's recurring *"green check that measures nothing"* shape ([T-107](T-107-post-id-cross-person-write.md)'s mock-measuring test, [T-109](T-109-ordering-tiebreak-unevidenced-siblings.md)'s tiebreak assertions, [T-028](T-028-qa-env-generator-worktree-build-context.md)'s AC1, [T-201](T-201-bff-cv-aggregate.md)'s own struck parallelism criterion), one layer removed.

## Not currently exploitable — and that is why it is a task and not a finding

Raised during T-201's `/security-review` (2026-08-27) and **deliberately not reported as HIGH or MEDIUM**. Checked at the time: `cv-domain-service` `@JsonIgnore`s the `person` relation on the section entities, so today's payloads match the declared interfaces exactly and nothing leaks. The review's bar is *">80% confident of actual exploitability"*, and a future-regression path does not meet it.

**Do not let that framing shrink the task.** The reason it is filed is that the failure mode is silent, cross-repo, and lands on anonymous traffic — the cost of being wrong is disclosure, and the fix is a few lines.

## Scope

- Rewrite `stripExperience`, `stripEducation`, `stripSkill`, `stripProject` to construct their result field-by-field from the contract's declared fields.
- Keep the public types as they are — they already describe the intended shape correctly; it is only the runtime that disagrees with them.
- **Add a test that would have caught the gap**: feed a mocked upstream carrying a field the interface does **not** declare (e.g. `personId`, or an invented `internalNote`) and assert it is absent from the response. Without this the change is unverified in exactly the way the current test is.

**Out of scope:** the second option considered and not taken at T-201's review — a contract test pinning `cv-domain-service`'s actual response keys. That is a cross-repo integration check with a different owner and a different failure mode; if it is still wanted after this lands, file it separately. **Also out of scope:** `normalizePerson` and `people.ts`'s `normalize()`, which are already allowlists and need no change.

## Acceptance criteria

- [ ] All four section normalizers construct their output explicitly; no `...rest` spread of an upstream payload survives in `src/routes/cv.ts`.
- [ ] **A test feeds an undeclared field through each of the four sections and asserts it does not appear in the response.** This must be a test that FAILS against the current denylist implementation — verify that by running it against `master` before changing the code, and say so in the PR.
- [ ] T-201's existing contract-shape and no-leak tests still pass unchanged — this task must not alter the documented payload.
- [ ] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass.

## Watch-outs

- **A field-by-field rebuild silently drops optional fields if one is forgotten**, which is the mirror-image defect and would break the contract shape rather than leak. T-201's field-for-field contract test is the guard against that; do not weaken it while making this change.
- The contract is the authority on which fields belong in each section — `docs/api-contract.md` §§ Experience, Education, Projects, Skills. Do not derive the list from the TypeScript interfaces, which are what this task exists to stop trusting.

## Definition of done

PR open against `master` from `fix/allowlist-section-normalizers`, GitHub Actions green, task updated.

## dev-loop notes

- **Developer:** `fullstack-developer` (adapter §2 — `cv-bff-node`). **Reviewers:** `/code-review` + `fullstack-developer` + `/security-review`.
- `risk: normal`, and the diff is small — but it is a **public-payload** change on an anonymous route, so it does not take the trivial fast-path.
- Gates (adapter §3): the `cv-bff-node` row — lint, typecheck, test, build. Authoritative CI: **GitHub Actions**.

## Provenance

Raised by `/security-review` during [T-201](T-201-bff-cv-aggregate.md)'s review round, 2026-08-27, recorded there as *"Recorded, deliberately not raised as a finding"* with two suggested options. Filed on the human's instruction, taking the first option (allowlist the normalizers) and leaving the second (a cross-repo contract test) unfiled. Filed rather than fixed inside T-201 per board rule 3 — T-201's acceptance criteria are its scope, and they do not cover this.
