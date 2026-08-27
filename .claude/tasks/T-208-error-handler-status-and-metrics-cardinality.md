---
id: T-208
title: "The terminal error handler turns every non-auth error into 500 — including Express's own 400s — and unmatched requests mint unbounded Prometheus labels"
repo: cv-bff-node
status: todo
owner:
branch: fix/error-handler-status-and-metric-cardinality
pr:
depends_on: []   # both defects are pre-existing on master and independent of any in-flight task
risk: normal
security_review: true   # both are reachable by anonymous traffic on routes T-013 ratified as public
---

## Two defects, one request class

Both were found by `/code-review` during [T-204](T-204-bff-validate-person-id-param.md)'s review round and **verified by the driver before filing**. They are separable fixes but share a trigger: an anonymous request that never reaches a route handler.

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

## Watch-outs

- **`err.status` is attacker-influenced only in shape, not value** — it comes from Express, not the request body. Still, clamp to the 4xx range rather than echoing any number an error object carries; a middleware setting `status: 302` must not turn the error handler into a redirector.
- Part 2 changes a metric's label values. Any Grafana panel or alert keyed on `route` for unmatched traffic will see the series change — check `cv-observability` before assuming nothing consumes it.

## dev-loop notes

- **Developer:** `fullstack-developer` (adapter §2 — `cv-bff-node`). Gates: the `cv-bff-node` row of adapter §3. CI: **GitHub Actions**.
- `risk: normal`, `security_review: true` — the terminal error handler and an internet-reachable metrics registry are both security surfaces, and part 1 governs every route in the app.
- The two parts are independent; splitting into two PRs is legitimate if the reviewer prefers it.

## Provenance

Both raised by `/code-review` (effort `high`) during T-204's review round 1, 2026-08-27, as one medium and one low. Verified by the driver — the 500 reproduced directly against `createApp()`, and the error handler's shape confirmed by reading `src/app.ts:39`. Filed rather than absorbed per board rule 3: T-204's acceptance criteria are its scope, its guard promise was kept, and this fix touches a handler shared by every route.
