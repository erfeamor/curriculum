---
id: T-503
title: "Put a real CV in production: replace T-018's durability-probe rows (human data entry through the admin)"
repo: cv-project (meta)
status: todo
owner:
branch:
pr:
depends_on: []
risk: low
security_review: false
---

## Why

Found 2026-10-04 (T-404's live check), filed as its own task by the 2026-10-06 board review. Production's only person is T-018's durability probe ("T018 Survival Probe", experience "T018 Testing Co" / "Durability Probe", skill `t018-probe-skill`), so **both public sites render test data**. Dev seeds are dev-only and never reach production. [T-501](T-501-e2e-cv-milestone.md)'s AWS step can't meaningfully verify "the CV" until real content exists.

## Scope

- **The human decides whose CV** production shows (theirs, or a clearly-labelled sample persona) and enters it through `https://dvdlxl0zqepqi.cloudfront.net/admin/`: person, experiences, education, skills, projects.
- Remove the probe rows (the person and its sections) once the real person exists, or repurpose person 1. Note that both public sites read **person 1** (`VITE_PERSON_ID` / `PERSON_ID` default `1`); if the real CV is a different id, the sites' person id must change too.
- The driver verifies: both public sites render the new CV; no `T018` strings remain.

## Acceptance criteria

- [ ] Production person 1 (or the configured id) is the real CV, with all four sections populated.
- [ ] No probe data remains, or it's recorded why it stays.
