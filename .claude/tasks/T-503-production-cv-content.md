---
id: T-503
title: "Put a real CV in production: replace T-018's durability-probe rows (human data entry through the admin)"
repo: cv-project (meta)
status: done
owner: tech-product-owner
branch:
pr: none   # production data change, no code
depends_on: []
risk: low
security_review: false
---

## Done — 2026-10-06 (driver, on the human's decision)

**Decided by the human, 2026-10-06:** production shows **their own CV**, from `~/Documentos/Curriculum vitae.pdf` (sha256 `5e1e57ff…`); location = the full street address and phone as printed (their call; see the phone note below); write path = **direct SQL through SSM** (writes need a user token since T-116, which the driver can't obtain); Projects = this demo + the MonticoM health platform (the PDF has none); proficiency by emphasis (EXPERT: TypeScript, JavaScript, React, Web Performance, Core Web Vitals, Micro-frontends, Claude Code, Spanish; ADVANCED: the rest).

- **Dry run first** on a throwaway local MySQL 8.4 with V1+V2 and a copy of the probe rows. It caught a bug in the transaction's guard: comment lines between the `UPDATE` and the `SET @updated = ROW_COUNT()` are sent as statements and reset `ROW_COUNT()` to 0, so every run aborted (and rolled back). Fixed by keeping nothing between them; a second run aborts by design (the guard requires person 1 to still be the probe).
- **Backup** taken just before: `s3://cv-project-mysql-backup-dev/mysql-dumps/cv-20261006T215528Z.sql.gz` (the host's own `mysql-backup.service`).
- **One transaction** (SSM `AWS-RunShellScript`, the SQL base64-piped into `docker exec -i mysql mysql`): person 1 updated in place (id kept, so neither site's person id changes; `version` 1 → 2), its sections and the `t018-probe-skill` deleted, then 7 experiences, 3 education rows (degree + two certifications), 2 projects, 30 skills (4 PDF categories + `Languages`), 30 assignments. Output: guard passed, counts 7/3/2/30, probe skill left 0.
- **Verified:** CloudFront `/bff/api/v1/people/1/cv` 200 with all four sections and no `id`/`personId`/`skillId`/`email`/`version`/`T018`; `/people/1` the same head; cv-public-react revalidated (Vercel `STALE` → new content, no `T018`); the vanilla site reads the same endpoint.
- **Phone is not public:** neither public BFF payload carries `phone` (the aggregate's head is `name`, `headline`, `location`, `summary`), so the stored number is visible only through the authenticated domain API / admin. The street address *is* public (`location`).
- **Small edits from the PDF:** the Netskope bullet's duplicated phrase ("Designed automated refactoring and static analysis scripts LLM-assisted…") became "Designed LLM-assisted refactoring and static analysis workflows"; Abadia's "software using." lost the stray "using"; bullets are joined with newlines (the sites render them as one paragraph). Dates with only a year use Jan 1 / Dec 31; month-only end dates use the month's last day.

## Why

Found 2026-10-04 (T-404's live check), filed as its own task by the 2026-10-06 board review. Production's only person is T-018's durability probe ("T018 Survival Probe", experience "T018 Testing Co" / "Durability Probe", skill `t018-probe-skill`), so **both public sites render test data**. Dev seeds are dev-only and never reach production. [T-501](T-501-e2e-cv-milestone.md)'s AWS step can't meaningfully verify "the CV" until real content exists.

## Scope

- **The human decides whose CV** production shows (theirs, or a clearly-labelled sample persona) and enters it through `https://dvdlxl0zqepqi.cloudfront.net/admin/`: person, experiences, education, skills, projects.
- Remove the probe rows (the person and its sections) once the real person exists, or repurpose person 1. Note that both public sites read **person 1** (`VITE_PERSON_ID` / `PERSON_ID` default `1`); if the real CV is a different id, the sites' person id must change too.
- The driver verifies: both public sites render the new CV; no `T018` strings remain.

## Acceptance criteria

- [x] Production person 1 (or the configured id) is the real CV, with all four sections populated.
- [x] No probe data remains, or it's recorded why it stays.
