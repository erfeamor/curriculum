---
id: T-107
title: "POST with a client-supplied id overwrites another person's row (person, experience)"
repo: cv-domain-service
status: in_review
owner: backend-developer
branch: fix/reject-client-supplied-id
pr: https://github.com/erfeamor/cv-domain-service/pull/6
checkpoint:
  stage: pr
  dor_answers: |
    §1 Person IS exposed the same way, minus the cross-person dimension (no parent), so the
       damage is an unauthorised overwrite of an arbitrary person record. Same 400.
    §2 Reject with 400, matching what T-102 shipped for education.
    §3 LOCAL guards via a shared common/ClientSuppliedIds — one home for the rule and its
       explanation, called from all three controllers. @JsonProperty(access = READ_ONLY) was
       CONSIDERED AND DECLINED, and the reasoning is recorded in that class: it protects a new
       resource whose author never read the rule, which is a real advantage, but it discards a
       supplied id in SILENCE, so a client that sent one believing it was updating gets a 201 for
       a different row and no signal it was wrong. Design rule 4 puts client mistakes in the 400
       family. The cost of the choice is that it must be CALLED — hence the DoR notes added to
       T-103 and T-104.
  proof: |
    Demonstrated against live MySQL 8.4, not argued. Guard temporarily removed, then restored.
      POST /api/v1/people/2/experiences with the id of a row owned by person 3:
        before   id=1  person_id=3  company=VictimCo  role=Staff Engineer
        request  201, body {"id":1,"company":"PWNED",...}
        after    id=1  person_id=2  company=PWNED     role=owned
        GET /people/3/experiences -> []      <- the victim's CV entry is gone
      Guard restored: same request 400, row untouched. Person and education verified identically,
      each asserted against the ROW and not just the status code (T-107 acceptance criterion).
  test_replaced: |
    ExperienceControllerTest.clientSuppliedIdInThePostBodyIsIgnored asserted 201 with the client's
    id "ignored" AND PASSED — this is why the defect survived three weeks in master. Its comment
    claimed "the entity exposes no id mutator, so Jackson ignores it"; Jackson does not. It passed
    because givenSaveReturnsWithId(5L) stubs save() to return id 5 whatever it receives, so the
    assertion measured the mock. Replaced, with the old body kept in a comment where it stood.
  gates: "mvn -B test 65 passed 0 failures · checkstyle 0 violations · both new tests confirmed RED first (201 where 400 required) · Jenkins SUCCESS on rebuild"
  ci_note: "PR-6 build #1 failed with 'No build record could be located' — T-026's cold-start defect, REPRODUCED (the reaper had stopped the box at 09:59:17 and this push woke it). Not related to this change: a rebuild on the warm box went green. Third data point, recorded in T-026."
depends_on: []
risk: high
security_review: true
---

## Why this exists

**Filed 2026-08-20 from T-102's `/code-review`.** The same defect was fixed for `education` inside T-102 (it was new code, and shipping a known cross-person write would have been indefensible). **`PersonController` and `ExperienceController` have it identically, and both are already merged to `master`.**

It had been on the board since T-102's refinement as a flagged-not-fixed nuisance — *"a client-supplied `\"id\": 999` in a POST body must not override the generated id"*. That description is wrong about the impact, which is why it sat unfixed: **it is not an id override, it is an authenticated cross-person write.**

## The mechanism, verified rather than argued

`Experience.id` / `Person.id` are private fields with a getter and **no setter**, which reads as un-bindable. Jackson's `MapperFeature.INFER_PROPERTY_MUTATORS` is on by default and binds the private field anyway. Confirmed empirically against the resolved jackson-databind (2.17.2 under Boot 3.3.2):

```
deserialize {"id":999,"institution":"UNED","degree":"BSc"}  ->  getId() == 999
```

From there:

1. A non-null id makes `SimpleJpaRepository.save()` evaluate `isNew() == false`, so it calls `em.merge()` instead of `persist()`.
2. `create()` has already set the owning person to **the caller's**.
3. The resulting statement is `UPDATE experience SET person_id = <caller>, … WHERE id = 999`.

**Person 2's row is overwritten and reassigned to person 1, and the caller gets `201` with the victim's id in the response body.**

`findByIdAndPersonId` scopes PUT and DELETE against exactly this. POST has no existing row to scope to, so it had no guard — the one verb where the protection was absent is the one that can create the reference.

## Scope

`PersonController.create` and `ExperienceController.create`. **Not** `education` — fixed in T-102 (`cbe077f`), and that fix is the pattern to copy:

```java
if (entity.getId() != null) {
    throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
            "id is assigned by the server and must not be supplied");
}
```

PUT needs no equivalent guard in any of the three: it copies fields onto the row returned by the scoped lookup and saves *that*, so the request body's id is never the id written. Confirm this holds in `person/` before assuming it — `Person` is not person-scoped and its update path differs.

## Definition of Ready — settle before code

1. **Is `Person` actually exposed the same way?** It is not a person-scoped child, so there is no cross-person dimension — the worst case is overwriting an arbitrary person row, which is still an unauthorised write but a different shape. Decide whether it warrants the same 400 or whether `POST /people` with an id is merely nonsense to reject.
2. **Reject with 400, or null the id and carry on?** T-102 chose 400: silently ignoring means a client that mistakenly sends an id believes it updated something. Diverging here would give three resources two behaviours — pick one and apply it to all three.
3. **Is a global fix better than three local ones?** A `@JsonProperty(access = READ_ONLY)` on each `id`, or disabling `INFER_PROPERTY_MUTATORS`, closes the class rather than the instances — and would also cover T-103/T-104 before they are written. Weigh that against a global Jackson setting affecting every payload in the service.

## Acceptance criteria

- [ ] `POST /api/v1/people/{personId}/experiences` with an `id` belonging to **another person** returns 400 and leaves the victim's row byte-for-byte unchanged — asserted against the row, not just the status code.
- [ ] The equivalent decision for `POST /api/v1/people` is implemented and its rationale recorded.
- [ ] Each guard has a test that was **confirmed red first** — this defect's whole history is that it looked harmless, so a test that never failed proves nothing.
- [ ] Whatever DoR 3 decides is applied consistently across person, experience and education.
- [ ] `mvn -B test` and `mvn -B checkstyle:check` pass; Jenkins green.

## Definition of done

PR merged, with the cross-person overwrite demonstrated closed by test.

## dev-loop notes

- **Developer:** `backend-developer`. **Reviewers:** `/code-review` + **`/security-review`** — this is an authorisation boundary.
- **`risk: high`** despite being a small diff: it is an unauthorised write against live data, on resources already in `master`.
- **Mitigating context, not an excuse:** the domain service requires a valid Cognito JWT for every `/api/v1/**` path (`AUTH_ENABLED=true` in the deployed config), and since [T-022](T-022-domain-service-origin-bypasses-cloudfront.md) it is only reachable through CloudFront. So this is an *authenticated* attack, and today the only credentials are the owner's. It becomes materially worse the moment the demo has more than one user.
- **Do before [T-103](T-103-skills-catalog-and-assignments.md) and [T-104](T-104-project-resource.md)** if DoR 3 picks the global fix — otherwise those two resources will be written with the same hole and need the same retrofit.
