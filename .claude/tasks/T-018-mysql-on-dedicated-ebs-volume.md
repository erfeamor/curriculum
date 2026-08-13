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
checkpoint:
  stage: H1
  note: "NOT a fresh todo. Stage 0 refinement was completed 2026-08-13 and the DoR rulings below are written up; whoever picks this up starts at IMPLEMENTATION, not refinement. Deliberately left status:todo with no owner so the board cannot repeat the stale-claim bug that parked three wave-1 tasks earlier this session — an H1-complete task with an owner set reads as in-flight and blocks re-pickup under board rule 1."
  repo: cv-infra
  branch: feat/mysql-dedicated-ebs
  worktree: none   # cv-infra cannot be worked from a worktree (local backend; see T-002 worktree_rationale)
  developer: infrastructure-engineer
  reviewers: [code-review, infrastructure-engineer, security-review]
  risk: high
  security_review: true
  h1_status: "refined, awaiting ratification — the five rulings below are PROPOSED, not yet human-ratified"
  budget_note: "Refined under a HARD budget reading (447/400 turns). Refinement only; no code, no spawns. Implementation and the two applies need a fresh session."
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

## Definition of Ready — decisions that must be settled before code

Refined 2026-08-13. Five rulings, each a place where the obvious implementation is wrong.

### 1. The instance's AZ is not currently pinned — fix this first

`compute.tf:31` sets `subnet_id = data.aws_subnets.default.ids[0]`. **`aws_subnets` does not guarantee ordering**, so `ids[0]` can resolve to a different subnet — and therefore a different availability zone — on a later plan.

An EBS volume is **AZ-locked**. If the instance moves AZ and the volume does not, attachment fails and the apply breaks with the database stranded in another zone. Today this is invisible because nothing is AZ-bound; this task makes it load-bearing.

**Ruling:** pin the subnet deterministically before adding the volume — an explicit AZ variable, or a subnet selected by a stable filter rather than list position — and derive `aws_ebs_volume.availability_zone` from that same pinned source so the two cannot diverge. Do not create the volume from a separately-computed AZ.

### 2. The device name Terraform gives you is not the device the kernel shows

`aws_volume_attachment.device_name` takes something like `/dev/sdf`, but these are **nitro instances**: the kernel presents EBS volumes as `/dev/nvme<N>n1`, and **N is not stable across boots**. A bootstrap that formats or mounts `/dev/sdf` either fails or, worse, matches the wrong disk.

**Ruling:** resolve the device by **volume ID**, via `/dev/disk/by-id/nvme-Amazon_Elastic_Block_Store_vol<id>` (note: AWS renders the ID without the `vol-` hyphen in that symlink) or `nvme id-ctrl` output. Never hard-code `/dev/sdf` or `/dev/nvme1n1` in the bootstrap.

### 3. Format only when the volume is genuinely empty — this is the failure that looks like success

**Ruling:** the bootstrap formats **only** if the resolved device has no filesystem, detected with `blkid` (or `file -s`) and a fail-closed default: if detection is ambiguous or errors, **do not format**. An unconditional `mkfs` reformats the database on the next instance replacement and the box comes up looking perfectly healthy — the exact failure this task exists to prevent, delivered by the task itself.

### 4. Mount before MySQL, and make it survive reboot without bricking the box

**Ruling:** mount at `/var/lib/cv-mysql` **before** the `docker run mysql` line in `templates/domain-service-user-data.sh` (currently at line ~38). Persist via `/etc/fstab` **by UUID, not device name** (see ruling 2), with `nofail` so a missing or detached volume degrades to a failed MySQL rather than an unbootable instance that cannot even be reached by SSM to diagnose.

### 5. Start empty; do not migrate the current contents

**Ruling:** the volume starts empty and Flyway rebuilds the schema. The database holds only test data (established at T-001's H1), and the previous instance replacement already discarded it. Writing a one-off data-migration path would add risk to buy nothing. **This ruling expires the moment the demo holds authored content** — at which point this task must run *before* that content exists, not after.

### Open question for the implementer — flag, do not guess

`aws_volume_attachment` destroy can hang waiting for a detach while the old instance is still terminating. `force_detach = true` avoids the hang but risks filesystem corruption if the volume is still mounted and dirty. **Do not reach for `force_detach` reflexively.** Establish what the replacement actually does first — that is what the two-replacement test in the acceptance criteria is for.

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
