---
id: T-023
title: "The documented E2E smoke command curls a path the BFF no longer serves"
repo: cv-project (meta)
status: todo
owner:
branch: docs/bff-smoke-path
pr:
depends_on: []
risk: trivial
security_review: false
---

## Why this exists

**Nobody owned this.** Filed 2026-08-17 during a board consistency sweep.

`CLAUDE.md:37` — the file every agent loads at the start of every session — documents the project's end-to-end smoke test as:

```bash
curl localhost:3000/api/v1/people/1                    # E2E smoke: BFF → Java → MySQL
```

`README.md:247` carries the same command with the same path. **That path no longer exists.** T-013 ratified `/bff/*` as the BFF's public edge prefix and T-202 implemented it on 2026-08-13, removing `/api/v1` from `cv-bff-node` entirely (`docs/api-contract.md` § BFF: *"only its path moves, from `/api/v1/people/:id` to `/bff/api/v1/people/:id`"*). The documented smoke test now 404s, in local dev and in AWS alike.

The correct command is:

```bash
curl localhost:3000/bff/api/v1/people/1
```

### Why it was nobody's job

Three tasks touch the neighbourhood and each one legitimately excludes it:

- **T-015** corrects the meta docs that claim the BFF is *deployed* — a different set of claims, and it is gated behind T-014 and T-403, so it cannot fix a wrong command that is wrong *today*.
- **T-016** notices the drift in passing (*"not the `/api/v1` form still written in the meta CLAUDE.md"*) but scopes itself to the MySQL 8.4 bump.
- **T-202** changed the path but lives in `cv-bff-node`; meta-repo docs are outside its repo.

So the drift sat in the most-read file in the workspace for four days with no owner. Same failure class as T-020: a documented assumption nobody re-checked, discovered only because someone went looking.

## Scope

**Three files, one path each** (this said "two" until 2026-08-20; the bullet list below always had three entries, and the third was verified present that day — see it). Deliberately small — resist widening it into T-015's territory.

- `CLAUDE.md:37` — the smoke command in § Commands.
- `README.md:247` — the same command in the local-development section (note this one is annotated *"vanilla-site path"*, which makes it doubly wrong: `cv-public-vanilla` calls the BFF, and T-403 will bake the `/bff` base URL into its bundle).
- `README.es.md:247` — the Spanish counterpart, **confirmed present 2026-08-20**, not a maybe: `curl http://localhost:3000/api/v1/people/1   # ruta del sitio público: BFF → servicio de dominio → MySQL`. Same dead path, same misleading annotation. Fix it in the same PR — the two READMEs are maintained in parallel and half-fixing them is how the next sweep finds this again.
- Any other file that curls port 3000. A `grep -rn "3000/api/v1"` on 2026-08-20 returned exactly these three lines and nothing else.

## Acceptance criteria

- [ ] `grep -rn "3000/api/v1" .` across the meta repo returns nothing that documents a current command.
- [ ] Every documented curl against port 3000 uses `/bff/api/v1`, and **each one was actually run against the local stack** before the PR — the whole point of this task is that a command was written down and never executed again.
- [ ] The domain-service smoke commands (port 8080, `/api/v1`) are left alone — that path is unchanged and correct.
- [ ] No changes to deployment claims; those are T-015's, and duplicating them here would create a second answer.

## Definition of done

PR open against `master` from `docs/bff-smoke-path`, merged.

## dev-loop notes

- **Developer:** `tech-product-owner` (meta-repo docs). **Reviewer:** `/code-review` only — `risk: trivial`, docs-only, H1/H2 as one-line confirms.
- **Verify by running, not by reading.** The stack must be up for the check to mean anything: a path that "looks right" is exactly what is already committed. If the local stack cannot be brought up, say so in the PR rather than asserting the command works.
- **Interacts with [T-016](T-016-dev-prod-mysql-parity.md)**, whose acceptance criteria already require running the corrected smoke command against MySQL 8.4. If T-016 is claimed first, it proves this fix; if this lands first, T-016 inherits a correct command to run. Neither blocks the other.
