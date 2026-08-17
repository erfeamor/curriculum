---
id: T-018
title: "Move MySQL onto a dedicated EBS volume so it survives instance replacement"
repo: cv-infra
status: done
owner: infrastructure-engineer
branch: feat/mysql-dedicated-ebs
pr: https://github.com/erfeamor/cv-infra/pull/16
depends_on: []
risk: high
security_review: true
checkpoint:
  stage: done
  merged: "2026-08-14 as 774a9fc (squash of 4e11fcc + 2470b43), cv-infra PR #16. Branch was 0 commits behind master at merge, so no rebase was needed; gates re-run on the exact merged tree (fmt clean, validate Success, test 2/0). H2 accepted by the human after the full verification below."
  outcome: "The trigger this task was written against is defused: MySQL's datadir now lives on vol-092113db466c84bc1, whose lifecycle is independent of the instance. Every acceptance criterion was proven by test rather than inspection — two instance replacements, a reattach that did not reformat (volume UUID identical across both), and rows written between the applies that read back intact. The two review-round-1 blockers were both real and both would have shipped silently: the detach would have hung against a live busy filesystem, and nofail would have let Docker start MySQL before the mount, initializing a fresh database that the real volume then shadowed. Neither was in the original five rulings — they were found by review, which is the argument for the review stage existing."
  note: "NOT a fresh todo. Stage 0 refinement was completed 2026-08-13 and the DoR rulings below are written up; whoever picks this up starts at IMPLEMENTATION, not refinement. Deliberately left status:todo with no owner so the board cannot repeat the stale-claim bug that parked three wave-1 tasks earlier this session — an H1-complete task with an owner set reads as in-flight and blocks re-pickup under board rule 1."
  claimed: "2026-08-14 — claimed live by the dev-loop driver, which is what makes owner-set safe now: the earlier no-owner state existed because nobody was driving. If H1 is rejected, reset owner and status:todo rather than leaving this claimed."
  premises_reverified: "2026-08-14, before presenting H1. All five rulings re-checked against cv-infra@56dea10: compute.tf:31 ids[0] unchanged; user_data_replace_on_change still true; /var/lib/cv-mysql mkdir at :38 and bind-mount at :44 unchanged; no aws_ebs_volume/aws_volume_attachment/availability_zone anywhere in *.tf, so this is a clean slate. The bootstrap's own comment states the premise: data 'is lost only if the instance itself is replaced'."
  repo: cv-infra
  branch: feat/mysql-dedicated-ebs
  worktree: none   # cv-infra cannot be worked from a worktree (local backend; see T-002 worktree_rationale)
  developer: infrastructure-engineer
  reviewers: [code-review, infrastructure-engineer, security-review]
  risk: high
  security_review: true
  h1_status: "RATIFIED 2026-08-14 — the five rulings are approved as written, developer and reviewer set confirmed, three-replacement verification plan accepted."
  h1_correction: "The board note of 2026-08-14 claimed T-014's apply would serve as this task's second replacement. Withdrawn at H1: this task's acceptance criteria must be met before it merges, so it cannot wait on a later task. Plan is apply #1 (add volume) → write test rows → apply #2 (trivial user_data touch) proving survival and no-reformat-on-reattach. T-014 later is a real-world confirmation, not the proof of record. The T-018-before-T-014 ordering is unaffected."
  review_round: 1
  open_findings: 0
  review_round_1_closed: "2026-08-14, commit 2470b43. All seven findings addressed as adjudicated; gates re-run independently by the driver (fmt clean, validate Success, test 2/0). Finding 4's guard was re-proven BY THE DRIVER, not accepted on report: reverting compute.tf's subnet_id to data.aws_subnets.default.ids[0] now makes terraform test FAIL (1 passed, 1 failed) with the intended message, and restoring it returns 2/0. That re-check matters because the assertion it replaced claimed to pin the same thing and did not — the failure class here is precisely 'a check that manufactures confidence'."
  pre_apply_db_check: "Run 2026-08-14 via SSM against i-038600c71d141035b, immediately before presenting the apply gate — the board requires re-checking contents before any apply that replaces the instance. Result is stronger than the 'test data only' assumption everything was resting on: the cv database is EMPTY. All six content tables (person, experience, education, skill, project, person_skill) report 0 rows; only flyway_schema_history has 1 row. Also confirmed the premise directly: /var/lib/cv-mysql is on /dev/nvme0n1p1, the instance ROOT volume, 75% full, with files dated 2026-08-13 15:21 (i.e. since T-001's replacement). So the apply destroys nothing whatsoever, and ruling 5 ('start empty') is not merely acceptable but exact. CONSEQUENCE FOR VERIFICATION: there is no existing data to prove survival with, so acceptance criterion 2 requires the driver to WRITE test rows after apply #1 and check them after apply #2. Proving 'the database still has its rows' against an empty database would be a vacuous pass — the same class of non-check as the tautological test assertion caught in review round 1."
  apply_1: "Run 2026-08-14. Plan was exactly 4 add / 0 change / 2 destroy: create aws_ebs_volume.mysql_data, replace aws_instance.domain_service (user_data change), replace aws_eip_association, create aws_volume_attachment. Applied clean, no hang. New instance i-0cf98e7849677cb5d, volume vol-092113db466c84bc1, EIP 15.236.195.130 preserved (aws_eip itself untouched, so CloudFront's /api/* origin stays valid). VERIFIED ON THE BOX, not from the plan: /var/lib/cv-mysql is mounted from /dev/nvme1n1 (the new volume) while / remains nvme0n1p1; fstab carries the by-UUID entry with nofail AND x-systemd.required-by/before=docker.service; both containers Up; Flyway rebuilt all six tables; domain-service answers 401 (correct — AUTH_ENABLED defaults on for Java, so this proves it is up and gating, not broken). Ruling 2 confirmed in reality: the by-id symlink resolved as ...Store_vol092113db466c84bc1, hyphen correctly stripped. Ruling 3 confirmed: the log shows 'has no filesystem -- first boot, formatting', i.e. the format branch, correct on a virgin volume."
  apply_1_caveat: "IMPORTANT — apply #1 did NOT exercise finding 1's fix. No attachment existed on the old instance, so Terraform destroyed it without any DetachVolume call; stop_instance_before_detaching was set but unused. The detach path it guards runs for the first time at apply #2. Do not read apply #1's clean run as evidence that the detach hang is solved."
  test_rows_written: "2026-08-14, after apply #1, because the pre-apply check found the database EMPTY and a survival check against zero rows would pass vacuously. Written: person=1 ('T018 Survival Probe', t018-probe@example.invalid), experience=1 ('T018 Testing Co'), skill=1 ('t018-probe-skill'), person_skill=1 (EXPERT). Volume UUID before apply #2: f922852d-6eef-452c-9643-41de45a34514 — the same UUID must be present afterwards, since a reformat would issue a new one. That UUID comparison is the sharpest available evidence against ruling 3's reformat-on-reattach failure, because it cannot be faked by a coincidentally-working database."
  apply_2: "Run 2026-08-14 via `terraform apply -replace=aws_instance.domain_service`. Plan: 3 delete/create (instance, volume attachment, eip association); aws_ebs_volume.mysql_data ABSENT from the plan, i.e. it survives. Applied clean in 1m39s — NO DETACH HANG. This is the first execution of the detach path and it settles the DoR's open question empirically: stop_instance_before_detaching works, and force_detach (which the DoR warned against reaching for) was never needed. New instance i-029dd84261c922f72, EIP 15.236.195.130 preserved."
  apply_2_verification: "All acceptance criteria proven on the box: (a) bootstrap log reads 'already has a filesystem -- reattach, not formatting' — ruling 3's reattach branch, the failure-that-looks-like-success, closed empirically; (b) volume UUID after = f922852d-6eef-452c-9643-41de45a34514, IDENTICAL to before, and a reformat mints a new UUID, so this cannot be faked by a database that merely happens to work; (c) rows survived — person/experience/skill/person_skill all still 1, and the probe row reads back as 'T018 Survival Probe / t018-probe@example.invalid'; (d) both containers Up. Two replacements exercised in total: apply #1 formatted a virgin volume, apply #2 reattached without touching it."
  reboot_test: "Driver-initiated, 2026-08-14 — NOT in the original test plan, added because review finding 2's systemd fix only bites on REBOOT and neither apply could exercise it (both mount synchronously before docker run). Rebooted i-029dd84261c922f72 and verified: rows survived; systemd translated the fstab options into real unit dependencies (RequiredBy=docker.service, Before=docker.service); mount ActiveEnterTimestamp 10:10:24 vs docker.service 10:10:30, so the mount genuinely precedes Docker by 6s; and unmounting revealed the underlying root-volume directory is EMPTY, proving no shadowed fresh database was ever initialized there. That last check is the direct disproof of finding 2's failure mode rather than an inference from ordering."
  stack_health_after: "Re-checked after the reboot test transiently stopped Docker: both containers Up, volume mounted, domain-service answers 401 locally AND through CloudFront (dvdlxl0zqepqi.cloudfront.net/api/v1/people/1) — 401 is correct, AUTH_ENABLED defaults on for Java, so the edge path is intact end to end. The box was not left degraded."
  criterion_wording_gap: "HONEST GAP, for the H2 reviewer. The criterion reads 'a user_data change is applied, the instance is replaced, and the database still has its rows afterwards'. Apply #1 WAS a user_data change that replaced the instance, but no rows existed yet; apply #2 had the rows but was triggered by -replace rather than a user_data edit, deliberately, to avoid inventing a cosmetic file change purely to force a replacement. The composition covers the intent — the storage layer cannot tell how the replacement was triggered — but the literal single-step sequence was not performed. One further ~2min apply would close it if the reviewer wants the letter as well as the intent."
  ci: "cv-infra has no CI system (adapter §3 lists '—'); the local gate commands ARE the authoritative gate. Stage 3 therefore completes at PR open."
  qa_bounces: 0
  fix_attempts: 0
  review_round_1: "/code-review high, 2026-08-14. Seven findings, two blocking, all adjudicated by the PO and routed to the persistent developer via SendMessage (no new spawn). BLOCKING: (1) aws_volume_attachment destroy issues DetachVolume against a STILL-RUNNING instance with the filesystem mounted and mysqld holding files — hangs indefinitely, apply errors half-done. The developer's comment claimed the dependency edge protected against this; it is what causes it. Fix is stop_instance_before_detaching (verified in the provider schema), NOT force_detach. This settles the DoR's open question empirically. (2) nofail is WantedBy but NOT ordered before local-fs.target, so docker.service can start ahead of the mount; the mysql:8.4 entrypoint then initializes a fresh database on the root volume which the real volume silently shadows — and the nightly timer uploads that empty dump to S3. Only bites on REBOOT (first boot mounts synchronously), which is why it was missed. FIXED-NOT-BLOCKING: (3) prevent_destroy + final_snapshot on the volume; (4) the subnet test assertion is a tautology — the shared aws_subnets mock makes it pass even with the pin reverted, proven empirically by the reviewer; (6) vacuous AZ validation. DOCUMENT-ONLY: (5) persisting the datadir breaks db_password rotation — PO downgraded after verifying db_password is a plain input variable, not generated per apply, so it fires only on deliberate rotation; an ALTER USER branch in a boot script is its own hazard and gets its own task. (7) wait-loop timeout leaves an instance Terraform reports as converged; recovery needs -replace, documented not engineered."
  followups_to_file: "T-021 (db_password rotation against a persistent datadir — finding 5). File before T-018 merges."
  a1_result: "PASS, re-run independently by the driver 2026-08-14 (not taken on the developer's word): terraform fmt -check -recursive clean, terraform validate Success, terraform test 2 passed / 0 failed. Diff is 6 files / ~180 insertions."
  a1_risk_recheck: "risk stays high (trivial was never claimed). A1 security-path rules did NOT fire — the diff touches no IAM, security_group, ingress/egress, published ports, CORS, secrets or CI config. security_review stays true on the PO flag from refinement, not on a path match; the real surface is at-rest encryption and a bootstrap that can mkfs a disk."
  a1_az_verification: "Checked against the live account before spending review effort: aws_instance i-038600c71d141035b is ALREADY in eu-west-3a on subnet-063ab75ace0adb750, which is exactly what data.aws_subnets.domain_service resolves to at var.availability_zone's default. Ruling 1's pin therefore codifies current placement rather than moving the instance — no hidden AZ migration in the apply. eu-west-3a/b/c all have default subnets, so the filter cannot come back empty."
  reviewer_set_decision: "PO call, 2026-08-14, recorded rather than taken silently. Adapter §7's high-risk set is '/code-review + specialist + QA coverage, plus /security-review WHEN THE A1 PATH RULES FIRE'. They did not fire (see a1_risk_recheck), so /security-review is not forced; the frontmatter's security_review:true was a stage-0 guess and A1 is the deterministic re-check. The actual surface is thin — no IAM, no security group, no ingress, no secrets, no CI config, and the volume is encrypted at rest. Running it anyway would spend a spawn where it cannot find much. The separate infrastructure-engineer specialist spawn is also skipped: the developer WAS the infrastructure-engineer, and the independent infra lens was applied inline by the driver (device-name resolution, set -e traps in the blkid capture and the wait loop, AZ pinned against the live account) — pipeline.md says never spawn for work the driver can do inline. Spawn budget therefore goes to the live verification at stage 4, which is what actually proves rulings 3 and 4; no amount of static review does. Spawns: developer(1) + /code-review(2) + QA(3), at the cap of 3."
  a1_set_e_verification: "Ruling 3's blkid capture is wrapped in set +e/set -e, so the first-boot case (blkid exit 2) does not abort under the script's set -euo pipefail. Separately verified by experiment that the wait loop's `[ -e ] && break` is exempt from set -e (non-final command in an && list) — it does not abort on the first miss, which would otherwise have made every first boot fail."
  budget_note: "Refined 2026-08-13 under a HARD reading (447/400 turns) — refinement only, no code, no spawns. Resumed 2026-08-14 in a fresh session; probe read ok at 79/400 turns (19.8%) before H1. Inherited cost from the refinement session is NOT re-counted here, per checkpoint.md §3: that session's turns were spent, and this one starts its own count against the same ceiling."
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
- **Order: this task BEFORE T-014** (recorded 2026-08-14). Separate PRs means two replacements either way, so the ordering is not about saving an apply — it is that **T-014's apply *is* this task's second replacement**, and this task's hardest acceptance criterion is "exercise the replacement twice, prove reattach does not reformat". Running T-018 first gets that proof from work already scheduled; running T-014 first buys nothing back and leaves the data-loss window open for another cycle. This task is also further along — its DoR is written and awaiting ratification, while T-014 has no checkpoint and starts at stage 0.
