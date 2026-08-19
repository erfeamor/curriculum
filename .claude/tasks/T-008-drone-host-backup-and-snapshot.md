---
id: T-008
title: Retire the T-002 gate snapshot, and give the CI host a real backup
repo: cv-infra
status: todo
owner:
branch: chore/drone-host-backup
pr:
depends_on: [T-002]
risk: normal
security_review: true
---

## Why this exists

Two things, one small and one not.

### The small one: an orphan snapshot with no owner

T-002's pre-apply gate (step 6) took a one-off EBS snapshot of the CI host's root volume before the `t3.small` resize and the live `drone-server` remediation:

```
snap-0d7f5ae272ce0cef5   30 GiB   from vol-0c82f0d4725b608c2   2026-08-08T08:01:04Z
Tags: Project=cv-project, Task=T-002, Purpose=pre-apply-gate
```

It exists purely as a rollback for that apply. Once T-002's post-apply verification passes it is dead weight: incremental storage, roughly **$0.40–0.50/month**, on a stack where T-002 already had to seek an explicit Free Tier exception for +$8/month. Nothing currently deletes it and nothing reminds anyone to.

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

That is the second time this gap has changed how another task is done ([T-012](T-012-aws-endgame-decision.md)'s option B is the first — it cannot be chosen until this lands). **The cost of not doing T-008 is no longer hypothetical: it is now blocking real verification work**, and it will block it again for any task that wants to prove a clean-boot path on the CI host.

## Sequencing

The snapshot deletion is gated on T-002's post-apply verification passing — do not delete it while that PR is still unverified, and do not let this task block on the larger backup decision. If the backup design needs more thought, split it: delete the orphan snapshot in a small PR, and keep the design question open.

## Acceptance criteria

- [ ] `snap-0d7f5ae272ce0cef5` deleted, **after** T-002's post-apply verification passes — or explicitly retained with a recorded reason and an owner.
- [ ] A decision recorded (in this file and/or `docs/`) on whether Drone's AWS secrets should move to SSM so the SQLite stops being the sole copy of a credential.
- [ ] If a backup mechanism is adopted: it is in Terraform, not hand-run; it covers `/var/lib/drone`; and it states whether `JENKINS_HOME` is included.
- [ ] A **restore actually performed once** — mount or copy the artifact back and confirm Drone comes up with `cv-admin-react` still active and its secrets intact. An untested backup is not a backup.
- [ ] Encryption decision recorded either way, with its cost/downtime implication stated rather than implied.
- [ ] Any recurring storage cost noted against the Free Tier exception T-002 opened, so the running total stays honest.

## Definition of done

PR open against `master` from `chore/drone-host-backup`, the orphan snapshot resolved, and the durability question answered in writing — even if the answer is a deliberate "accept the risk", provided that is recorded rather than left implicit.
