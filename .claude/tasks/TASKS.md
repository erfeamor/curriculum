# Board

Protocol: [README.md](README.md) · Contract: [docs/api-contract.md](../../docs/api-contract.md)

## M2 — Complete the domain model end-to-end

| ID | Title | Repo | Status | Owner | Depends on | PR |
|----|-------|------|--------|-------|------------|----|
| [T-101](T-101-experience-resource.md) | Experience resource in the domain API | cv-domain-service | todo | | — | |
| [T-102](T-102-education-resource.md) | Education resource in the domain API | cv-domain-service | todo | | — | |
| [T-103](T-103-skills-catalog-and-assignments.md) | Skill catalog + person-skill assignments | cv-domain-service | todo | | — | |
| [T-104](T-104-project-resource.md) | Project resource in the domain API | cv-domain-service | todo | | — | |
| [T-151](T-151-dev-seeds-cv-sections.md) | Dev seed data for CV sections | cv-database | todo | | — | |
| [T-201](T-201-bff-cv-aggregate.md) | BFF: aggregated public CV endpoint | cv-bff-node | todo | | T-101…T-104 | |
| [T-301](T-301-admin-cv-sections-crud.md) | Admin UI: CRUD for the four sections | cv-admin-react | todo | | T-101…T-104 | |
| [T-401](T-401-public-cv-sections.md) | Public site: render full CV | cv-public-vanilla | todo | | T-201 | |
| [T-501](T-501-e2e-cv-milestone.md) | End-to-end verification + roadmap close-out | cv-project | todo | | all above | |

### Parallelization notes (read before claiming)

- **Wave 1 (5 agents in parallel):** T-101, T-102, T-103, T-104, T-151 — fully independent; the four API tasks touch disjoint packages, so PRs won't conflict except trivially.
- **Wave 2:** T-201 and T-301 — both may *start* against the contract (mocked upstreams) during wave 1; their final verification needs wave 1 merged.
- **Wave 3:** T-401 after T-201; T-501 strictly last.
- T-103 is the highest-risk API task (composite key, upsert, 409) — assign it to the strongest agent or start it first.
