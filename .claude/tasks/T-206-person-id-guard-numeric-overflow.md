---
id: T-206
title: "The shared person-id guard accepts digit runs that overflow Java Long — 5 upstream calls and a 502 where a 400 belongs"
repo: cv-bff-node
status: done
owner: fullstack-developer
branch: fix/person-id-guard-length-bound
pr: https://github.com/erfeamor/cv-bff-node/pull/7
depends_on: [T-201]   # T-201 ships the guard this changes. Also read T-204, which ADOPTS the same guard — see "Who this affects".
risk: normal
security_review: true   # same reasoning as T-201's ruling 2: the route is anonymous by contract, and this is the guard standing in front of a five-way upstream fan-out
checkpoint:
  stage: done
  repo: cv-bff-node
  branch: fix/person-id-guard-length-bound
  pr: https://github.com/erfeamor/cv-bff-node/pull/7
  merged: 8d169ac   # squash-merged 2026-08-27, admin bypass (same ruleset as PR #6)
  commit: 5636125   # round-1 fixes on top of e1ab543 (first implementation)
  superseded_commit: e1ab543   # A1 green: lint 0, typecheck 0, test 62/62, build 0. Red re-verified by the driver: reverting ONLY the middleware to master fails 6 tests (2 route-level, 4 unit-level); 62/62 with it restored.
  developer: fullstack-developer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 1
  open_findings: 0   # all 3 findings from round 1 resolved on-branch
  qa_bounces: 0
  fix_attempts: 1
  env_slot: 0
  updated: 2026-08-27
  budget:
    turns: 232
    total_tokens: 29000000
    subagent_tokens: 71000
    spawns: 2
    status: ok
    checked: 2026-08-27
    session_note: "SECOND task this session — T-205 was driven to merge first and cost ~140 turns. The turn ceiling is session-wide while max_spawns_per_task is per-task, so this task starts at ~46% of ceiling_turns with a full spawn budget. Expect SOFT during this task."
---

## Goal

`src/middleware/validate-person-id.ts` tests `/^[0-9]+$/`. A 300-digit string **is** a run of digits, so it passes — then overflows Java's `Long` upstream. Found by exploratory QA during [T-201](T-201-bff-cv-aggregate.md), 2026-08-27, against the live stack.

Observed end to end, not reasoned about:

```
GET /bff/api/v1/people/999…9/cv   (20 or 300 nines)
  -> guard PASSES
  -> five real upstream calls made
  -> cv-domain-service 400s (Long parse failure)
  -> the BFF's get() maps any non-404 upstream failure to 502
  -> client receives 502
```

Two things are wrong with that, and they are separable:

1. **A client error is reported as a server error.** The caller sent a malformed id; 502 says the BFF's upstream is broken. The contract does not cover this case, so nothing is technically violated — but 502 is the wrong answer to give a public site, and it is the answer that gets paged on.
2. **The guard's whole purpose is not to make the call.** Its own doc comment says an invalid id *"must never reach an upstream URL"*, and here five of them do.

## The part that makes this worth a task

**The guard's comment promises something the code does not deliver**, and that is the specific defect class this board keeps cataloguing — most recently [T-026](T-026-first-build-after-cold-start-fails.md)'s attempt 1, a guard whose failure was indistinguishable from its success. Here the comment reads as an absolute guarantee (*"anything that is not a run of digits is not an id, and must never reach an upstream URL"*) and its own framing is what lets the overflow through: an oversized digit run **is** a run of digits, so the code is faithful to the letter of the comment while defeating its point.

**Fix both halves or neither.** A length bound with the comment left overstating is the same trap one size smaller.

## Who this affects — this is not confined to `/cv`

[T-204](T-204-bff-validate-person-id-param.md) `depends_on` T-201 specifically so it **adopts this shared guard** rather than writing a second implementation. So whatever this task decides propagates to `GET /people/:id` automatically. **Sequencing matters:** if T-204 lands before this, it inherits the weaker guard and nobody re-checks it. Prefer landing this first, or note the interaction in T-204's PR.

## Scope

- Add an upper bound to the guard. **Justify the number rather than picking one** — Java `Long.MAX_VALUE` is 19 digits, so 19 is the natural ceiling and anything above it cannot be a valid id in this system. Decide whether to reject `>19` digits outright or to range-check the parsed value; the second also catches a 19-digit number above `Long.MAX_VALUE`.
- **Rewrite the doc comment so it states what the guard actually guarantees.** No absolute claim the code does not keep.
- Return **400**, consistent with the guard's existing behaviour for other malformed input.

**Out of scope:** the `get()` helper's non-404 → 502 mapping, which is [T-201](T-201-bff-cv-aggregate.md) ruling 4 and correct for genuine upstream failures. This task stops malformed input from reaching it; it does not change what happens when it does.

## Acceptance criteria

- [ ] An over-long digit run returns **400** and makes **no upstream call** — asserted the way T-201's guard tests already are, by confirming `fetch` was never called.
- [ ] The test is **confirmed red before the fix**, per this board's standing practice. The reproduction is trivial: 20 nines.
- [ ] Valid ids at the boundary still work — a 19-digit id at or below `Long.MAX_VALUE` must not be rejected if the chosen approach is a range check, and the choice is recorded either way.
- [ ] **The doc comment no longer makes a guarantee the code does not keep.** This is a real criterion, not a tidy-up: the comment is why the gap survived review, `/security-review` and a falsifiability check.
- [ ] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass.

## Watch-outs

- **Do not "fix" this by widening the regex or parsing with `Number()`.** `Number('1e3')` is 1000 and `parseInt('12abc')` is 12 — both would loosen a guard whose value is that it is strict. The current regex is correct as far as it goes; it needs a bound, not a replacement.
- QA verified the guard's other properties hold (`1abc`, `1;DROP`, `..%2F..%2Fadmin`, `1%20` all 400 with **no upstream request**, confirmed against the domain service's own logs). Do not regress those while adding the bound.

## Definition of done

PR open against `master` from `fix/person-id-guard-length-bound`, GitHub Actions green, task updated.

## dev-loop notes

- **Developer:** `fullstack-developer` (adapter §2 — `cv-bff-node`). **Reviewers:** `/code-review` + `fullstack-developer` + `/security-review`.
- Gates (adapter §3): the `cv-bff-node` row — lint, typecheck, test, build. Authoritative CI: **GitHub Actions**.
- **Small diff, but do not take the trivial fast-path**: it is the guard in front of an anonymous five-way fan-out.

## Provenance

Found by exploratory QA at T-201's stage-4, 2026-08-27, against the live isolated stack — a black-box probe of the guard with an oversized input, which no unit test in T-201 had tried. Filed rather than fixed inside T-201 per board rule 3: T-201's acceptance criteria are its scope and none of them cover numeric overflow. QA classified it low-severity and explicitly **not** a T-201 defect, which is the right call — the contract makes no promise here and the 502 is technically compliant. It is filed because the comment overstates, not because the status code is illegal.

---

## Independent corroboration — T-205's exploratory QA, 2026-08-27

Reproduced a **second** time, by a separate QA run against a separate stack (`cvdl_t-205`, BFF `:3010`), while testing an unrelated change. The original observation above came from T-201's QA; this one was found by probing around T-205's test plan, not by looking for it.

A **34-digit** id (the original used 20 and 300 nines) reproduces the full chain, and this run pinned down the upstream side more precisely than the first:

- the guard **passes** the id, as `/^[0-9]+$/` must;
- cv-domain-service throws `MethodArgumentTypeMismatchException` converting the value to `Long`;
- **five identical `WARN` log lines at a single timestamp** — direct confirmation that all five parallel upstream calls were made, which the original entry inferred from the route's structure rather than measured;
- the BFF's "any non-404 upstream failure → 502" rule fires and the client receives **502**.

So both halves of this task's argument are now measured rather than reasoned: the client error surfaces as a server error, **and** the guard's documented promise that an invalid id *"must never reach an upstream URL"* is broken five times over per request.

Recorded here rather than filed as a new task — same defect, second sighting. It also strengthens the sequencing note in [T-205](T-205-bff-allowlist-section-normalizers.md) and `TASKS.md` that [T-204](T-204-bff-validate-person-id-param.md) should not land before this one: T-204 adopts the shared guard, and adopting it while it still accepts overflowing digit runs propagates the weaker version to a second route.

---

## Test plan (QA)

Authored by `quality-assurance` at stage 0, 2026-08-27 — the plan QA itself would execute at stage 4. **Driver-verified before filing:** QA's open question 3 was checked — `1abc` and `1%20` are **not** in the suite anywhere (the only guard tests are `1;DROP` at `cv.test.ts:310` and `..%2F..%2Fadmin` at `:321`). The task's watch-out lists them as "verified live", which they were — but never as automated tests. Adding them is real new coverage, not duplication.

### 1. Red-before-green

Test `'rejects a digit run longer than Long.MAX_VALUE with 400 and makes NO upstream call'`, input `'9'.repeat(20)`:

```ts
const fetchMock = jest.fn();
global.fetch = fetchMock as unknown as typeof global.fetch;
const res = await request(createApp()).get(`/bff/api/v1/people/${'9'.repeat(20)}/cv`);
expect(res.status).toBe(400);
expect(fetchMock).not.toHaveBeenCalled();
```

**Assert the call count explicitly in the red run** — `fetchMock.mock.calls.length === 5`. QA's reasoning is worth keeping: `not.toHaveBeenCalled()` is the *green* assertion, but pre-fix the mock **is** called five times, and the count is what makes the red state legible as *"the fan-out happened"* rather than merely *"wrong status code"*. That count is the whole defect in one number.

Add a **300-digit** variant too — the task's other repro size, and it defends against a fix that special-cases "a bit past 19" instead of bounding generally.

### 2. "Makes NO upstream call" — the criterion that matters most

Every new case asserts a fresh `jest.fn()` (**not** `mockHappyPath()`) was `not.toHaveBeenCalled()`, exactly as the two existing guard tests do. Status and call-count assertions must sit **in the same test body** — status alone does not prove the fan-out was skipped, since a route could fire the calls and then override the response.

### 3. Non-regression on the guard's existing properties

| input | expected | upstream |
|---|---|---|
| `1abc` | 400 | none — **new test** |
| `1;DROP` | 400 | none — existing, keep |
| `..%2F..%2Fadmin` | 400 | none — existing, keep |
| `1%20` | 400 | none — **new test** |
| `1`, `12345` | 200 via `mockHappyPath()` | 5 calls |

### 4. Boundary matrix — written to survive either H1 ruling

| input | digits | vs `Long.MAX_VALUE` (9223372036854775807) | Option A (length > 19) | Option B (range check) | agree |
|---|---|---|---|---|---|
| `9223372036854775807` | 19 | == max | 200 | 200 | yes |
| `9223372036854775808` | 19 | max + 1 | **200 — A cannot see this** | **400** | **NO** |
| `'9'.repeat(20)` | 20 | ≫ max | 400 | 400 | yes |
| `'9'.repeat(300)` | 300 | ≫ max | 400 | 400 | yes |
| `'0'.repeat(25) + '1'` | 26 chars, value 1 | in range | **400 — A counts digits, not value** | **200** | **NO** |
| `1`, `0` | 1 | in range | 200 | 200 | yes (whether id `0` exists is the domain service's business, not this guard's) |

The two disagreement rows get their **own named tests, each carrying a comment naming the option in force** — otherwise the test silently passes for the wrong reason if the implementation later switches.

**`BigInt`, not `Number`, if Option B is chosen — a correctness issue, not a style preference.** `Number` loses integer precision above 2^53 (`9007199254740992`), which is *below* `Long.MAX_VALUE` (~9.22×10^18). So a `Number`-based range check is already silently wrong for legitimate 16–17 digit ids **well before** reaching the boundary it exists to defend: `Number('9007199254740993') === Number('9007199254740992')` is `true`. Dedicated test — both are ≤ max and both must be accepted; the point is proving the implementation did not collapse them to one value and get lucky.

### 5. Where the tests live — both, and neither subsumes the other

- **New `test/validate-person-id.test.ts`** calling `isValidPersonId()` directly with the full matrix, no Express or fetch machinery. It is a pure function, the matrix is large, and route-level supertest for every row is a network-shaped test for a parse decision. **This is also the file [T-204](T-204-bff-validate-person-id-param.md) points at when it adopts the guard** — it should not have to re-derive the boundary matrix.
- **Route-level tests stay in `cv.test.ts`** (items 1–3 only). They prove the *wiring* — that the route checks the guard's return before calling `fetch`. A middleware unit test cannot see that; a route test for all ten matrix rows would be slow and redundant.
- **No `/people/:id` tests in this task** — that guard is not wired yet and T-204 owns it. Flagged rather than silently skipped: nothing is lost, because the new unit file is exactly what T-204 will reuse.

### 6. The doc-comment criterion — reviewer judgment, and a real bar

No test asserts that prose is honest. The bar at review:

- The new comment must describe the **magnitude** bound as well as the shape one, and **name the constant** (`Long.MAX_VALUE`) so a future reader need not re-derive 19 from first principles.
- **If Option A:** it must say the check is on digit *count*, not parsed *value*, and that `0000…1` padded past the bound is rejected despite being a small number — otherwise the comment reintroduces the exact "faithful to the letter, defeats the point" trap this task exists to close, moved to the leading-zero edge.
- **If Option B:** it must say it parses and range-checks, and record the `BigInt` reasoning, so a later editor does not "simplify" it to `Number` and restore the precision bug.
- **QA will raise a finding if the comment states a mechanism with no justification** — "checks length" without *why 19*. The original defect survived because the comment asserted an outcome instead of describing a mechanism; a bare mechanism with no reason is a smaller version of the same gap.

### 7. Stage 4 — **no live stack, and here is the argument**

All acceptance criteria are observable through `createApp()` + a mocked `fetch`: the 400-and-no-call pair by supertest, boundary correctness by pure unit tests, the comment by reading it, the gates by running them.

What a live stack would add is confirmation of the `MethodArgumentTypeMismatchException` → 400 → 502 chain — **but that chain is precisely what this task removes.** After the fix the guard rejects before any upstream call, so there is nothing left for a live upstream to demonstrate that the mock does not already prove; the only fact in question is *"was `fetch` called"*, which is the mock's entire job. **The original discovery needed a live stack because nobody had written the boundary case yet; verification does not, because the fix makes the upstream unreachable by the very input that was interesting.** A live run would be warranted only if the fix were on the domain-service side, which is explicitly out of scope.

**Recommend skipping the stage-4 bring-up, and saying so in the PR** — so the human gate sees the reasoning rather than an absent step.

---

## H1 rulings — 2026-08-27

**Ruling 1 — the bound is a VALUE RANGE CHECK using `BigInt`, not a digit-count bound.** Option B from the test plan's matrix.

```ts
const LONG_MAX = 9223372036854775807n;
// ... after the existing PERSON_ID_PATTERN test:
return BigInt(value) <= LONG_MAX;
```

Reasoning, recorded because the task required the choice be justified rather than picked: **validity here is about the value, not the string's shape.** `0000000000000000000000001` is id `1` however it is spelled, and rejecting it for a formatting accident is a false positive with no security or correctness benefit. Conversely, accepting `9223372036854775808` because it happens to have 19 digits is a false negative that **reinstates this task's own defect**, merely relocated from "any digit count" to "exactly 19 digits, above max". A length bound closes the reachable failure mode; a range check closes the class.

**`BigInt`, never `Number` — a correctness requirement, not a preference.** `Number` loses integer precision above 2^53 (`9007199254740992`), which is *below* `Long.MAX_VALUE` (~9.22×10^18). A `Number`-based range check is therefore already silently wrong for legitimate 16–17 digit ids **before** it ever reaches the boundary it exists to defend: `Number('9007199254740993') === Number('9007199254740992')` evaluates `true`.

~~**A length pre-check before parsing was considered and rejected.**~~ **WRONG — SUPERSEDED at review round 1, 2026-08-27. See the amendment below; the pre-check is REQUIRED and is now implemented.** The struck reasoning follows as written, because the argument is plausible enough to be made again:

> **A length pre-check before parsing was considered and rejected.** The concern was unbounded parse cost on a pathological digit run. It does not survive contact with the runtime: Node caps the HTTP request line at 16 KB by default, so the digit run is already bounded, and `BigInt` parses a 16 KB numeral in microseconds. The extra branch would buy nothing and would drag Option A's leading-zero rejection back in at a higher threshold. Recorded so nobody re-proposes it.

### Amendment to ruling 1 — 2026-08-27, from review round 1

**The paragraph above is wrong, and the error is the driver's, not the developer's** — the implementation matched the ruling exactly as written.

`BigInt('0'.repeat(9000) + '1')` is `1n`, comfortably `<= LONG_MAX`, so the value bound **accepts** it. The route then builds a **9049-byte** upstream URL and fans out five calls. cv-domain-service overrides nothing in `src/main/resources/`, so Spring Boot 3's **8192-byte** `max-http-request-header-size` default applies: Tomcat rejects the request line, `get()` maps it to 502, and the result is **502 after five upstream calls — T-206's own symptom, restored through the leading-zero door.** AC1 was therefore not met.

**Where the reasoning failed:** it argued from Node's 16 KB request-line cap, which is real but is **twice the downstream limit** — the wrong side of the hop. A bound that sits above the limit it is supposed to protect bounds nothing. It also assumed the two mechanisms were alternatives; they are not, and they fail in opposite directions:

- a **value** bound alone leaves the string unbounded (`0`-padding);
- a **length** bound alone misfires on both `9223372036854775808` (19 digits, over max) and `0000…1` (long, but id 1).

**Resolution: both checks, length first.** `MAX_ID_LENGTH = 64`, an *abuse* bound rather than a validity rule — far above the 19 digits any legitimate id needs, and far below the size at which the upstream request line stops being reasonable (at the cap the longest URL this route builds is **112 bytes, ~1.4% of the 8192-byte budget**). Option B's value semantics are untouched: `'0'.repeat(25) + '1'` is still accepted, and its test is still green.

Note the consequence, because it keeps the tests honest: **20 and 34 characters sit *under* the cap**, so the original T-206 reproductions are still decided by the value bound alone; only the 300- and 9000-digit rows are caught by the length cap. Neither bound is provable by the other's cases, and the tests say which is which.

**Ruling 2 — stage 4 runs with NO live docker stack**, adopting the test plan's §7 argument in full. Every acceptance criterion is observable through `createApp()` + a mocked `fetch` and pure unit tests. The live chain a stack would exercise (`MethodArgumentTypeMismatchException` → 400 → 502) is **exactly what this fix removes**: after the fix nothing reaches the upstream, so the only fact in question is whether `fetch` was called, which is the mock's entire job.

**The distinction that carries this ruling: discovery needed a live stack; verification does not.** This bug was found live twice (T-201's QA, then T-205's) precisely because no unit test had tried an oversized input. Once the boundary case is written down, the stack has nothing left to add. **This must be stated in the PR** so the H2 gate reads an argued decision, not a skipped step.

**Reviewers:** `/code-review` + `/security-review`, as skills. Same reasoning as T-205's H1 ruling — `max_spawns_per_task: 3`, and the spawns that earn their place are QA's plan, the developer, and a bounce-back if one is needed.

---

## Review round 1 — 2026-08-27

Reviewers per H1: `/code-review` (effort `high`) + `/security-review`, both against `fix/person-id-guard-length-bound` as an explicit target (T-029). **Three findings: one MEDIUM blocking, two low. All three applied on the same branch** (`e1ab543` → `5636125`) by the persistent developer instance — bounced via message rather than a fresh spawn, so the task stayed at 2 spawns.

### `/security-review` — no findings

The one genuinely new failure mode is `BigInt()`'s throw path, and it is closed **by construction**: `BigInt` is reached only after `/^[0-9]+$/` passes, which guarantees a non-empty ASCII digit run — the one shape it cannot throw on. Probed rather than reasoned: **2000 regex-passing samples, zero throws**, and every adversarial shape rejected (`1e3`, `0x10`, `1_000`, `+1`, `-1`, whitespace-padded, empty).

Two things that probe surfaced, worth keeping:

- **The strict ASCII regex earns more than the task credits it for.** `١٢٣` (Arabic-Indic digits) is rejected — but `Number('١٢٣')` is `123` in JavaScript. The "do not replace the regex with a parse" watch-out is protecting against a character-set hole as well as `1e3`.
- **The check order is load-bearing, not stylistic.** Reversed, an oversized non-numeric input throws `SyntaxError` into the central error handler and answers **500** on an anonymous route — worse than the 502 this task exists to fix.

### `/code-review` — finding 1, MEDIUM, **blocking**

Bounding the **value** left the digit **count** unbounded. Full detail and the resolution are in the *Amendment to ruling 1* above; in short, a zero-padded id passed the guard and reproduced T-206's own symptom. **The root cause was the H1 ruling, not the implementation.** Fixed by adding `MAX_ID_LENGTH = 64` before the parse, plus a route-level regression test (`'0'.repeat(9000) + '1'` → 400, `fetch` not called) confirmed red first: `Received number of calls: 5`.

### `/code-review` — finding 2, low, accepted

**`PERSON_ID_PATTERN` was still exported, and it is now only one third of the rule.** Before this task the pattern *was* the guard, so exporting it was harmless; after it, an importer calling `PERSON_ID_PATTERN.test(id)` gets the shape check with **neither** bound. The named consumer is [T-204](T-204-bff-validate-person-id-param.md), and this module's whole stated reason for being shared is that *"a private helper would guarantee two implementations of one rule"* — so exporting the weaker symbol left that footgun loaded, and T-204 reaching for it would reinstate T-206 on `GET /people/:id`. No consumers existed, so un-exporting was free then and impossible later. **`isValidPersonId` is now the module's only export.**

### `/code-review` — finding 3, low, accepted

The test titled *"parses the two neighbours as DIFFERENT values"* **never called the module** — both assertions were statements about JavaScript's own `BigInt`/`Number` constructors, and it would pass with `validate-person-id.ts` deleted. The 2^53 pair are both accepted under a `Number` implementation too, so they pin nothing on their own; **the test that actually fails under `Number` is `rejects Long.MAX_VALUE + 1`**, since `Number` coerces max and max+1 to the same value. The tests are kept but retitled and re-commented, and the doc comment's pointer now names the real pin.

This is the same shape as the finding that produced [T-207](T-207-public-types-derived-from-domain-interfaces.md) one task earlier, and as [T-109](T-109-ordering-tiebreak-unevidenced-siblings.md): **an assertion that cannot go red, sitting where a guarantee is assumed to be.**

### Driver verification of the final state

Independently re-derived, not taken from the report: 64 chars in-range **accept**, 65 **reject**, 9000-zero-pad **reject**, `Long.MAX_VALUE` **accept**, max+1 **reject**, 20/34 nines **reject** (value bound, under the cap), 300 nines **reject**. Longest URL at the cap: **112 bytes against the 8192-byte downstream limit.** A1 green: lint 0, typecheck 0, **66/66 tests**, build 0.
