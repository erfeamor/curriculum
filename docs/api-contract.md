# API contract — CV section resources (v1)

Status: **ratified v1** (2026-07-12). Changes require a PR to this file plus sign-off in the task that consumes it. All tasks in `.claude/tasks/` targeting the domain model implement *this* document — when in doubt, this file wins over any task prose.

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

New public endpoint aggregating the full CV in **one** call:

`GET /api/v1/people/:id/cv` → 200:

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
- The existing `GET /api/v1/people/:id` endpoint is unchanged.

## Non-goals (v1)

- Pagination (CV sections are small by nature).
- PATCH semantics — `PUT` replaces.
- Auth changes — the existing `AUTH_ENABLED` behavior in both services covers these routes as-is.
