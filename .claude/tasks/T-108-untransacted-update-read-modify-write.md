---
id: T-108
title: "PUT is an untransacted read-modify-write: a concurrent DELETE makes it re-INSERT the row under a new id"
repo: cv-domain-service
status: done
owner: tech-product-owner
branch: fix/transactional-update-paths
pr: https://github.com/erfeamor/cv-domain-service/pull/11
depends_on: []
risk: normal
security_review: false   # concurrency/correctness on an already-authenticated, already-scoped path; no adapter §5 security path in the likely diff. A1 re-checks against the real diff.
checkpoint:
  stage: done   # merged b87d565 (squash of cv-domain-service#11), 2026-09-26 — H2 accepted by the human. QA: PASS 2026-09-26 on real MySQL (slot 0, image labelled 3216902): PUT 200 same id x3; PUT to deleted id 404, no ghost row; 40 racing PUT/DELETE, 0 x 500, counts unchanged, no deadlock/lock-wait in logs; PersonSkill race 10x, 0 x 500; torn down
  repo: cv-domain-service
  branch: fix/transactional-update-paths
  worktree: none   # removed after merge
  commit: b87d565   # squash merge on master (branch head was 3216902)
  pr: https://github.com/erfeamor/cv-domain-service/pull/11
  developer: backend-developer
  reviewers: [code-review, quality-assurance]
  risk: normal
  security_review: false
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: 0
  updated: 2026-09-26T19:45:00+02:00
  budget:
    turns: 80   # --since 2026-09-25T12:49:25.700Z
    total_tokens: 21869911
    subagent_tokens: 0
    spawns: 2   # quality-assurance (shared; reused for the coverage pass via SendMessage) + backend-developer
    status: ok
    checked: 2026-09-26T18:58:00+02:00
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
| `ProjectController.update` | `project/` | on `master` (T-104, merged) |

`PersonSkillController` is **not** in scope and should be checked rather than assumed: T-103 already routes its upsert through a `TransactionTemplate` with a retry, for a different reason (insert-if-absent racing), so it may already be covered or may need a different answer.

## Decide at H1

1. **`@Transactional` on the update path, or `@Version` on the entities?** They fix different halves. `@Transactional` closes failure mode 1 by keeping the read and the write in one persistence context; `@Version` closes failure mode 2 by turning a lost update into a `409`. Doing only the first leaves silent lost updates; doing only the second leaves the resurrection. Price them both — `@Version` adds a column and therefore a **migration**, which this task otherwise does not need.
2. **Does a `409` on optimistic-lock failure need a contract change?** `docs/api-contract.md` design rule 4 enumerates 400/404/204 and § Skills documents a 409 for duplicate catalog names. A new 409 on section PUTs is arguably new contract surface — if so it is a docs PR first, sequenced ahead of this one, per board rule 4.
3. **Is this reachable in the demo as deployed?** `/api/v1/**` requires a Cognito JWT and today the only credentials are the owner's, so two concurrent conflicting PUTs need one user racing themselves. Same severity shape as [T-107](T-107-post-id-cross-person-write.md): latent now, real the moment the demo has a second user, which an admin UI with logins ([T-301](T-301-admin-cv-sections-crud.md)) implies. That argues for fixing it before T-301, not for calling it urgent today. **(2026-09-25: the lane now orders T-108 → T-301.)**

## Acceptance criteria

- [x] All three `update()` paths hold the read and the write in **one** transaction.
- [x] A test proves failure mode 1 is closed — the resurrection is observable, so assert against it directly rather than asserting that an annotation is present.
- [x] Whatever is decided for failure mode 2 at H1 is implemented **or explicitly declined in writing on this task**, not left silent.
- [x] `PersonSkillController` is checked and the finding recorded either way.
- [x] `mvn -B test` and `mvn -B checkstyle:check` pass.

## Provenance

Found by `/code-review` (high effort) on [T-104](T-104-project-resource.md)'s branch, 2026-08-22. **Filed rather than fixed inside T-104 per board rule 3**, and the reasoning is worth keeping: the shape is *verbatim identical* in two resources already on `master`, so fixing only Project would leave three sibling resources with two different concurrency behaviours. That is the same argument [T-107](T-107-post-id-cross-person-write.md) used to decline the structural `@JsonProperty(access = READ_ONLY)` fix — consistency across siblings beat a locally better answer, and the price was that the guard has to be *called*. Here the price is that this task has to be *done*.

**Contrast with T-107, deliberately.** T-107's defect was fixed inside T-102 rather than deferred, because shipping new code carrying a known cross-person *write* would have been following process off a cliff. This one is different on both axes: it is not an authorization hole, and it is not new — it ships identically on `master` today. Deferring it changes nothing about the exposure; deferring T-107 would have added a fourth instance of a live one.

## Test plan — quality-assurance, 2026-09-26 (stage 0)

- [x] **Resurrection repro, per resource (Experience, Education, Project), must fail on master:** deterministic, no sleeps — the row is deleted in a separate, **actually committed** transaction between `update()`'s read and its write. Pre-fix: a new id / extra row / returned id ≠ requested. Post-fix: **404**, no new row, the deleted row stays deleted. Assert on rows and ids, never on the annotation's presence.
- [x] **Trap:** the test must not run inside Spring's per-test rollback transaction (`@DataJpaTest` default) — that folds the "concurrent" delete into the same transaction and false-passes on master too. Use `@Transactional(propagation = NOT_SUPPORTED)` or a `@SpringBootTest` without the wrapper.
- [x] Happy path regression: a plain PUT still returns 200 with the **same** id, on all three.
- [x] `PersonSkillController`: one confirmatory test of the same race (reading suggests the upsert's `TransactionTemplate` and `@Transactional delete` already cover it); record the finding either way.
- [x] Failure mode 2: the written decline (or implementation) exists on this task.
- [x] H2 note: H2 defaults to READ_COMMITTED, InnoDB to REPEATABLE READ. The repro is about transaction boundaries, not snapshot visibility, so H2 proves failure mode 1; it proves nothing about lock waits. Record this.
- [x] Live, isolated stack slot 0 (domain `:8090`, MySQL `:3316`; `AUTH_ENABLED: "false"` from the base compose, verify the override keeps it): PUT → 200 same id; DELETE then GET → 404; best-effort concurrent PUT/DELETE via curl, informative only.
- Gates: `mvn -B test`, `mvn -B checkstyle:check`.

## H1 decisions — human, 2026-09-26

1. **`@Transactional` on the three `update()` paths.** A DELETE committed between the read and the write makes the flush update 0 rows, and that is mapped to **404**. Today the same race returns a 200 under a new id; without the mapping it would be a 500. 404 is already in contract design rule 4, so no contract change is needed.
2. **Failure mode 2 (`@Version` → 409) is DECLINED for this task, in writing:** it needs a `cv-database` migration, which is barred until T-014, and a 409 on section PUTs is new contract surface (board rule 4 puts a contract PR first). Filed as **[T-113](T-113-optimistic-locking-lost-update.md)**, `depends_on: [T-108, T-014]`.
3. Reachability: latent today (one owner credential), fixed before T-301 as the lane orders.
