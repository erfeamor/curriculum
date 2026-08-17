---
id: T-024
title: "Contract: the skill-assignment PUT row is the one place a request body reads as a response"
repo: cv-project (meta)
status: todo
owner:
branch: docs/contract-skill-put-shape
pr:
depends_on: []
risk: normal
security_review: false
---

## Why this exists

**Promised and never filed.** [T-103](T-103-skills-catalog-and-assignments.md)'s DoR ruling 1 (ratified at refinement) ends with:

> *"A follow-up docs PR clarifies this wording in `docs/api-contract.md`; it does not block this task."*

That PR was never opened and no task held it. Found 2026-08-17 in a board consistency sweep — the ruling is load-bearing for T-103's implementation and its clarification exists only inside a task file, which is exactly the arrangement the contract is supposed to replace (`docs/api-contract.md`'s own header: *"this file wins over any task prose"*).

## The ambiguity

`docs/api-contract.md` § Skills, assignments table:

| Verb | Path | Returns |
|---|---|---|
| GET | `/api/v1/people/{personId}/skills` | 200, array of `{ skillId, name, category, proficiency }` |
| PUT | `/api/v1/people/{personId}/skills/{skillId}` | **200, body `{ "proficiency": "ADVANCED" }` — upsert** |

The column is headed **Returns**, so read literally the PUT returns a bare `{"proficiency": "ADVANCED"}` — a different shape from the GET on the identical resource. But `{"proficiency": "ADVANCED"}` is plainly the *request* body: it is the only cell in the entire document that shows one inline, and every other PUT in the contract is specified as *"200, updated entity"*.

T-103 ruled the response is the **full joined shape** `{skillId, name, category, proficiency}` — same as GET — on the grounds that a GET and a PUT on one resource returning different shapes is an inconsistency no contract text asks for. That ruling is right; it is simply written in the wrong file.

## Scope

`docs/api-contract.md` only. No code — T-103 implements against the clarified text, and if T-103 has already merged by the time this lands, **verify the shipped behaviour matches** rather than assuming it.

- Split the conflated cell: state the request body and the response body separately for the assignment PUT, in whatever form the table can carry (an extra column, or a note below it).
- State that the PUT response is the same shape as the GET element.
- Confirm the 200-on-both-branches semantics (T-103 DoR 2: create and update both return 200, there is no 201 variant) — currently inferable only from the absence of a 201 in the table.
- While in this table, check whether the same conflation exists anywhere else. It should not; the T-103 review found this to be the only instance.
- Update the contract's status/amendment line, as T-006 and T-013 both did.

## Acceptance criteria

- [ ] The assignment PUT's **request** body and **response** body are separately and unambiguously stated.
- [ ] The response shape matches the GET element shape, explicitly rather than by inference.
- [ ] `docs/api-contract.md`'s amendment line records this change with its date and task ID.
- [ ] T-103's DoR ruling 1 is updated to point at the merged contract text instead of promising a future PR.
- [ ] If T-103 has already merged: the shipped response shape is checked against the clarified contract and any divergence is filed as its own task, not fixed here.

## Definition of done

PR open against `master` from `docs/contract-skill-put-shape`, merged, T-103's ruling 1 pointed at it.

## dev-loop notes

- **Developer:** `tech-product-owner` (contract change; no repo persona implements a docs PR — same pattern as T-006 and T-013). **Reviewer:** `backend-developer`, who owns the resource that implements it.
- **`risk: normal`, not `trivial`**, for the reason T-013 gave: the docs fast-path covers prose, but this document is the source of truth three repos build from, and this task changes what an endpoint returns.
- **Sequencing against [T-103](T-103-skills-catalog-and-assignments.md):** ideally lands **before** T-103 is implemented, so the implementer builds from the contract rather than from a task-file ruling. It does **not** block T-103 — the ruling stands either way, which is why it was correctly deferred. If T-103 is claimed first, the two can run in parallel; only the review needs to see both.
- `/code-review` has no purchase on a markdown-only diff — record it as deliberately skipped rather than silently dropped, as T-006 and T-013 did.
