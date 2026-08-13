# API contract — CV section resources (v1)

Status: **ratified v1** (2026-07-12). Amendments: **2026-08-13 — T-013** (BFF public edge path, anonymous reads, `/metrics` exposure). Changes require a PR to this file plus sign-off in the task that consumes it. All tasks in `.claude/tasks/` targeting the domain model implement *this* document — when in doubt, this file wins over any task prose.

## Design rules

1. Every section resource is **person-scoped**: nested under `/api/v1/people/{personId}`. A request for a section of a nonexistent person returns `404`.
2. Skills are the exception: the **catalog** is global (`/api/v1/skills`), the **assignment** (skill + proficiency) is person-scoped.
3. Dates are ISO-8601 (`YYYY-MM-DD`). `endDate: null` means "current".
4. Validation errors return `400` with Spring's default problem body; unknown IDs return `404`; success on `DELETE` is `204`.
5. The domain service exposes internal `id`s; the BFF **strips ids and emails** from public payloads (same rule as the existing `people/:id` normalization).

## Domain service (cv-domain-service)

### Experience — `/api/v1/people/{personId}/experiences`

| Verb | Path | Returns |
|---|---|---|
| GET | `/` | 200, array |
| POST | `/` | 201, created entity |
| PUT | `/{id}` | 200, updated entity |
| DELETE | `/{id}` | 204 |

```json
{ "id": 1, "company": "ACME", "role": "Backend Engineer", "location": "Remote",
  "startDate": "2022-01-01", "endDate": null, "description": "..." }
```
Required: `company`, `role`, `startDate`.

### Education — `/api/v1/people/{personId}/educations`

Same verb table as Experience.

```json
{ "id": 1, "institution": "UNED", "degree": "BSc", "fieldOfStudy": "Computer Science",
  "startDate": "2015-09-01", "endDate": "2019-06-30" }
```
Required: `institution`, `degree`, `startDate`.

### Projects — `/api/v1/people/{personId}/projects`

Same verb table as Experience.

```json
{ "id": 1, "name": "cv-project", "description": "...", "repoUrl": "https://github.com/...",
  "startDate": "2026-07-01", "endDate": null }
```
Required: `name`.

### Skills

Catalog (global):

| Verb | Path | Returns |
|---|---|---|
| GET | `/api/v1/skills` | 200, array of `{ id, name, category }` |
| POST | `/api/v1/skills` | 201 (name unique → duplicate returns 409) |

Assignments (person-scoped):

| Verb | Path | Returns |
|---|---|---|
| GET | `/api/v1/people/{personId}/skills` | 200, array of `{ skillId, name, category, proficiency }` |
| PUT | `/api/v1/people/{personId}/skills/{skillId}` | 200, body `{ "proficiency": "ADVANCED" }` — upsert |
| DELETE | `/api/v1/people/{personId}/skills/{skillId}` | 204 |

`proficiency` ∈ `BEGINNER | INTERMEDIATE | ADVANCED | EXPERT` (matches the `person_skill` enum in cv-database).

## BFF (cv-bff-node)

### Public edge path — `/bff/api/v1`

The BFF is served under its own edge prefix, **`/bff/*`**, as a new CloudFront `ordered_cache_behavior` alongside the existing `/api/*`. This is the whole of the routing decision, and it exists because the BFF and the domain service would otherwise both claim `GET /api/v1/people/:id`.

The two patterns are **disjoint** — they differ in the first path segment — so CloudFront's first-match-wins evaluation never has to choose between them and their declaration order is irrelevant. The collision is solved by the prefixes being different, not by ordering one ahead of the other. Do not add a precedence constraint that does not exist.

| Edge path | Origin | Consumers |
|---|---|---|
| `/bff/*` | cv-bff-node (:3000) | `cv-public-vanilla`, `cv-public-react` |
| `/api/*` | cv-domain-service (:8080) — **unchanged** | `cv-admin-react` |

**The prefix is not stripped at the edge.** CloudFront forwards the matched path whole, and the BFF mounts its routers at `/bff/api/v1`, so a given endpoint has *one* URL and it is the same string in local dev and in AWS:

```
GET /bff/api/v1/people/:id        → person, normalized
GET /bff/api/v1/people/:id/cv     → the aggregate below
```

Rejected: a CloudFront Function rewriting `/bff/api/v1/...` → `/api/v1/...` so the BFF could keep its internal paths. It buys tidier internals at the cost of an extra AWS resource, a second place routing can break, and dev/prod URLs that differ — the failure mode being a deploy that 404s for reasons invisible in local testing.

`/api/*` → domain service is **byte-identical to today**, so the already-deployed `cv-admin-react` needs no redeploy and no retest. That is the reason this option was chosen over moving the admin to its own prefix.

### Public (anonymous) routes

These BFF routes serve unauthenticated traffic **even when `AUTH_ENABLED=true`**, because the public sites have no user to authenticate:

| Route | Public | Why |
|---|---|---|
| `GET /bff/api/v1/people/:id` | **yes** | public site's person header |
| `GET /bff/api/v1/people/:id/cv` | **yes** | public site's whole payload |
| anything else under `/bff/api/v1` | no | stays behind `requireAuth()` |

(`/health` and `/metrics` are mounted outside `/bff/api/v1` and are unaffected by the guard either way — see below.)

**Match on exact method + path, not on path prefix.** Both public routes are `GET`s under `/people/:id`, so a prefix-style exemption would look correct today and silently exempt every future route added under that path — including non-`GET`s. The allowlist is two entries, not a subtree.

**This is deliberate — do not "fix" it by removing the exemption.** It is enumerated as an explicit allowlist rather than by setting `AUTH_ENABLED=false`, which would leave the entire surface open including any future non-public route. This mirrors the domain service's existing pattern, where `SecurityConfig` permits `/actuator/health`, `/actuator/prometheus` and swagger by explicit list while requiring auth for everything else.

Consequence, stated plainly: on these two routes the § Design-rules ban on `id`, `personId`, `skillId` and `email` in public payloads stops being a normalization nicety and becomes **the only thing between the domain database and the open internet**. A normalization leak here is a data-exposure bug, not a cosmetic one.

### `/metrics` and `/health` are not exposed at the edge

**No CloudFront behavior routes either path to the BFF.** `cv-observability` scrapes `/metrics` in-network and that is its only consumer; `/health` is for container and local checks. Both stay mounted at the BFF app root (outside `/bff/api/v1`), so neither is reachable through CloudFront and neither is affected by the auth allowlist above.

**What the edge actually returns is not a 404, and T-014 must not assume it is.** With no matching behavior these paths fall through to `default_cache_behavior`, which carries a `function_association` to the `spa_router` CloudFront Function (`cv-infra/functions/spa-router.js`). That function rewrites *any* URI whose last segment has no file extension to `/index.html`. `/metrics` and `/health` both qualify, so the edge serves **HTTP 200 with the public site's SPA shell**.

The security property holds — no BFF metrics or health data is exposed — but the observable behavior is misleading, and a monitoring probe pointed at the edge would read that 200 as "healthy". **T-014 must exclude both paths from the `spa_router` rewrite** so they return an honest 404 rather than a false 200. This is a required implementation step, not an optional cleanup.

### Aggregate endpoint

Aggregates the full CV in **one** call:

`GET /bff/api/v1/people/:id/cv` → 200:

```json
{
  "name": "Jane Doe", "headline": "...", "location": "...", "summary": "...",
  "experiences": [ { "company": "...", "role": "...", "location": "...", "startDate": "...", "endDate": null, "description": "..." } ],
  "education":   [ { "institution": "...", "degree": "...", "fieldOfStudy": "...", "startDate": "...", "endDate": "..." } ],
  "skills":      [ { "name": "...", "category": "...", "proficiency": "ADVANCED" } ],
  "projects":    [ { "name": "...", "description": "...", "repoUrl": "...", "startDate": "...", "endDate": null } ]
}
```

- Fetches person + four sections from the domain service **in parallel** (`Promise.all`).
- No `id`, `personId`, `skillId`, or `email` fields in the public payload.
- Person 404 upstream → 404. Any section fetch failing → 502 (the public site treats the CV as one unit).
- The existing person endpoint keeps its behavior and payload; only its **path** moves, from `/api/v1/people/:id` to `/bff/api/v1/people/:id`, per the edge-path decision above. Consumers must update their base URL — this is a breaking change for `cv-public-vanilla`, which calls the old path today.

## Non-goals (v1)

- Pagination (CV sections are small by nature).
- PATCH semantics — `PUT` replaces.

> **Removed 2026-08-13 (T-013):** *"Auth changes — the existing `AUTH_ENABLED` behavior in both services covers these routes as-is."* This was false for a deployed public BFF. `AUTH_ENABLED=true` applies `requireAuth()` to all of `/api/v1`, which would 401 every anonymous visitor to the public site; `AUTH_ENABLED=false` would leave the whole surface open. Neither is "covered as-is". The public-route allowlist in § BFF replaces it, and auth on the BFF is now explicitly **in scope** for v1.
