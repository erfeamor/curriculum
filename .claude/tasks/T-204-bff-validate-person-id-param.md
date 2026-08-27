---
id: T-204
title: "BFF: validate the person id before interpolating it into the upstream URL"
repo: cv-bff-node
status: done
owner: fullstack-developer
branch: fix/validate-person-id-param
pr: https://github.com/erfeamor/cv-bff-node/pull/8
depends_on: [T-202, T-201]   # T-201 ADDED 2026-08-27 by its review round 1. NOT a scheduling nicety: T-201 ruling 3 puts the shared guard in src/middleware/validate-person-id.ts precisely so this task adopts it in one line. Branching off master before T-201 merges means that file does not exist, and this task writes the SECOND implementation of one rule -- the exact outcome ruling 3 exists to prevent.
risk: normal
security_review: true
checkpoint:
  stage: done
  repo: cv-bff-node
  branch: fix/validate-person-id-param
  pr: https://github.com/erfeamor/cv-bff-node/pull/8
  merged: d74d200   # squash-merged 2026-08-27, admin bypass (same ruleset as PR #6/#7)
  commit: 65b4253   # 6ea0693 guard + 65b4253 encode. A1 green: lint 0, typecheck 0, test 72/72, build 0.
  developer: fullstack-developer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 1
  open_findings: 0   # finding 3 applied at 65b4253; findings 1+2 filed as T-208
  qa_bounces: 0
  fix_attempts: 0
  updated: 2026-08-27
  budget:
    turns: 278
    total_tokens: 42400000
    subagent_tokens: 0
    spawns: 0
    status: ok
    checked: 2026-08-27
    session_note: "THIRD task this session (after T-205 and T-206, both merged). ceiling_turns is session-wide; this task starts at ~69% and is expected to trip SOFT (>=80%, i.e. 320 turns) partway through. Park at the nearest checkpoint if so."
---

## Use T-201's shared guard — do not write a second one (added 2026-08-27)

[T-201](T-201-bff-cv-aggregate.md) ships `src/middleware/validate-person-id.ts`, an exported `isValidPersonId()` over `/^[0-9]+$/`, and applies it to the aggregate route **before any upstream call**. Its ruling 3 justifies the shared module entirely on this task adopting it:

> *"A private helper would guarantee two implementations of one rule, which is exactly how this defect came to have two instances in the first place."*

**That justification only holds if this task lands after T-201**, which is why `T-201` is now in `depends_on` above. It was missing when T-201 merged its refinement, and a review round caught it: nothing sequenced the two, `TASKS.md` marked this task claimable in parallel, and an implementer branching off `master` would find no such file.

**What this task still owns, unchanged:** applying the guard to `GET /people/:id` in `src/routes/people.ts`, which T-201 deliberately did **not** touch (board rule 3 — T-201's acceptance criteria are its scope). The regex, its rationale, and the JS-specific note that `$` without `/m` matches only end-of-input — so the trailing-newline bypass that works in Python and Ruby does not apply here — are all settled in that module. Adopt, do not re-derive.


## Why this exists

Found by the forced security review on **T-202** (2026-08-13). The bug is **pre-existing on `master`** and T-202 did not introduce it — but T-202 changes who can reach it, which is why it is filed now rather than left in a review comment.

`src/routes/people.ts:36` interpolates the route param straight into the upstream URL:

```ts
const response = await fetch(`${DOMAIN_SERVICE_URL}/api/v1/people/${req.params.id}`);
```

`req.params.id` is unvalidated and **percent-decoded by Express before it lands there**. A caller can therefore put path syntax into the upstream request — `id = ".."` traverses, `id = "1%2Fsomething"` decodes to a literal `/` inside the segment — and steer the BFF's call to a different upstream path than the one intended.

### What actually changed, and why that is the whole point

| | before T-202 | after T-202 |
|---|---|---|
| Path | `/api/v1/people/:id` | `/bff/api/v1/people/:id` |
| Reachable with `AUTH_ENABLED=true` | only with a valid Cognito JWT | **anonymously — it is on the public allowlist** |

The defect is identical; the population that can reach it is not. This route is now one of exactly two the contract makes public, so it goes on the internet with no token in front of it the moment T-014 deploys the BFF.

**Why it was not a T-202 blocker.** `normalize()` (`src/routes/people.ts:25-32`) is a strict four-key allowlist — `name`, `headline`, `location`, `summary` — so arbitrary upstream JSON is not echoed back to the caller, which bounds the practical blast radius to what an attacker can infer from status codes and those four fields. Fixing it inside T-202 would also have violated board rule 3 (acceptance criteria are the scope). It is a real finding, correctly deferred, not waved away.

## Scope

`cv-bff-node` only. `src/routes/people.ts`, and the same treatment for any sibling route that interpolates a param into an upstream URL.

- Validate `id` before use. It is a domain-service `BIGINT` primary key, so the accepting shape is a positive integer — reject anything else with **400** rather than passing it upstream.
- Do not rely on `encodeURIComponent` alone. It stops the traversal but still forwards nonsense to the domain service and turns a client error into a confusing upstream 404; validate first, then encode.
- Decide and record whether the same guard belongs in a shared helper — T-201's aggregate route will interpolate the identical param, and this should not have to be found twice.

## Acceptance criteria

- [ ] A non-numeric `id` returns **400** from the BFF and makes **no upstream call** (assert `fetch` was not called — a test that only checks the status would pass against a fixed-but-still-calling implementation).
- [ ] Traversal and encoded-separator inputs are covered explicitly by tests: at minimum `..`, `1%2Fadmin`, and a negative number.
- [ ] A valid numeric id behaves exactly as today — existing `people.test.ts` assertions unchanged.
- [ ] The public/gated auth matrix from T-202 (`test/auth-matrix.test.ts`) still passes untouched.
- [ ] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass; GitHub Actions green.

## Definition of done

PR open against `master` from `fix/validate-person-id-param`, CI green, merged.

## dev-loop notes

- **Developer:** `fullstack-developer` (adapter §2). **Reviewers:** `/code-review` + `infrastructure-engineer` for the security lens.
- **`security_review: true`** — it is an input-validation fix on an internet-facing, pre-auth route.
- **Sequencing:** `depends_on: [T-202]`, which moves the route and puts it on the public allowlist. It does **not** block T-014 — the deployment can proceed without it — but it *should* land before the BFF is genuinely public-facing for long. If T-014 is imminent, do this first; the fix is small and the window is the entire time the route is anonymous and unvalidated.

---

## H1 rulings — 2026-08-27

**Ruling 1 — the "any sibling route" question is CLOSED, not open.** The scope says *"the same treatment for any sibling route that interpolates a param into an upstream URL"*, which reads as a hunt. It is not: a grep of every `req.params` use in `cv-bff-node/src/routes/` returns exactly **two** sites — `cv.ts:154` (guarded since T-201) and `people.ts:36` (unguarded). **This task's surface is one route.**

**Ruling 2 — no QA test-plan spawn; refinement done inline.** On T-205 and T-206 the stage-0 QA spawn earned its cost by settling genuine open questions (`toEqual` vs `toStrictEqual` against a parsed body; the Option A/B boundary matrix). **This task has no such question** — its acceptance criteria already name every case a plan would produce: 400 with `fetch` asserted uncalled, `..`, `1%2Fadmin`, a negative number, plus the existing `people.test.ts` and `auth-matrix.test.ts` kept green. Spawning to restate that would be paying a cold start to re-derive a spec that is already written. Recorded because it is a **deliberate departure from stage 0**, approved at the gate, not an omission.

**Ruling 3 — the sequencing payoff, recorded because it is the whole argument for the shared module.** T-201 ruling 3 put the guard in `src/middleware/validate-person-id.ts` *specifically* so this task would adopt rather than reimplement. [T-206](T-206-person-id-guard-numeric-overflow.md) then landed **first** (2026-08-27, `8d169ac`) and bounded that guard by **length and value**. So `/people/:id` inherits protection against the `Long` overflow and the zero-padding fan-out **without this task knowing they exist**. Had T-204 gone first it would have adopted the weaker guard and nobody would have re-checked it — exactly the risk `TASKS.md` and T-206 both warned about. Adopt `isValidPersonId`; do **not** import `PERSON_ID_PATTERN`, which T-206 made module-private for this precise reason.

**Ruling 4 — the behavioral change is intended, and one existing test must survive it.** `people.ts` currently passes the upstream status through (`res.status(response.status)`), so today a malformed id yields `400 {"error":"upstream error"}` **after a real upstream call** — measured live by QA during T-205. After this it is `400 {"error":"invalid person id"}` with **no call**: same status, different body, different cost. The existing `propagates upstream errors` test covers *genuine* upstream failures and must keep passing unchanged; it is not what this ruling changes.

**Reviewers:** `/code-review` + `/security-review`, as skills — same reasoning as T-205 and T-206.

---

## AC2 amendment — the bare `..` case, 2026-08-27

**AC2 requires "at minimum `..`" as a route-level test. That spelling is not testable, and the developer caught it before writing it rather than after.**

Verified independently by the driver against a bare Express app:

```
/p/%2E%2E          -> 404 {"nomatch":"/"}
/p/..              -> 404 {"nomatch":"/"}
/p/..%2F..%2Fadmin -> 200 {"id":"../../admin"}
```

When `..` is the **final** path segment, the client resolves it before the request is sent, so the server receives `/`. The route never matches, `req.params.id` never exists, and the guard is never consulted. **A test spelled that way would have gone green against unguarded `master` and asserted nothing** — this board's recurring *"green check that measures nothing"* shape ([T-107](T-107-post-id-cross-person-write.md), [T-109](T-109-ordering-tiebreak-unevidenced-siblings.md), [T-028](T-028-qa-env-generator-worktree-build-context.md), [T-205](T-205-bff-allowlist-section-normalizers.md)'s premise, [T-207](T-207-public-types-derived-from-domain-interfaces.md), and [T-206](T-206-person-id-guard-numeric-overflow.md)'s third finding), this time caught **before** it was committed instead of by a later reviewer.

**Ruling: substitution accepted.** The route-level test uses `..%2F..%2Fadmin`, which keeps the segment intact through routing and hands the handler `../../admin` — the value that actually reached the upstream URL on `master`. That is also the exact spelling `cv.test.ts` uses, so the two routes' guard tests stay symmetrical.

**AC2 is satisfied in substance, not waived:** `isValidPersonId('..')` is false on the shape check, and `test/validate-person-id.test.ts` covers the bare string directly at unit level, where no routing layer can dissolve it. The route test proves the wiring; the unit test proves the rule. Neither could cover this case alone.

---

## Review round 1 — 2026-08-27

`/code-review` (effort `high`) + `/security-review`, explicit target (T-029). **Three findings. One accepted into this PR, two filed as follow-ups.**

**`/security-review` — no findings.** Strictly hardening: it closes a real path-manipulation vector (`1%2Fadmin` is percent-decoded by Express into `1/admin` and steered the upstream request at a *different path* — the red run reproduced that literally). The guard sits **before** the `try`, matching `cv.ts`; that placement is safe only because `isValidPersonId` is **total**, which [T-206](T-206-person-id-guard-numeric-overflow.md) established — `BigInt` runs only on regex-validated input, so it cannot throw.

`/code-review` also confirmed **no consumer breaks**: `cv-public-vanilla`'s `VITE_PERSON_ID` defaults to `'1'`, and `cv-public-react` passes its segment to the already-guarded `/cv`. The new 400 is not a breaking change.

### Finding 3 — low — ACCEPTED INTO THIS PR (it is literally in scope)

The task's own Scope says *"Do not rely on `encodeURIComponent` alone… validate first, then encode."* **The PR validates but interpolates `id` raw.** It is safe *today* only because the pattern is `/^[0-9]+$/`, which makes encoding a no-op — so the URL's safety is entirely load-bearing on a regex in a **different module**. That is precisely the coupling this task's own scope told it to break. Encoding costs nothing and makes the interpolation safe independent of that coupling.

Applied to **both** `people.ts` and `cv.ts:162`: the Scope sentence covers *"any sibling route that interpolates a param into an upstream URL"*, and leaving the two routes asymmetric on this point would be worse than the one-line diff.

### Findings 1 and 2 — filed as [T-208](T-208-error-handler-status-and-metrics-cardinality.md), NOT absorbed

**Finding 1, medium — a malformed percent-encoding yields 500, not 400.** Express decodes `req.params.id` in `Layer.match` **before** the handler runs, throwing a `URIError` carrying `status = 400`. The terminal handler at `src/app.ts:39` maps only `UnauthorizedError` and sends everything else to 500. Driver-verified:

```
%E0%A4%A     500 {"error":"internal server error"}     fetch calls: 0
abc          400 {"error":"invalid person id"}
1%2Fadmin    400 {"error":"invalid person id"}
```

An anonymous caller can therefore mint 5xx responses and `console.error` stack lines at will on a route T-013 ratified as public.

**Why this is not blocking, unlike T-206's medium.** The guard's core promise holds: **`fetch` was called zero times**, so malformed input still never reaches an upstream. What is wrong is only the status code, on a path the guard **never runs on** — Express throws before the handler exists. This task cannot fix it: the fix is in the terminal error handler, which governs **every route in the app** and needs its own tests (the 401 mapping and the genuine-500 path must both be proven intact). That is a wider blast radius than a one-route task, so board rule 3 applies.

**Finding 2, low — unbounded Prometheus label.** `src/metrics.ts:17` falls back to `req.path` when no route matched, so attacker-supplied pathnames become `route` label values on `http_request_duration_seconds` — unbounded registry growth from anonymous traffic, reachable by the same request class. Also outside this diff.
