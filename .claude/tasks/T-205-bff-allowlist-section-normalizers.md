---
id: T-205
title: "BFF: the aggregate's section normalizers are denylists — make them allowlists like every other normalizer in the repo"
repo: cv-bff-node
status: done
owner: fullstack-developer
branch: fix/allowlist-section-normalizers
pr: https://github.com/erfeamor/cv-bff-node/pull/6
depends_on: [T-201]   # T-201 introduces the code this changes. Not a scheduling nicety: the four normalizers do not exist until it merges.
risk: normal
security_review: true   # the route this protects is ANONYMOUS by contract (T-013) — the same reasoning that set T-201's flag
checkpoint:
  stage: done
  repo: cv-bff-node
  branch: fix/allowlist-section-normalizers
  pr: https://github.com/erfeamor/cv-bff-node/pull/6
  merged: 68dbfd2   # squash-merged 2026-08-27; admin bypass (ruleset needs 1 approving review + code-owner review + signed commits — no second human on this repo, and GitHub blocks the author self-approving; same route PR #5 took)
  commit: b6fd1f6   # A1 green: lint 0, typecheck 0, test 36/36, build 0. Red-before-green re-verified by the driver: the four leak tests fail against master's normalizers, pass against b6fd1f6.
  developer: fullstack-developer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 1
  open_findings: 0   # review round 1: 1 finding (LOW, non-blocking) — filed as T-207, not absorbed (board rule 3)
  qa_bounces: 0
  fix_attempts: 0
  env_slot: 0
  updated: 2026-08-27
  budget:
    turns: 88
    total_tokens: 7200000
    subagent_tokens: 85887
    spawns: 2
    status: ok
    checked: 2026-08-27
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
- [ ] **The comment above the four normalizers is deleted with the code it defends.** `cv.ts` currently argues the denylist is deliberate — *"Destructuring rather than rebuilding field-by-field is deliberate: a new contract field arrives in the payload without an edit here, and the only way an internal id leaks is if it is named something these do not strip"*. That reasoning is what this task overturns; leaving it strands a defence of the defect in the file. Replace it with a comment stating why the rebuild is an allowlist. **Added at H1 on the human's instruction, 2026-08-27** — a reviewer should treat leaving it as a finding.
- [ ] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass.

## Watch-outs

- **A field-by-field rebuild silently drops optional fields if one is forgotten**, which is the mirror-image defect and would break the contract shape rather than leak. T-201's field-for-field contract test is the guard against that; do not weaken it while making this change.
- The contract is the authority on which fields belong in each section — `docs/api-contract.md` §§ Experience, Education, Projects, Skills. Do not derive the list from the TypeScript interfaces, which are what this task exists to stop trusting.

## Definition of done

PR open against `master` from `fix/allowlist-section-normalizers`, GitHub Actions green, task updated.

## dev-loop notes

- **Developer:** `fullstack-developer` (adapter §2 — `cv-bff-node`). ~~**Reviewers:** `/code-review` + `fullstack-developer` + `/security-review`.~~ **Reviewer set settled at H1, 2026-08-27: `/code-review` + `/security-review`, run as skills in-session — no separate `fullstack-developer` reviewer spawn.** The adapter's `max_spawns_per_task: 3` binds, and the three that earn their place are QA's test plan, the developer, and stage-4 exploratory QA. The dropped lens was the weakest of the three named: it would have been the same persona reviewing its own authored code, and on an anonymous public payload `/security-review` is the lens that matters. Stage-4 QA was explicitly preserved over it — it is the only stage where real cv-domain-service payloads are compared against the BFF's output unmocked, which is the very coupling this task exists to sever.
- `risk: normal`, and the diff is small — but it is a **public-payload** change on an anonymous route, so it does not take the trivial fast-path.
- Gates (adapter §3): the `cv-bff-node` row — lint, typecheck, test, build. Authoritative CI: **GitHub Actions**.

## Provenance

Raised by `/security-review` during [T-201](T-201-bff-cv-aggregate.md)'s review round, 2026-08-27, recorded there as *"Recorded, deliberately not raised as a finding"* with two suggested options. Filed on the human's instruction, taking the first option (allowlist the normalizers) and leaving the second (a cross-repo contract test) unfiled. Filed rather than fixed inside T-201 per board rule 3 — T-201's acceptance criteria are its scope, and they do not cover this.

---

## Test plan (QA)

Authored by `quality-assurance` at stage 0, 2026-08-27 — this is the plan QA itself executes at stage 4. Verified against the real `test/cv.test.ts`: the `ok()` helper, `mockHappyPath()` and the `PERSON`/`EXPERIENCES`/`EDUCATIONS`/`SKILLS`/`PROJECTS` fixtures all exist as written, so the snippets below drop into the existing file with no new test infrastructure.

### 1. The regression test that is the point of the task

New `describe` block in `test/cv.test.ts`, sibling to the existing one, reusing the same `mockHappyPath`/`ok` helpers and the same `global.fetch` mock/restore pattern.

**One `it` per section — four tests, not one parameterized test**, so a failure names the section directly. For each, override exactly one of the five upstream mocks with the existing fixture **plus two undeclared keys**: `personId` (the realistic leak — the JPA `person` relation on the entity) and `internalNote` (an arbitrary future column, standing in for "a field nobody has invented yet"). The other four upstreams keep their normal fixtures.

```ts
it('strips fields the contract does not declare from experiences, even ones nobody named', async () => {
  const leaky = [{ ...EXPERIENCES[0], personId: 1, internalNote: 'do not ship' }];
  global.fetch = jest.fn()
    .mockResolvedValueOnce(ok(PERSON))
    .mockResolvedValueOnce(ok(leaky))
    .mockResolvedValueOnce(ok(EDUCATIONS))
    .mockResolvedValueOnce(ok(SKILLS))
    .mockResolvedValueOnce(ok(PROJECTS)) as unknown as typeof global.fetch;

  const res = await request(createApp()).get('/bff/api/v1/people/1/cv');

  expect(res.body.experiences[0]).not.toHaveProperty('personId');
  expect(res.body.experiences[0]).not.toHaveProperty('internalNote');
  expect(JSON.stringify(res.body)).not.toContain('do not ship');
});
```

Repeat for **education** (`{ ...EDUCATIONS[0], personId: 1, internalNote: 'do not ship' }`), **skills** (`{ ...SKILLS[0], personId: 1, internalNote: 'do not ship' }` — a skill *assignment* row carries a person FK too, and `skillId` is the leak the existing test already covers), and **projects** (`{ ...PROJECTS[0], personId: 1, internalNote: 'do not ship' }`).

Assertion shape: `not.toHaveProperty` on the specific array element for both injected keys, plus one `JSON.stringify(res.body)).not.toContain('do not ship')` per test as a value-level backstop — mirroring the existing "leaks no internal id" test's habit of asserting over the serialized body, not just parsed keys.

**Red-before-green, concretely (AC2 requires this and requires saying so in the PR).** Create the branch, write the four tests first with **no production edit**, run `npm test -- -t "does not declare"` from `cv-bff-node/`, and confirm all four **fail** against the unmodified normalizers — the denylist spreads `...rest`, so both injected keys pass straight through. The branch starts identical to `master`, so **that red run *is* the master run**; no separate checkout or stash choreography is needed. Paste the failing output into the PR description, then implement the rebuild and re-run green.

### 2. The mirror-image defect: a forgotten optional field, silently dropped

The existing `matches the contract example field-for-field` test is **not sufficient** on its own — its fixtures populate every optional field, so a rebuild that forgot `description` would still pass it, because the forgotten field simply never gets asserted. It must not be weakened (per the watch-out), so leave it **byte-for-byte as-is** and add a **new, second** test exercising the opposite fixture shape: upstream payloads with every optional field omitted.

```ts
it('preserves every contract field for a sparse payload with no optional fields set', async () => {
  const sparseExperience = { id: 7, company: 'ACME', role: 'Backend Engineer', startDate: '2022-01-01', endDate: null };
  const sparseEducation  = { id: 3, institution: 'UNED', degree: 'BSc', startDate: '2015-09-01', endDate: null };
  const sparseSkill      = { skillId: 42, name: 'Java', proficiency: 'ADVANCED' };
  const sparseProject    = { id: 9, name: 'cv-project', endDate: null };

  global.fetch = jest.fn()
    .mockResolvedValueOnce(ok(PERSON))
    .mockResolvedValueOnce(ok([sparseExperience]))
    .mockResolvedValueOnce(ok([sparseEducation]))
    .mockResolvedValueOnce(ok([sparseSkill]))
    .mockResolvedValueOnce(ok([sparseProject])) as unknown as typeof global.fetch;

  const res = await request(createApp()).get('/bff/api/v1/people/1/cv');

  expect(res.body.experiences[0]).toEqual({ company: 'ACME', role: 'Backend Engineer', startDate: '2022-01-01', endDate: null });
  expect(res.body.education[0]).toEqual({ institution: 'UNED', degree: 'BSc', startDate: '2015-09-01', endDate: null });
  expect(res.body.skills[0]).toEqual({ name: 'Java', proficiency: 'ADVANCED' });
  expect(res.body.projects[0]).toEqual({ name: 'cv-project', endDate: null });
});
```

The two bound the rebuild from both directions: the untouched happy-path test proves every declared field survives **when present**; this sparse test proves the required and nullable fields still shape correctly and no stray `undefined`-valued key leaks **when optionals are absent**. A forgotten `description` would pass the sparse test by accident but fail the happy-path test loudly — which is precisely why that test must not be edited.

> **Review-time read-the-diff item, not a fifth test:** `endDate` is required-but-**nullable**, not optional. A rebuild written `e.endDate || null` instead of a direct `e.endDate` would collapse a legitimate empty string to `null` — a latent bug neither test catches, against a value cv-domain-service is not known to emit. Catch it by reading the diff.

### 3. Non-regression — must pass unchanged

All **twelve** existing `it` blocks in `test/cv.test.ts` must pass **without modification**: the contract-shape test, the no-leak test, the four-section-paths test, the parallel-dispatch test, the order-passthrough test, both person-404 tests, the three 502 tests, and the two id-guard tests.

**The only acceptable diff inside `test/cv.test.ts` is additive** — the four AC2 leak tests plus the one sparse test above. A diff touching any existing fixture value, expected body, or assertion style is a **red flag at review**: AC3 says the documented payload must not change, and these tests are the proof of it.

### 4. The `undefined`-key question — decided

**Assert against `res.body` (the parsed HTTP response), use `toEqual` throughout, and do not export the normalizers for direct unit testing.**

`res.body` is `JSON.parse` of what `res.json(body)` serialized, and `JSON.stringify` never emits a key whose value is `undefined` — the key is dropped before it reaches the wire. So a rebuild like `{ location: e.location, … }` with `e.location === undefined` yields, in `res.body`, an object with **no `location` key at all**, not a key present-but-undefined. Since `JSON.parse` can never reconstruct an own property with value `undefined`, `toEqual` and `toStrictEqual` are **behaviorally identical here** — `toStrictEqual`'s only extra strictness has nothing to bite on. Using it would add no safety and would diverge from the file's convention for no reason.

> **If the developer instead exports the four normalizers to unit-test them directly, flag it at review.** An in-memory object literal *can* carry an explicit `undefined`-valued key, and at that point the two matchers diverge and this ambiguity reopens. Every new assertion routes through `supertest` + `res.body`, like every existing test in the file.

### 5. Stage-4 exploratory QA against the live isolated stack

**Corrected against adapter §6** — QA's draft omitted `COMPOSE_PROJECT_NAME` and used the wrong override filename. The generator emits the `cvdl_` prefix (`PROJECT_PREFIX = "cvdl_"`, `qa-env-override.py:70`) and prints the exact commands; use what it prints:

```bash
python3 scripts/qa-env-override.py --task T-205 --slot 0 \
  --smoke bff:/bff/api/v1/people/1/cv
COMPOSE_PROJECT_NAME=cvdl_T-205 docker compose \
  -f docker-compose.dev.yml -f docker-compose.override.cvdl_T-205.yml up --build -d
```

Slot 0 → BFF host **3010**, domain-service host **8090**. Dev seeds (`cv-database/sql/dev-seeds/`, Flyway `afterMigrate`) give person `1` its sections. **This is the one stage where the payloads are not mocked** and the cross-repo coupling is observable for real.

```bash
# 1. Raw domain-service sections — the actual upstream shape, unmocked.
for s in experiences educations skills projects; do
  echo "== $s"; curl -s localhost:8090/api/v1/people/1/$s | jq '.[0] | keys'
done

# 2. BFF aggregate — the normalized public payload.
curl -s localhost:3010/bff/api/v1/people/1/cv | jq \
  '{exp: (.experiences[0]|keys), edu: (.education[0]|keys), sk: (.skills[0]|keys), pr: (.projects[0]|keys)}'
```

Compare by hand: **step 2's key sets must be a proper subset of step 1's**, restricted exactly to the contract-declared names. Confirm specifically that `id` is absent from all four sections of step 2, `personId` is absent from step 2 (it appears in step 1 if any entity's `person` relation loses its `@JsonIgnore` — the exact regression this task defends against), and `skillId` is present in step 1's skills but absent from step 2's. Re-run the emitted smoke curl; check `200` and `content-type: application/json`.

Teardown: same `-f` pair plus `down -v`, with the same `COMPOSE_PROJECT_NAME` — the isolated project name is what keeps this off a developer's default-port stack and away from the shared Grafana volume the meta CLAUDE.md warns about.

### 6. Out of scope — restated so it is not silently expanded

- **No cross-repo contract test** pinning cv-domain-service's actual JSON keys from inside cv-bff-node's suite. That is the task's own deliberately-unfiled second option; §5's curl comparison is a **manual one-time QA probe**, and turning it into an automated gate is out of scope here.
- **No changes to `normalizePerson`** or to `people.ts`'s `normalize()` — both are already allowlists. A diff touching either is a **scope-creep finding, not a bonus fix**.

### Ambiguity flagged rather than resolved

AC2 names `personId` and `internalNote` only as examples ("e.g."). QA chose exactly those two for every section rather than inventing per-section fields (e.g. an `assignmentId` for skills), reasoning that `personId` is the realistic contract-adjacent leak the provenance section's `@JsonIgnore` discussion actually worries about, and `internalNote` stands in for anything not yet imagined. A section-specific fabricated field is a legitimate variation on the same intent — **not** a plan violation, and should not be read as a mismatch at review.

---

## Review round 1 — 2026-08-27

Reviewer set per the H1 ruling: `/code-review` (effort `high`) + `/security-review`. Both run against branch `fix/allowlist-section-normalizers` @ `b6fd1f6`, named as an explicit target — [T-029](T-029-code-review-cannot-see-worktrees.md) is on this board precisely because `/code-review` silently reviews the wrong thing without one, and the driver's shell was in the meta repo at the time.

**Outcome: no blocking findings. One LOW finding, filed as [T-207](T-207-public-types-derived-from-domain-interfaces.md) rather than absorbed.**

### `/security-review` — no HIGH or MEDIUM findings

The change is purely restrictive at the trust boundary: the set of data reaching the anonymous route can now only shrink. No new input, sink, or authorization decision. The driver traced the whole file rather than the changed hunk alone, to answer "does anything *else* still forward upstream data unfiltered": `normalizePerson` is already an allowlist; the body's `...normalizePerson(person)` spreads a **locally constructed** object, not an upstream one, so it is not a forwarding path; `UpstreamError` renders a constant `{ error: 'upstream error' }` with no upstream body or status echoed; `isValidPersonId` is unchanged and still runs before any URL is built.

Recorded, not raised: the guarantee is only as complete as `docs/api-contract.md` is accurate. The allowlist pins the public payload to that document, so a contract amendment is now the review point for any widening of anonymous disclosure. That is the intended design and the new comment says so.

### `/code-review` — one LOW, non-blocking

Confirmed by the reviewer: field lists match the contract for all four sections; `endDate` assigned directly, not `|| null`; the wire payload is identical to `master` for every declared field; null/non-array upstream payloads fail the same way as before; the twelve existing tests are byte-identical and the test diff is purely additive; AC4 is satisfied with no stale denylist-defending prose surviving anywhere in the repo.

**The finding — `src/routes/cv.ts:66`: the allowlist's compile-time contract is derived from the domain interfaces it exists to distrust, and fails in both directions.** `PublicExperience = Omit<DomainExperience, 'id'>` and its three siblings mean `tsc` checks T-205's rebuilds against the **domain** shape, not the contract. **The driver re-verified both directions independently before filing:**

- **Leak direction.** Adding a required `personId: number` to `DomainSkillAssignment` yields `src/routes/cv.ts(115,64): error TS2741: Property 'personId' is missing in type '{ name: string; category: string | undefined; proficiency: string; }' but required in type 'PublicSkill'.` — pointing at `stripSkill`. The path of least resistance under that pressure is `personId: s.personId`, reintroducing this task's disclosure on the anonymous route with a green build.
- **Drop direction.** Adding an optional `techStack?: string` to `DomainProject` typechecks **clean** with `stripProject` unchanged — a new contract field silently missing from the public payload, no compile error, no failing test.

So the comment this task added slightly overstates the guarantee ("a new CONTRACT field needs an edit in this file"). The runtime is now an allowlist; **the types are still a denylist.**

**PO ruling: non-blocking, filed as [T-207](T-207-public-types-derived-from-domain-interfaces.md).** T-205's scope note says *"Keep the public types as they are"*, and board rule 3 makes anything beyond the acceptance criteria a new task file — the same rule under which T-205 itself was filed out of T-201. The reviewer reached the same conclusion unprompted. The merged behavior is correct and byte-identical to `master` for every contract field; what T-207 fixes is the durability of the guard, not the payload.

---

## Exploratory QA — 2026-08-27 · **PASS**

Stage 4, run against the live isolated stack (`cvdl_t-205`, BFF `:3010`, domain-service `:8090`) by `quality-assurance` executing its own §5 plan. **This is the only stage in the whole pipeline where real cv-domain-service JPA-entity JSON meets these normalizers** — every other test, including the four new leak tests, runs against mocks.

**Build provenance was verified, not assumed.** `qa-env-override.py` warned that every service builds from the main checkout "(master)" — [T-028](T-028-qa-env-generator-worktree-build-context.md)'s exact false-pass shape. The driver checked directly: `cv-bff-node`'s checkout was on `fix/allowlist-section-normalizers` @ `b6fd1f6` with zero `...rest` spreads remaining, so the running container carried the change.

### Raw upstream key sets — a live record of what cv-domain-service actually sends

Worth keeping regardless of pass/fail: **nothing in cv-bff-node pins these**, which is the coupling this task exists to sever.

```
experiences: ["company","description","endDate","id","location","role","startDate"]
educations:  ["degree","endDate","fieldOfStudy","id","institution","startDate"]
skills:      ["category","name","proficiency","skillId"]
projects:    ["description","endDate","id","name","repoUrl","startDate"]
```

**No raw section carries `personId` or `email` today** — the `@JsonIgnore` the security review relied on is still in place. So there was **no live leak being masked**; the guard is prophylactic against a future regression, exactly as the provenance section claims. That claim is now measured rather than asserted.

### BFF aggregate key sets

```
experiences: ["company","description","endDate","location","role","startDate"]
education:   ["degree","endDate","fieldOfStudy","institution","startDate"]
skills:      ["category","name","proficiency"]
projects:    ["description","endDate","name","repoUrl","startDate"]
```

Each is an **exact subset** of its raw counterpart, restricted precisely to the contract-declared names. `id` absent from all four; `personId` absent; `skillId` present upstream and absent from the BFF's skills; no `email` anywhere (top-level person fields are only `name`, `headline`, `location`, `summary`).

### Error paths and behavior

| Probe | Result |
|---|---|
| Unknown id `9999` | `404 {"error":"upstream error"}` — pass |
| Non-numeric `abc` on `/cv` | `400 {"error":"invalid person id"}`, **zero upstream log entries during the call** — the guard's "never reaches an upstream URL" promise verified by observation, not by reading — pass |
| 34-digit id | `502` — **not a T-205 regression**; see T-206 below |

Content-type `application/json; charset=utf-8`. **Ordering passed through untouched** — experiences (startDate DESC), projects (startDate DESC, undated last, with the `id` tiebreak visible in the Ledger CLI / Schema Diff Reporter tie) and skills (category ASC, name ASC) are byte-identical in order to the raw upstream arrays, so no re-sort crept in. The BFF person route's fields match the aggregate's top-level fields exactly.

### Mirror-image defect, against real rows

Every contract-declared optional field the seed data populates is **present** in the BFF output: experience `location`+`description` (3/3 rows), education `fieldOfStudy` (2/2), skill `category` (5/5), project `description`+`repoUrl` (4/4), including the nullable-`startDate` case (`Dotfiles`, `startDate: null`) passed through correctly. No forgotten field.

> **Evidence gap, recorded rather than glossed.** The seed data never produces a skill with `category: null`, nor an experience/education with a null `location`/`fieldOfStudy`, so the null-optional case could **not** be exercised live for those fields. It is covered by the new sparse-payload unit test, not by this stage. A gap in the evidence, not a passed criterion.

### Two observations — both already on the board, neither a new task

QA raised both as "possibly worth a follow-up if not already tracked". They are:

- **`people.ts`'s `/people/:id` has no id guard at all.** Confirmed live: `abc` on that route makes a *genuine* upstream call (domain-service `MethodArgumentTypeMismatchException` in the logs) and returns `400 {"error":"upstream error"}`, versus `/cv`'s pre-validated `400 {"error":"invalid person id"}` with no upstream call. **This is exactly [T-204](T-204-bff-validate-person-id-param.md)'s scope** — that task explicitly owns "applying the guard to `GET /people/:id` in `src/routes/people.ts`, which T-201 deliberately did not touch". No new task.
- **The 34-digit id returning 502.** **This is exactly [T-206](T-206-person-id-guard-numeric-overflow.md)**, and QA has now reproduced it independently on a second occasion — see the corroboration recorded in that file. No new task.

**Verdict: PASS.** No defects against T-205's acceptance criteria. No QA bounce-back.
