---
id: T-108
title: "PUT is an untransacted read-modify-write: a concurrent DELETE makes it re-INSERT the row under a new id"
repo: cv-domain-service
status: todo
owner:
branch: fix/transactional-update-paths
pr:
depends_on: []
risk: normal
security_review: false   # concurrency/correctness on an already-authenticated, already-scoped path; no adapter §5 security path in the likely diff. A1 re-checks against the real diff.
---

## Goal

`update()` in **three** person-scoped resources reads an entity in one transaction and saves it in another. Under `open-in-view: false` — which `application.yml` sets — that is a detached-entity `merge()`, and it has two failure modes.

## The two failure modes

`application.yml` sets `spring.jpa.open-in-view: false` and no `update()` method carries `@Transactional`, so **every repository call is its own transaction**:

```
tx1  requirePerson(personId)
tx2  findByIdAndPersonId(id, personId)   -> returns a DETACHED entity
     ...field copying happens outside any transaction...
tx3  save(existing)                      -> a separate merge()
```

1. **A concurrently deleted row is resurrected under a new id.** Request A reads project 5. Request B `DELETE`s project 5 and commits. A's `merge()` then does `session.get(Project, 5)`, finds nothing, and Hibernate's `DefaultMergeEventListener` falls through to `entityIsTransient` → `persist`. With `GenerationType.IDENTITY` that issues an **INSERT**. The client gets a `200` whose `id` is **not** the `{id}` it PUT, and a row the DELETE was supposed to have removed reappears.
2. **Plain lost update between two concurrent PUTs.** No `@Version` on any of these entities, so the second write silently overwrites the first with no signal to either client.

## Scope — all three resources, or none

This is the whole reason it is a task rather than a line in someone's PR.

| Resource | Where | Status |
|---|---|---|
| `ExperienceController.update` | `experience/` | on `master` (T-101) |
| `EducationController.update` | `education/` | on `master` (T-102) |
| `ProjectController.update` | `project/` | T-104 |

`PersonSkillController` is **not** in scope and should be checked rather than assumed: T-103 already routes its upsert through a `TransactionTemplate` with a retry, for a different reason (insert-if-absent racing), so it may already be covered or may need a different answer.

## Decide at H1

1. **`@Transactional` on the update path, or `@Version` on the entities?** They fix different halves. `@Transactional` closes failure mode 1 by keeping the read and the write in one persistence context; `@Version` closes failure mode 2 by turning a lost update into a `409`. Doing only the first leaves silent lost updates; doing only the second leaves the resurrection. Price them both — `@Version` adds a column and therefore a **migration**, which this task otherwise does not need.
2. **Does a `409` on optimistic-lock failure need a contract change?** `docs/api-contract.md` design rule 4 enumerates 400/404/204 and § Skills documents a 409 for duplicate catalog names. A new 409 on section PUTs is arguably new contract surface — if so it is a docs PR first, sequenced ahead of this one, per board rule 4.
3. **Is this reachable in the demo as deployed?** `/api/v1/**` requires a Cognito JWT and today the only credentials are the owner's, so two concurrent conflicting PUTs need one user racing themselves. Same severity shape as [T-107](T-107-post-id-cross-person-write.md): latent now, real the moment the demo has a second user, which an admin UI with logins ([T-301](T-301-admin-cv-sections-crud.md)) implies. That argues for fixing it before T-301, not for calling it urgent today.

## Acceptance criteria

- [ ] All three `update()` paths hold the read and the write in **one** transaction.
- [ ] A test proves failure mode 1 is closed — the resurrection is observable, so assert against it directly rather than asserting that an annotation is present.
- [ ] Whatever is decided for failure mode 2 at H1 is implemented **or explicitly declined in writing on this task**, not left silent.
- [ ] `PersonSkillController` is checked and the finding recorded either way.
- [ ] `mvn -B test` and `mvn -B checkstyle:check` pass.

## Provenance

Found by `/code-review` (high effort) on [T-104](T-104-project-resource.md)'s branch, 2026-08-22. **Filed rather than fixed inside T-104 per board rule 3**, and the reasoning is worth keeping: the shape is *verbatim identical* in two resources already on `master`, so fixing only Project would leave three sibling resources with two different concurrency behaviours. That is the same argument [T-107](T-107-post-id-cross-person-write.md) used to decline the structural `@JsonProperty(access = READ_ONLY)` fix — consistency across siblings beat a locally better answer, and the price was that the guard has to be *called*. Here the price is that this task has to be *done*.

**Contrast with T-107, deliberately.** T-107's defect was fixed inside T-102 rather than deferred, because shipping new code carrying a known cross-person *write* would have been following process off a cliff. This one is different on both axes: it is not an authorization hole, and it is not new — it ships identically on `master` today. Deferring it changes nothing about the exposure; deferring T-107 would have added a fourth instance of a live one.
