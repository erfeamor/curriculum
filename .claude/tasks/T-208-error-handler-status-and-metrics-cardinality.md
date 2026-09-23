---
id: T-208
title: "The terminal error handler turns every non-auth error into 500 — including Express's own 400s — and unmatched requests mint unbounded Prometheus labels"
repo: cv-bff-node
status: done
owner: fullstack-developer
branch: fix/error-handler-status-and-metric-cardinality
pr: https://github.com/erfeamor/cv-bff-node/pull/11
depends_on: []   # both defects are pre-existing on master and independent of any in-flight task
risk: normal
security_review: true   # both are reachable by anonymous traffic on routes T-013 ratified as public
checkpoint:
  stage: done   # merged 889a82f (squash of cv-bff-node#11), 2026-09-24 — H2 accepted by the human
  repo: cv-bff-node
  branch: fix/error-handler-status-and-metric-cardinality
  worktree: none   # removed after merge
  developer: fullstack-developer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  commit: 889a82f   # squash merge on master (branch commit was e14bd1a)
  pr: https://github.com/erfeamor/cv-bff-node/pull/11
  qa: pass   # stage 4, cvdl_t-208, provenance e14bd1a
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: 1
  wave: [T-023, T-408, T-208]   # 2026-09-24 wave, human-requested
  updated: 2026-09-24T11:40:00+02:00
  budget:
    turns: 445
    total_tokens: 125733638
    subagent_tokens: 186000
    spawns: 2
    status: soft   # 83.8% of ceiling_total_tokens — ask before starting merge
    checked: 2026-09-24T11:40:00+02:00
---

## Two defects, one request class

Both were found by `/code-review` during [T-204](T-204-bff-validate-person-id-param.md)'s review round and **verified by the driver before filing**. They are separable fixes but share a trigger: an anonymous request that never reaches a route handler.

## Goes public with T-014 — land before it, or with it (added 2026-09-24, board review)

Both defects are reachable only on localhost today: `cv-bff-node` has never been deployed. [T-014](T-014-deploy-bff-to-aws.md) puts it behind CloudFront on the public `/bff/*` edge, and from that apply onward any anonymous visitor can mint 5xx responses, stack-trace log lines and new Prometheus label values at will. That is the same argument that made [T-204](T-204-bff-validate-person-id-param.md) *"not sit unfixed for long after T-014"*.

**Deliberately not a `depends_on` edge in either direction** — T-014 is the claimable head of the critical chain and must not wait on this, and this task needs nothing T-014 builds. It is a *priority*, recorded in the board's Now/Next lane: claim it before T-014's apply, or at the latest let T-014's first deployed image carry it. If T-014 ships first, T-014's H2 should name this task as a known open exposure rather than let it go unmentioned.

## Part 1 — a malformed percent-encoding answers 500, where Express itself said 400

Express decodes `req.params` in `Layer.match`, **before the handler runs**, and throws a `URIError` carrying `status = 400`. The terminal handler at `src/app.ts:39` maps only `UnauthorizedError` and sends everything else to 500:

```ts
app.use((err: Error, _req, res, _next) => {
  if (err.name === 'UnauthorizedError') {
    return res.status(401).json({ error: 'invalid or missing token' });
  }
  console.error(err);
  res.status(500).json({ error: 'internal server error' });
});
```

Measured on `fix/validate-person-id-param`, with T-204's guard in place:

```
%E0%A4%A     500 {"error":"internal server error"}     fetch calls: 0
abc          400 {"error":"invalid person id"}
1%2Fadmin    400 {"error":"invalid person id"}
```

So an **anonymous** caller (T-013 ratified `GET /people/:id` and `/cv` as public) can mint 5xx responses and `console.error` stack lines at will. The 5xx is the part that gets paged on; the log line is the part that costs money on a `t3.micro`.

**This is the same argument [T-206](T-206-person-id-guard-numeric-overflow.md) made and won:** a client error reported as a server error. T-206 fixed it for one input class by guarding earlier. This is the class that **no guard can reach**, because Express throws before the handler exists.

**Why T-204 did not absorb it.** T-204's guard promise held — `fetch` was called **zero** times, so malformed input still never reached an upstream. Only the status code was wrong, on a path the guard never runs on. And the fix governs **every route in the app**, which is a wider blast radius than a one-route task: it needs its own tests proving the `UnauthorizedError` → 401 mapping and the genuine-500 path are both intact.

### Scope, part 1

- Honour a sub-500 `err.status`/`err.statusCode` set by Express or its middleware, instead of flattening it to 500.
- **Do not leak the error message** into the response body — the current constant-body habit is right and must survive; only the *status* changes.
- **Do not `console.error` a client error.** A 4xx is not an application fault, and logging it is the half of this defect that scales with attacker volume rather than with real bugs.
- Keep the `UnauthorizedError` → 401 branch exactly as it is.

## Part 2 — unmatched requests mint unbounded Prometheus label values

`src/metrics.ts:17` labels the histogram with `req.route?.path || req.path`. The fallback fires whenever **no route matched** — every 404, and the part-1 case above — so an attacker-supplied pathname becomes a `route` label value on `http_request_duration_seconds`.

Cardinality is therefore unbounded and anonymously driven: the registry grows without limit, and `/metrics` scrapes degrade with it. Prometheus label cardinality is the classic memory-exhaustion shape for a metrics registry, and this one is exposed to the internet.

### Scope, part 2

- Bucket unmatched requests to a **constant** (e.g. `'unmatched'`) rather than echoing `req.path`.
- Matched routes keep using `req.route.path`, which is bounded by the route table and is the useful signal.

## Acceptance criteria

- [ ] A malformed percent-encoding (`GET /bff/api/v1/people/%E0%A4%A`) returns **400**, makes **no upstream call**, and writes **no error-level log line**.
- [ ] `UnauthorizedError` still returns 401; a genuine unexpected error still returns 500 **and** still logs. Both proven by test, not by inspection.
- [ ] The response body for a client error carries **no** exception message or stack.
- [ ] An unmatched path produces a **constant** `route` label; asserted by scraping the registry after requesting two different bogus paths and confirming one series, not two.
- [ ] A matched route still reports its route template, unchanged.
- [ ] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass; GitHub Actions green.

## Test plan (QA)

Authored by `quality-assurance` at refinement, 2026-09-24 — the plan it executes at stage 4. Driver-verified the same day: the handler block spans `src/app.ts:39-45` on `origin/master`; `test/app.test.ts` and `test/health.test.ts` exist and neither covers the status mapping or the label value; `scripts/qa-env-override.py` repoints the build context at the worktree and stamps task/branch/commit build labels.

### 0. Re-verified watch-out: does anything key on `route`?

`grep -rn "\"route\"\|'route'\|route=" cv-observability/` and `grep -rln "route" cv-observability/` → no matches. Re-run at stage 4 against `cv-observability`'s current `master` (it can drift independently) before treating the watch-out as closed.

### 1. Unit-level (Jest, `createApp()` + supertest, no live stack)

New/modified: `test/app.test.ts` (error-handler section) and a new `test/metrics.test.ts` (or extend `test/health.test.ts`'s `/metrics` block).

| # | Case | Assertion | AC |
|---|---|---|---|
| 1a | `GET /bff/api/v1/people/%E0%A4%A` | 400; `fetch` mock **not called**; no `stack`/message in body; `console.error` **not** called (`jest.spyOn`) | AC1, AC3 |
| 1b | `UnauthorizedError` from a stub middleware | 401, body unchanged (`{error:'invalid or missing token'}`) | AC2 |
| 1c | A genuine unexpected error (handler throws a plain `Error`, or upstream `fetch` rejects) | 500, `{error:'internal server error'}`, **and** `console.error` called once | AC2 — proven, not inferred from 1a |
| 1d | Body-leak check, both directions | for 1a and 1c, body is exactly the constant shape — no `err.message`, no `.stack`, no extra keys | AC3 |
| 1e | Clamp — `next(Object.assign(new Error('x'), { status: 302 }))` (and an out-of-range `statusCode: 600`) | never echoed: status is a sane 4xx or 500, never 302, no `location` header | Watch-out 1 |
| 1f | Two different unmatched paths (`/bff/api/v1/does-not-exist`, `/bff/api/v1/also-missing`) | after both, `register.metrics()` shows exactly **one** distinct `route` value for unmatched traffic, equal to the constant — not either literal path | AC4 |
| 1g | Matched route (`GET /bff/api/v1/people/1`, mocked fetch) | sample carries `route` = the Express template, unchanged | AC5 |

**Red-before-green without touching the reviewed tree:** clone `cv-bff-node` at `origin/master` into the scratchpad, copy the new test file(s) from the branch in (`git show <branch>:test/…`), `npm ci && npx jest <file>`. Expected red: 1a (500 **and** `console.error` called — a fix that changes the status but still logs is half-red), 1e (302 echoed), 1f (**two** distinct `route` values). Then the same suite green on the worktree.

### 2. Live stack (isolated slot 1 — BFF `:3020`)

`python3 scripts/qa-env-override.py --task t-208 --slot 1 --smoke bff:/bff/api/v1/people/1`, then the printed `up` command.

- **Provenance first (T-028):** `docker inspect` the `bff` image for the generator's build labels; branch = `fix/error-handler-status-and-metric-cardinality`, SHA = `git -C /home/erfeamor/work/cvdl-worktrees/t-208 rev-parse HEAD`. Nothing below counts until this passes.
- **Malformed path:** `curl -g -s -o body.json -w '%{http_code}\n' "http://localhost:3020/bff/api/v1/people/%E0%A4%A"` → `400`, constant body.
- **No upstream call:** `logs domain-service --since <t0>` shows no line for it — cross-checked against a known-good `/people/1` in the same window, so a silent log cannot pass by accident.
- **No error-level log:** `logs bff --since <t0>` shows no stack for the 400 — contrasted with a genuine-500 probe so a quiet channel is not mistaken for a fixed one.
- **Cardinality:** hit `/bff/api/v1/people/%E0%A4%A` and `/bff/api/v1/totally/bogus`, then `curl -s :3020/metrics | grep 'http_request_duration_seconds_count{'` → exactly **one distinct `route=` value** for unmatched traffic (a histogram emits `_bucket`/`_sum`/`_count` lines per series, so "one series" ≠ "one grep line"); `/people/1` still reports `route="/bff/api/v1/people/:id"`.
- Teardown with the printed `down`; slot 0 (T-408) untouched.

### 3. Gates

In the worktree: `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`, all exit 0. GitHub Actions green on the PR — read the statuses API, not `gh pr checks`.

### 4. Findings on the spec

- Part 1 cites `src/app.ts:39` — the block starts there; the `res.status(500)` call is `:44`. Line drift only; the quoted shape matches.
- AC4's *"one series, not two"* is exact for direct registry inspection; on a live scrape read it as one distinct `route` value, per §2.

## QA record — stage 4, 2026-09-24 (PASS)

Executed by the `quality-assurance` instance that authored the plan, against `cvdl_t-208` (slot 1, BFF `:3020`), with the three driver corrections applied (router-relative label; 1b/1c/1e are regression guards; the implementation's constants). Driver spot-checked teardown and PR head afterwards.

| Item | Result | Evidence |
|---|---|---|
| Provenance (T-028) | PASS | generator repointed `bff` → the worktree @ `e14bd1a`; container labels `commit=e14bd1a, dirty=false` = PR #11 head |
| Gates | PASS | lint, typecheck, 90/90, build |
| 1a · 1d · 1f (behaviour changes) | PASS | **red on a disposable master clone** — 1a `500`, 1d `500` for 404/413, 1f two literal paths — green on the branch |
| 1b · 1c · 1e (regression guards) | PASS | green on master **and** branch, as expected |
| 1g matched template | PASS | `route="/people/:id"` unchanged |
| Live malformed path | PASS | `GET /bff/api/v1/people/%E0%A4%A` → `400 {"error":"bad request"}` |
| No upstream call | PASS | domain-service `http_server_requests_seconds_count{uri="/api/v1/people/{id}"}` counted only the genuine requests; no series for the malformed one |
| No error log for the 400 | PASS | BFF log silent for it — **contrasted** with a forced genuine 500 (domain-service stopped) that logged a full `TypeError: fetch failed` stack in the same stream |
| Live cardinality | PASS | three distinct bogus/malformed paths → one `route="unmatched"` (split only by `status_code` 400/404) |
| Teardown | PASS | no `cvdl_t-208` containers, override removed; slot 0 untouched |

No defect bounced. `qa_bounces: 0`.

## Watch-outs

- **`err.status` is attacker-influenced only in shape, not value** — it comes from Express, not the request body. Still, clamp to the 4xx range rather than echoing any number an error object carries; a middleware setting `status: 302` must not turn the error handler into a redirector.
- Part 2 changes a metric's label values. Any Grafana panel or alert keyed on `route` for unmatched traffic will see the series change — check `cv-observability` before assuming nothing consumes it.

## dev-loop notes

- **Developer:** `fullstack-developer` (adapter §2 — `cv-bff-node`). Gates: the `cv-bff-node` row of adapter §3. CI: **GitHub Actions**.
- `risk: normal`, `security_review: true` — the terminal error handler and an internet-reachable metrics registry are both security surfaces, and part 1 governs every route in the app.
- The two parts are independent; splitting into two PRs is legitimate if the reviewer prefers it.

## Provenance

Both raised by `/code-review` (effort `high`) during T-204's review round 1, 2026-08-27, as one medium and one low. Verified by the driver — the 500 reproduced directly against `createApp()`, and the error handler's shape confirmed by reading `src/app.ts:39`. Filed rather than absorbed per board rule 3: T-204's acceptance criteria are its scope, its guard promise was kept, and this fix touches a handler shared by every route.
