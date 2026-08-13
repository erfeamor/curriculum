---
id: T-018
title: "Move MySQL onto a dedicated EBS volume so it survives instance replacement"
repo: cv-infra
status: todo
owner:
branch: feat/mysql-dedicated-ebs
pr:
depends_on: []
risk: high
security_review: true
---

## Why this exists

Surfaced during T-001's H1 refinement (2026-08-13). MySQL's data lives at `/var/lib/cv-mysql` on the **instance's own root volume** (`templates/domain-service-user-data.sh:38,44`), and `compute.tf:49` sets `user_data_replace_on_change = true`. Every `user_data` edit therefore **replaces the instance and destroys the database**.

That is not a hypothetical. It has already shaped two tasks:

| Task | Effect |
|---|---|
| **T-001** (backup) | Its own apply destroys the data it exists to protect, at the one moment no backup exists |
| **T-014** (deploy the BFF) | Edits `user_data` to add the BFF container, replacing the instance again |

Both are proceeding anyway because **the database currently holds only test data** — confirmed by the human at T-001's H1. This task exists so that fact is treated as a *deadline*, not a permanent excuse.

## The trigger

**The moment the demo holds authored CV content, the next `user_data` edit silently destroys it.** There is no guard: `terraform apply` will report the replacement in the plan, but nothing distinguishes "replacing a box with a scratch database" from "replacing a box with the only copy of real content".

Do this **before** the demo is populated for real — which, per T-012, is before anything meant to be shown live.

## Scope

- `aws_ebs_volume` + `aws_volume_attachment`, mounted at `/var/lib/cv-mysql`, provisioned so the mount happens before the MySQL container starts.
- Handle the **first-boot vs subsequent-boot** distinction: format the volume only when it is empty, never on reattach. Getting this wrong reformats the database on the next replacement — a worse failure than the one being fixed, because it looks like success.
- A one-off migration of any existing data onto the volume, or an explicit note that it starts empty.
- `terraform test` assertions for the new resources, per the repo's own review guidance.

## Acceptance criteria

- [ ] MySQL data lives on a volume whose lifecycle is independent of the instance.
- [ ] **Proven by test, not by inspection:** a `user_data` change is applied, the instance is replaced, and the database still has its rows afterwards. Reading the Terraform is not evidence — this is precisely the class of claim that was wrong in T-013's review.
- [ ] Reattach does **not** reformat. Exercise the replacement twice.
- [ ] `terraform fmt`/`validate`/`test` pass; volume cost recorded against the credit runway (T-010).

## Definition of done

PR open against `master` from `feat/mysql-dedicated-ebs`, gates green, applied and verified across a real instance replacement, merged.

## dev-loop notes

- **Developer:** `infrastructure-engineer`. **Reviewers:** the full `high`-risk set plus `/security-review`.
- **`risk: high`** — a real apply, a destructive edge, and a failure mode (reformat-on-reattach) that presents as success.
- Cheaper alongside T-014, which already replaces the instance: doing both in one replacement halves the churn. But **do not bundle them into one PR** — T-014 is already the expensive one, and mixing a storage-layout change into it makes both harder to review and to roll back.
