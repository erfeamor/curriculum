---
id: T-006
title: Contract — define ordering for the CV section collections
repo: cv-project (meta)
status: in_progress
owner: tech-product-owner
branch: docs/contract-section-ordering
pr:
depends_on: []
risk: normal
checkpoint:
  stage: H1
  repo: cv-project (meta)
  branch: docs/contract-section-ordering
  worktree: none   # docs-only change in the meta repo; no build, no stack, nothing to isolate
  developer: tech-product-owner
  reviewers: [code-review, backend-developer]
  risk: normal          # gates take the docs fast-path; the DECISIONS do not (see task DoD)
  security_review: false
  wave: [T-006, T-013]
  wave_slot: 0
  merge_order: 2        # rebases onto T-013 — see wave note below
  file_conflict: "docs/api-contract.md — shares § BFF and the status/version line with T-013"
  qa_stage_4: waived    # docs-only: no stack to exercise; substituted by consumer-buildability review
---

## Why this exists

Surfaced by T-101's stage-2 review. `ExperienceRepository.findByPersonId` returns rows in **whatever order MySQL happens to return them** — no `ORDER BY` anywhere in the chain. `docs/api-contract.md` says nothing about ordering, and T-101's ratified DoR forbids inventing behaviour the contract doesn't specify, so it was correctly left alone and escalated rather than patched.

The consequence is not cosmetic. A CV whose jobs appear in arbitrary order is wrong to a reader, and `cv-public-react` caches its rendered output via ISR — so an arbitrary order gets *frozen* into a cached page, and a later revalidation can silently reshuffle it. The same gap applies to all four section resources, not just Experience.

This is a **contract change**, so per the adapter it is its own PR against `docs/api-contract.md`, sequenced ahead of the consumers via `depends_on` — not improvised inside a consuming task.

Note `docs/api-contract.md` § Non-goals lists *pagination* as out of scope for v1. Ordering is not pagination, and nothing in that section rules it out.

## What has to be decided

Every one of these needs a definite answer written into the contract. They are listed as questions because refinement should settle them, not because implementers may choose.

**1. Ordering per collection.** Proposed starting point, to be confirmed:

| Collection | Proposed order | Rationale |
|---|---|---|
| `experiences` | `startDate DESC` | CV convention — current role first |
| `education` | `startDate DESC` | same |
| `projects` | `startDate DESC` | same |
| `skills` (person) | `category`, then `name` | no date to sort on; grouping by category is how a CV renders them |
| `skills` (catalog) | `name` | it is a lookup list |

**2. NULL handling — this is the sharp edge.** `project.start_date` is **nullable** (unlike experience and education, where it is `NOT NULL`). MySQL sorts NULL as the lowest value, so `ORDER BY start_date DESC` places undated projects **last**. That is probably the behaviour you want, but it must be stated in the contract rather than inherited from an engine detail — a different database, or a future move to a query that sorts in Java, would reverse it silently.

**3. A deterministic tiebreaker is mandatory.** Two experiences starting the same month currently come back in arbitrary relative order, and ISR will cache whichever won that day. Every ordering needs a secondary key — `id` is the obvious one. Without it "ordered" still means "unstable".

**4. Where ordering is enforced.** Recommendation: **the domain service**, so there is one source of truth and the admin UI, the BFF aggregate, and both public sites all agree. The BFF then passes arrays through unchanged. State this in the contract so nobody re-sorts in a frontend and creates a second answer.

## Scope

- `docs/api-contract.md` only. Add ordering to each section's spec — including the BFF aggregate section, which should say it preserves upstream order rather than imposing its own.
- No code in this task. Consuming repos implement it under their own tasks.

## Rollout — the part that needs care

- **T-102, T-103, T-104 have not started.** They should absorb the ordering into their DoR and tests from the start. Their task files need updating once this merges.
- **T-101 — DECIDED 2026-08-13 at this task's H1: follow-up task, filed as [T-105](T-105-experience-ordering-retrofit.md).**
  - The two options below were written while T-101 was still `in_review`. It has since **merged** ([cv-domain-service#3](https://github.com/erfeamor/cv-domain-service/pull/3), 2026-08-09), which killed the first one outright — a merged PR cannot absorb the change. The choice made itself; it is recorded here so the dead option is not rediscovered and re-argued.
  - ~~*Amend T-101's PR* — it is idle anyway and the change is a few characters plus a test; cheapest overall, but it reopens a converged review.~~ **Dead: T-101 is merged.**
  - *Follow-up task* — keeps T-101's review history clean at the cost of another PR. **Chosen.**
- **T-201, T-401, T-402** consume the ordering and should not be implemented against an unspecified contract. `T-201` now lists this task in `depends_on`, which gates the whole downstream chain.

## Acceptance criteria

- [ ] Every section collection in `docs/api-contract.md` has a stated order, including a secondary tiebreaker.
- [ ] NULL placement is stated explicitly for `projects.startDate`, not left to engine behaviour.
- [ ] The document states that ordering is the domain service's responsibility and that the BFF preserves it.
- [ ] The contract's version/status line is updated — it is currently "ratified v1 (2026-07-12)" and this is a change to a ratified document.
- [ ] Consuming task files (T-102, T-103, T-104, T-201, T-401, T-402) updated to reference the new requirement.
- [ ] A decision recorded on how T-101 picks it up.

## Definition of done

PR open against `master` from `docs/contract-section-ordering`, contract updated, consuming tasks updated, T-101 approach decided and recorded. Docs-only, so the `trivial` fast-path applies to the gates — but the *decisions* above are not trivial and should be reviewed on their merits.
