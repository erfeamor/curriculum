# API contract — CV section resources (v1)

Status: **ratified v1** (2026-07-12). Amendments: **2026-08-13 — T-013** (BFF public edge path, anonymous reads, `/metrics` exposure) · **2026-08-13 — T-006** (collection ordering) · **2026-08-20 — T-024** (skill-assignment PUT: request body split from response body) · **2026-08-28 — T-209** (optional fields: `null`, key always present). Changes require a PR to this file plus sign-off in the task that consumes it. All tasks in `.claude/tasks/` targeting the domain model implement *this* document — when in doubt, this file wins over any task prose.

## Design rules

1. Every section resource is **person-scoped**: nested under `/api/v1/people/{personId}`. A request for a section of a nonexistent person returns `404`.
2. Skills are the exception: the **catalog** is global (`/api/v1/skills`), the **assignment** (skill + proficiency) is person-scoped.
3. Dates are ISO-8601 (`YYYY-MM-DD`). `endDate: null` means "current".
4. Validation errors return `400` with Spring's default problem body; unknown IDs return `404`; success on `DELETE` is `204`.
5. The domain service exposes internal `id`s; the BFF **strips ids and emails** from public payloads (same rule as the existing `people/:id` normalization).
6. Every collection response is **explicitly ordered** — see § Ordering. An endpoint returning rows in the database's natural order does not satisfy this contract.
7. **Optional fields are always present; `null` is the empty value.** Every field this contract declares in a **response** body — section resources, the person head, and the BFF's payloads alike — is a key in that response whether or not it has a value. An optional field with no value serializes as `"fieldOfStudy": null`, never as a missing key. A consumer may assume the key exists and must handle `null`; it must not treat a missing key as the empty case.

   *The producer's tests cite this rule by the phrase* **"absent optionals serialize as null"** *— they mean this paragraph.*

   **Requests are the other way round, and rule 7 does not govern them.** `PUT` replaces (§ Non-goals rules out `PATCH`), so an optional omitted from a **request** body *is* the empty case and clears the stored value. This rule constrains what the API emits, never what a client must send: a client does not have to send explicit `null`s.

   **`endDate` is the one field this rule does not govern.** It is absent from every section's `Required:` list — those lists govern request validation — but it is **always emitted**, and its `null` carries the specific meaning **"current"** (rule 3), not "no value". The wire shape is identical to an empty optional; the semantics are not. `endDate` is the only field whose `null` says anything beyond absence, and rule 3 continues to own it.

   **End-to-end by inheritance, not by enforcement.** The BFF's public routes (§ BFF) rebuild each payload field by field and copy these values **verbatim**, so a consumer of `/bff/api/v1/people/:id` or `/bff/api/v1/people/:id/cv` sees whatever shape the domain service produced. The BFF adds no nulls and removes none — it does **not** coerce an absent upstream key into a `null`, and rule 5's id/email stripping removes those keys outright rather than nulling them. **The guarantee therefore rests on the producer honouring it, not on a BFF check**: a consumer relying on key-presence is relying on this rule, and a producer that ever stopped emitting a key would propagate that straight through to the public payload.

   *Added 2026-08-28 (T-209). This is an **amendment to a silence**, not a correction — the document had never stated the rule either way. The producer has behaved this way since v1 and its tests assert it, but three consumers each had to guess and guessed differently. No consumer was in violation; there was nothing to violate.*

## Ordering

Added 2026-08-13 (T-006). Collection endpoints returned rows in whatever order MySQL happened to produce, which is wrong to a CV reader and, because `cv-public-react` renders via ISR, gets *frozen* into a cached page that a later revalidation can silently reshuffle.

**Ordering is the domain service's responsibility.** It sorts; the BFF passes arrays through unchanged; no frontend re-sorts. One source of truth, so the admin UI, the aggregate, and both public sites always agree. A frontend that re-sorts is creating a second answer and is a review blocker.

| Collection | Order | Then |
|---|---|---|
| `experiences` | `startDate` **DESC** | `id` ASC |
| `education` | `startDate` **DESC** | `id` ASC |
| `projects` | `startDate` **DESC**, undated **last** | `id` ASC |
| `skills` (person) | `category` ASC, uncategorized **last**, then `name` ASC | `skillId` ASC |
| `skills` (catalog) | `name` ASC | `id` ASC |

**The secondary key is mandatory, not decorative.** Two experiences starting the same month otherwise come back in arbitrary relative order, and ISR caches whichever won that day — "ordered" without a tiebreaker still means "unstable". The tiebreaker is insertion order and makes no claim about recency.

It is `id` ASC for four of the five collections. **Person skills are the exception:** `person_skill` has a composite primary key `(person_id, skill_id)` and **no `id` column of its own**, so there is no row id to sort by. Its tiebreaker is `skillId` ASC — the joined `skill.id`, which is also the name the response payload uses. Do not write `id` here; it does not exist.

**NULL placement is specified behavior, not inherited behavior.** Two sort keys in the table above are nullable, and MySQL sorts NULL lowest, which would silently place both groups *first*:

| Column | Nullable | Specified placement |
|---|---|---|
| `project.start_date` | yes — the only nullable date of the three | undated projects **last** |
| `skill.category` | yes | uncategorized skills **last** |

Both must be expressed explicitly — `ORDER BY start_date IS NULL, start_date DESC, id ASC` and `ORDER BY category IS NULL, category ASC, name ASC, skill_id ASC` — rather than relying on the engine default. The default happens to disagree with both rules today, so leaving it implicit is not merely fragile, it is wrong now. `experience.start_date` and `education.start_date` are `NOT NULL`; do not add NULL handling there, where it would be dead code implying a nullability the schema does not have.

**Implementation note — the nullable cases need `@Query`.** Spring Data's derived method names support `OrderBy…Asc/Desc` chains but cannot express a synthetic `IS NULL` sort key. Experiences, education and the skill catalog can use the derived form (`findByPersonIdOrderByStartDateDescIdAsc`); **projects and person skills cannot** and require an explicit `@Query`. Following the derived idiom there would compile, look right, and produce the wrong NULL placement.

Ordering is **not** pagination — § Non-goals rules out the latter for v1 and says nothing about the former.

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

| Verb | Path | Request body | Returns |
|---|---|---|---|
| GET | `/api/v1/people/{personId}/skills` | — | 200, array of `{ skillId, name, category, proficiency }` |
| PUT | `/api/v1/people/{personId}/skills/{skillId}` | `{ "proficiency": "ADVANCED" }` | 200, the assignment — `{ skillId, name, category, proficiency }` |
| DELETE | `/api/v1/people/{personId}/skills/{skillId}` | — | 204 |

`proficiency` ∈ `BEGINNER | INTERMEDIATE | ADVANCED | EXPERT` (matches the `person_skill` enum in cv-database).

**The assignment PUT, spelled out** (amended 2026-08-20, T-024). The `Returns` column previously carried `200, body { "proficiency": "ADVANCED" } — upsert`, conflating the request with the response: it was the only cell in this document showing a request body inline, and read literally it made PUT return a different shape than GET on the same resource. It is now two columns, and the semantics are stated rather than inferred:

- **Request body** is `{ "proficiency": ... }` alone. `personId` and `skillId` come from the path and must not be repeated in the body.
- **Response body** is the **same shape the GET returns for one element** — `{ skillId, name, category, proficiency }`, the joined view including the catalog's `name` and `category`. A GET and a PUT on one resource return the same shape; nothing here asks for two answers.
- **`200` on both branches.** PUT is an upsert: it returns `200` whether it created the assignment or updated an existing one. There is deliberately **no `201` variant** — unlike `POST /api/v1/skills`, which is explicitly `201`. Absence of a 201 in this table is now a stated rule, not an inference.
- Unknown `personId` **or** unknown `skillId` → `404` (design rule 4). A person and skill that both exist with no assignment linking them is not an unknown id: PUT **creates** it and returns `200`, while DELETE returns `404` because there is no existing resource to remove. The two verbs diverge on "absent" on purpose.

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
- **Preserves upstream order** in every section array — the BFF does not sort, re-sort, or reverse. Ordering is settled in § Ordering and owned by the domain service; a `.sort()` in this layer is a second source of truth and a review blocker.
- No `id`, `personId`, `skillId`, or `email` fields in the public payload.
- Person 404 upstream → 404. Any section fetch failing → 502 (the public site treats the CV as one unit).
- The existing person endpoint keeps its behavior and payload; only its **path** moves, from `/api/v1/people/:id` to `/bff/api/v1/people/:id`, per the edge-path decision above. Consumers must update their base URL — this is a breaking change for `cv-public-vanilla`, which calls the old path today.

## Non-goals (v1)

- Pagination (CV sections are small by nature).
- PATCH semantics — `PUT` replaces.

> **Removed 2026-08-13 (T-013):** *"Auth changes — the existing `AUTH_ENABLED` behavior in both services covers these routes as-is."* This was false for a deployed public BFF. `AUTH_ENABLED=true` applies `requireAuth()` to all of `/api/v1`, which would 401 every anonymous visitor to the public site; `AUTH_ENABLED=false` would leave the whole surface open. Neither is "covered as-is". The public-route allowlist in § BFF replaces it, and auth on the BFF is now explicitly **in scope** for v1.
