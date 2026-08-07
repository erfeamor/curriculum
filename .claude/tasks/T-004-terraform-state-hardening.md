---
id: T-004
title: Harden Terraform state — permissions now, remote backend properly
repo: cv-infra
status: todo
owner:
branch: chore/tf-state-hardening
pr:
depends_on: []
risk: normal
security_review: required
---

## Why this exists

Found while reviewing how T-002's secrets reach AWS. **`cv-infra/terraform.tfstate` stores every secret in plaintext**, including the ones declared `SecureString` — `SecureString` describes how *AWS* stores a parameter, not how *Terraform* records it. Verified in the live state file:

| Parameter | Declared type | In local state |
|---|---|---|
| `/cv-project/dev/db/password` | `SecureString` | **plaintext** |
| `/cv-project/dev/ci/drone-rpc-secret` | `SecureString` | **plaintext** |
| `/cv-project/dev/ci/github-client-secret` | `SecureString` | **plaintext** |

And the file is **`-rw-rw-r--` (0664)** — group- and world-readable — while `terraform.tfvars` is correctly `0600`.

It is gitignored (`.gitignore:2 *.tfstate`), so nothing reaches the repo. The exposure is local-disk only. But it means the usual advice — "keep secrets out of `tfvars`, pass them as `TF_VAR_…`" — only half-works: **the state captures them regardless of how they were supplied.**

Applying **T-002** adds two more secrets to this file (`jenkins-admin-password`, `github-pat`), so the permissions fix should land first.

## Part 1 — immediate, do before applying T-002

```bash
chmod 600 /home/erfeamor/work/curriculum/cv-infra/terraform.tfstate*
```

Thirty seconds, closes the world-readable window. Not a substitute for part 2.

Also check whether any *other* repo in this workspace has left a local state file at default permissions.

## Part 2 — the real fix: remote backend

Move state to S3 with:

- **Server-side encryption** (SSE-KMS, or SSE-S3 if the KMS key cost isn't justified for a demo).
- **Bucket versioning** — state corruption is recoverable; a truncated local state is not.
- **Public access block** on the bucket, explicitly, not by default.
- **State locking** — DynamoDB table, or S3 native locking (`use_lockfile`) on a recent enough provider. Pick one and record why.
- Bucket policy denying non-TLS access.

This also fixes a problem nobody has filed yet: **state currently lives on exactly one laptop.** Losing that disk means losing the mapping between the config and every live AWS resource — recoverable only by hand-importing each one.

**Free Tier:** S3 and DynamoDB usage at this scale is negligible (well under the free allowances; a few KB of state and a handful of lock writes). Unlike T-002 this needs no cost exception, but confirm rather than assume.

### Migration is the risky step

`terraform init -migrate-state` rewrites where state lives. Before running it:
- Back up `terraform.tfstate` and `.backup` outside the repo.
- Confirm `terraform plan` immediately afterward shows **no changes** — a successful migration is one where Terraform still recognises every existing resource. Any resource showing as "to be created" means the migration lost track of it; stop and restore rather than applying.

## Part 3 — decide on rotation

The secrets have been sitting in a world-readable file. On a single-user laptop the practical risk is low, but "low" is a judgement call, not a fact. Decide explicitly, and record the decision either way:

- `db_password`, `drone_rpc_secret`, `drone_github_client_secret` — rotate, or accept?
- Rotating means: new value in SSM via Terraform, then restart whatever consumes it (the Drone containers read theirs at boot; the domain service reads the DB password at boot).
- Note T-002's finding N8/R8: the Jenkins container's config hash now folds in the fetched secrets, so a rotated secret triggers a container recreate rather than leaving a stale value live. Drone has no equivalent — a rotation there needs a manual restart.

## Acceptance criteria

- [ ] `terraform.tfstate*` are `0600` (part 1, do first).
- [ ] State in S3 with encryption, versioning, public-access block, and locking.
- [ ] `terraform plan` after migration shows **no changes** — proving no resource was orphaned.
- [ ] Local state files removed from the working tree only *after* the remote backend is verified working.
- [ ] `.gitignore` still covers any state artifact that can appear locally.
- [ ] The rotation decision is recorded with its reasoning, whichever way it goes.
- [ ] `terraform fmt -check -recursive`, `terraform validate`, `terraform test` pass.

## Explicitly out of scope

Rotating Cognito or application secrets unrelated to state; changing how secrets reach the instances (that mechanism — SSM + instance profile — is sound and is T-005's territory); any change to `aws_instance` resources.

## Definition of done

PR open against `master` from `chore/tf-state-hardening`, `/security-review` clean, migration verified by a no-change plan, rotation decision recorded.
