---
id: T-008
title: Retire the T-002 gate snapshot, and give the CI host a real backup
repo: cv-infra
status: in_review
owner: tech-product-owner
branch: chore/drone-host-backup
pr: https://github.com/erfeamor/cv-infra/pull/23
depends_on: [T-002]
risk: normal
security_review: true
checkpoint:
  stage: qa   # review converged r2 (59f3b82); cv-infra#23 open (no CI in cv-infra). NEXT = the LIVE part, deferred by the human to the START of session 2: apply → CI host up after a reaper tick → SSM tunnel → safe cutover (runbook) → real deploy → SQLite rebuild rehearsal (human does GitHub OAuth + copies a fresh Drone token) → delete snap-0d7f5ae272ce0cef5 → H2
  repo: cv-infra
  branch: chore/drone-host-backup
  worktree: none   # main cv-infra checkout (state is remote now, but tfvars is local and gitignored)
  commit: 59f3b82   # branch head, main cv-infra checkout is ON this branch
  pr: https://github.com/erfeamor/cv-infra/pull/23
  developer: infrastructure-engineer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true   # creates an IAM access key + SSM secret; touches CI secrets
  review_round: 2   # r1: /code-review high 10 findings fixed in 700fd15; r2: /security-review 1 Medium
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a   # live rehearsal on the CI host
  updated: 2026-09-28T17:00:00+02:00
  budget:
    turns: 232   # --since 2026-09-28T07:50:05.000Z (session 1)
    total_tokens: 95000000
    subagent_tokens: 0
    spawns: 2   # quality-assurance (plan) + infrastructure-engineer
    status: ok
    checked: 2026-09-28T15:00:00+02:00
---

## H1 — design decided by the human, 2026-09-28

1. **The credential moves out of the SQLite.** Terraform creates a **new** `aws_iam_access_key` for `drone-deploy`, stored as an SSM SecureString. Its secret lands in the Terraform state, which has been in the encrypted S3 backend since T-004. A reseed script sets `cv-admin-react`'s Drone repo secrets from SSM. The old out-of-band key is **deleted after cutover**. That also rotates a credential that sat on an unencrypted disk.
2. **The Drone SQLite is reconstructable, and rehearsed.** No ongoing backup, and **no new IAM grant** on the CI role, which build containers can reach until T-007. A live rehearsal on the CI host proves the rebuild: move the DB aside, GitHub login, activate `cv-admin-react`, reseed, push, green build. There is also a one-off pre-T-007 copy of the SQLite, kept locally at 0600 in `~/.local/share/cv-infra-state-backups/<date>/`. Build history is expendable.
3. **Encryption happens at [T-007](T-007-ecs-agent-cleanup.md)'s replacement.** It uses an encrypted root with the AWS-managed EBS key, at no extra cost and with no in-place conversion. `snap-0d7f5ae272ce0cef5` (unencrypted) is deleted **after the rehearsal is proven**. **`JENKINS_HOME` is out of scope:** its jobs are seeded by provisioning code (T-026), and its build history is expendable.

> **Board review 2026-09-28**: runs **after [T-004](T-004-terraform-state-hardening.md) part 2** (remote state) in the same session, so this task's apply is the first against the S3 backend. This is lane ordering, not a `depends_on` edge: T-004's other criteria must not block the backup.


**H1 decision 2 amended by the human at review round 1 (2026-09-28): no off-host SQLite copy.** Review showed Drone stores repo secrets and GitHub OAuth tokens **unencrypted** in `database.sqlite`, since `DRONE_DATABASE_SECRET` is unset. Every route off the host either failed (`aws s3 presign` has no PUT) or left a lingering copy (the CI artifacts bucket is versioned). Once the cutover deletes the old key, the file's only value is build history. The fallback during the rehearsal is the moved-aside `database.sqlite.rehearsal-<date>` on the host, which disappears with T-007's replacement. *Observation for T-007/T-005: Drone's SQLite secrets are unencrypted at rest; consider `DRONE_DATABASE_SECRET` when the host is rebuilt.*

**PO settlements at H1 (accepted with the plan):**
- **The SSM path is outside `ci/*`:** `/cv-project/dev/deploy/drone-deploy/{access-key-id,secret-access-key}`. The CI host's role reads `ci/*`, and until T-007 lands so can every build container. Under `ci/*`, the deploy key would reach every build step, not just the deploy step `from_secret` feeds.
- **The reseed runs off-host,** with operator credentials, through an **SSM port-forwarding tunnel** to Drone's API. No new IAM grant, and no secret on plain HTTP (the CI host has no TLS until T-033).
- The rehearsal runs on the real `cv-admin-react` repo, the only Drone repo.

## ▶ First in the cost-trim sequence (added 2026-09-24 — [T-012](T-012-aws-endgame-decision.md) chose A)

Under A this task stops being a precondition for teardown and becomes **step 1 of the trims**: [T-007](T-007-ecs-agent-cleanup.md) now **replaces the CI host** (AMI swap, smaller root) and depends on this task, because Drone's credentials live only on that root disk and in `snap-0d7f5ae272ce0cef5` until they are in SSM and a restore has been proven. Deleting the snapshot afterwards saves **$0.69/month** (Cost Explorer, `EBS:SnapshotUsage`, 2026-08-24 → 09-23).


## Why this exists

Two things, one small and one not.

### The small one: an orphan snapshot with no owner

T-002's pre-apply gate (step 6) took a one-off EBS snapshot of the CI host's root volume before the `t3.small` resize and the live `drone-server` remediation:

```
snap-0d7f5ae272ce0cef5   30 GiB   from vol-0c82f0d4725b608c2   2026-08-08T08:01:04Z
Tags: Project=cv-project, Task=T-002, Purpose=pre-apply-gate
```

It exists purely as a rollback for that apply. Once T-002's post-apply verification passes it is dead weight: incremental storage, ~~roughly **$0.40–0.50/month**, on a stack where T-002 already had to seek an explicit Free Tier exception for +$8/month~~ **$0.69/month measured** (Cost Explorer, see the header; the account is going Paid under T-012, so there is no "Free Tier exception" to count against). Nothing currently deletes it and nothing reminds anyone to.

It is also **unencrypted**, since snapshots inherit the source volume's encryption and `vol-0c82f0d4725b608c2` is not encrypted. See below for why that is more than a formality here.

### The real one: `/var/lib/drone` has no backup at all

The gate turned up where Drone's state actually lives — and it is not where you would guess:

- **Not a docker volume.** `docker volume ls` on the CI host returns nothing.
- It is a host bind mount, `/var/lib/drone` → `/data`, containing a single **1.35 MB `database.sqlite`**.

That file holds the activated-repo list (`cv-admin-react`), the build history, and — the part that matters — Drone's secrets:

```
aws_access_key_id
aws_secret_access_key
```

These are the `drone-deploy` IAM user's credentials from `iam.tf`. **They exist nowhere else.** They are not in SSM Parameter Store, not in `terraform.tfvars`, not in Terraform state. Losing that 1.35 MB file means re-issuing an IAM access key and re-entering it in the Drone UI by hand, plus re-activating repositories.

Today the only copy is on one unencrypted EBS root volume, on one instance, with no snapshot schedule. `snap-0d7f5ae272ce0cef5` is the first backup this data has ever had, and it was taken by accident of a different task's checklist.

This is the same class of gap **T-001** records for self-hosted MySQL ("durability rests on the instance's volume"), and the same answer probably applies — but it is a *different* volume holding *different* unreconstructable data, so it needs its own decision rather than being assumed covered.

## What to decide, not just do

The task is not "write a cron job." Pick and record an answer to:

1. **Is Drone's SQLite worth backing up at all, or should the credentials simply move out of it?** Arguably the better fix is that Drone's AWS secrets should not be the sole copy of anything — issue them from SSM and treat the SQLite as reconstructable. That would shrink this problem to "build history is nice to have." Weigh this *first*; it may make the rest cheap.
2. **If it is worth backing up:** a `dbs`-style periodic `sqlite3 .backup` to S3 (cheap, tiny, restorable file-level — mirrors T-001's intended `mysqldump→S3`), or AWS Backup / DLM snapshot lifecycle on the volume (coarser, costlier, but zero custom code and covers the whole box including Jenkins' `JENKINS_HOME`).
3. **Encryption.** If any of this is going to hold credentials at rest, decide whether the volume and its snapshots should be KMS-encrypted. Note that encrypting an existing volume is not in-place — it means snapshot → `copy-snapshot --encrypted` → new volume → swap, i.e. instance downtime. Scope it honestly or defer it explicitly.

Note that T-002 now also puts **Jenkins' `JENKINS_HOME`** on this same host, so whatever is decided should say whether Jenkins config/job history is in or out of scope.

## New reason this matters — found at T-009, 2026-08-19

**T-009's acceptance criterion could not be executed because of the gap this task exists to close.** It asks for a *"fresh boot self-provisions Jenkins"* proof, which means replacing the instance. Replacing it destroys `/var/lib/drone/database.sqlite`, whose `drone-deploy` AWS credentials this task records as existing **nowhere else**. So the verification was substituted with an SSM probe over the identical fetch → verify → execute path, and the criterion is recorded as deliberately unexecuted.

That is the second time this gap has changed how another task is done ([T-012](T-012-aws-endgame-decision.md)'s option B is the first — it cannot be chosen until this lands). *(2026-09-25: T-012 chose A, so the option-B blocker is moot. The T-009 argument stands, and T-007's replacement is now the concrete case.)* **The cost of not doing T-008 is no longer hypothetical: it is now blocking real verification work**, and it will block it again for any task that wants to prove a clean-boot path on the CI host.

## Sequencing

*(2026-09-25: T-002 is `done` and its post-apply verification passed long ago, so that gate is satisfied. The snapshot's remaining job is to be the Drone credentials' only backup until the SSM move and a proven restore land here.)* The snapshot deletion is gated on T-002's post-apply verification passing — do not delete it while that PR is still unverified, and do not let this task block on the larger backup decision. If the backup design needs more thought, split it: delete the orphan snapshot in a small PR, and keep the design question open.

## Acceptance criteria

- [ ] `snap-0d7f5ae272ce0cef5` deleted, **after** T-002's post-apply verification passes — or explicitly retained with a recorded reason and an owner.
- [ ] A decision recorded (in this file and/or `docs/`) on whether Drone's AWS secrets should move to SSM so the SQLite stops being the sole copy of a credential.
- [ ] If a backup mechanism is adopted: it is in Terraform, not hand-run; it covers `/var/lib/drone`; and it states whether `JENKINS_HOME` is included.
- [ ] A **restore actually performed once** — mount or copy the artifact back and confirm Drone comes up with `cv-admin-react` still active and its secrets intact. An untested backup is not a backup.
- [ ] Encryption decision recorded either way, with its cost/downtime implication stated rather than implied.
- [ ] Any recurring storage cost noted against [T-020](T-020-cost-model-correction.md)'s cost model (was: *"against the Free Tier exception T-002 opened"*; the account is going Paid under T-012), so the running total stays honest.

## Definition of done

PR open against `master` from `chore/drone-host-backup`, the orphan snapshot resolved, and the durability question answered in writing — even if the answer is a deliberate "accept the risk", provided that is recorded rather than left implicit.
