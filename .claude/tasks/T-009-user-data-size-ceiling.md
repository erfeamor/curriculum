---
id: T-009
title: Get the CI host's provisioning script out of user_data before it hits the 16 KB wall
repo: cv-infra
status: done
owner: infrastructure-engineer
branch: feat/provision-script-from-s3
pr: https://github.com/erfeamor/cv-infra/pull/18
depends_on: [T-002]
risk: normal
security_review: true
checkpoint:
  stage: done               # merged as a9706fb (cv-infra#18), 2026-08-19
  APPLIED: true
  result: "user_data 16,104 B (98.3%, 280 B headroom) -> 3,528 B (21.5%, 12,856 B headroom). 78% smaller. The <4 KB acceptance criterion is met."
  design_note: "The expected SHA-256 lives in SSM, not baked into the bootstrap stub. That is what fixes the SECOND cost this task names: an inlined checksum would change user_data on every script edit, and a user_data change stop/modify/starts the instance -- the source of T-002's repeated ~90s Drone outages. The re-provision signal is not lost: null_resource.jenkins_provision still triggers on sha256(local.jenkins_provision_script), so an edit still reaches the live box over SSM Run Command; only the reboot is gone."
  comment_irony: "First measurement was 4,403 B -- missing <4 KB by 307 bytes because the stub's OWN header comments were 2.2 KB. Trimming them would have been the exact toll this task exists to stop paying, so the rationale moved to ci-provision.tf, which has no size budget. Nothing was lost; the figure came in at 3,528."
  verification: "Against the live account, not by reading Terraform. (1) Applied 7 added / 1 changed in place / 0 destroyed; plan clean after. (2) SSM checksum == uploaded object hash -- the pair-consistency that CANNOT be asserted at plan time, because local.jenkins_provision_script embeds aws_eip.drone.public_ip and is unknown under command=plan. (3) On the live box via SSM Run Command: downloaded through the instance role and checksum verified, proving the scoped s3:GetObject grant works. (4) NEGATIVE TEST -- corrupted the SSM checksum deliberately; the bootstrap REFUSED with an exact mismatch message and non-zero exit, then Terraform detected the drift and restored it. That is this task's 'fails loudly, demonstrated -- not assumed' criterion. (5) terraform test 3/0, size guard tightened 16 KB -> 8 KB and MUTATION-TESTED: fires when the template is inflated, passes when restored."
  criterion_not_met: "The 'fresh boot self-provisions Jenkins' criterion was NOT executed, deliberately. A fresh boot means replacing the instance, which destroys Drone's SQLite -- and T-008 records that the drone-deploy AWS credentials exist ONLY in /var/lib/drone/database.sqlite: not in SSM, not in Terraform state, not reconstructable. ci.tf's lifecycle ignore_changes=[ami] exists for the same reason. So this task's own acceptance criterion, executed literally, would destroy unbacked-up credentials. The SSM probe exercises the identical fetch -> verify -> execute path without that cost. If a real replacement test is ever wanted, T-008 lands first."
  t005_reconciliation: "This grants the drone instance role s3:GetObject on ONE object ARN, which widens a role T-005 wants to narrow. The two are compatible and it is worth being explicit: T-005's control is metadata_options http_put_response_hop_limit=1, which stops CONTAINERS reaching IMDS. This grant is used host-side by the bootstrap before any container exists, exactly like the existing param() helper. A container still cannot use it once T-005 lands."
---

## Why this exists

`aws_instance.drone`'s `user_data` is the concatenation of two rendered templates, and it is nearly full:

| Piece | Rendered bytes |
|---|---|
| `templates/drone-user-data.sh` | 2,148 |
| `templates/jenkins-provision.sh` | 13,532 |
| joined | **15,681** |

EC2's limit is **16,384 bytes** (measured before base64 encoding, which is what the join above measures). That leaves **703 bytes — 95.7% consumed**, and `jenkins-provision.sh` alone is 86% of the payload.

This is not theoretical drift. Over T-002 the figure went **85.6% → 91.1% → 94.4% → 95.7%**, and *three consecutive bug fixes each required trimming explanatory comments back out of the script to fit*. Comments were deleted not because they were wrong but because they did not fit. That is a bad trade being made repeatedly, and the trend line reaches the wall well before the work on this box is finished — T-005 alone plans to add metadata options and split parameter paths, and T-007 needs a few `systemctl` lines.

## The failure mode is worse than "it stops fitting"

Exceeding the limit is not caught by `terraform fmt`, `validate`, or `terraform test` — `tests/plan.tftest.hcl` runs under `mock_provider` and never evaluates the real length. It surfaces as an **apply-time API rejection on a live CI host**, in the same window where `aws_instance.drone` is being modified. The person who trips it will be mid-apply on the box that gates two repos' CI, which is precisely the situation T-002's pre-apply gate existed to avoid.

There is also a second, quieter cost: because `user_data` currently carries the whole script, any edit to `jenkins-provision.sh` changes the `user_data` hash, which makes Terraform stop/start the instance on every provisioning tweak. That is where T-002's repeated ~90 s Drone outages came from.

## Proposed fix — stage the script in S3, fetch it at boot

Keep `drone-user-data.sh` in `user_data` (2,148 B) and reduce the Jenkins half to a short bootstrap that fetches and runs the real script. That drops `user_data` to roughly **2.5 KB, ~15% of the limit**, restoring years of headroom instead of bytes.

Sketch, not a prescription:

- `aws_s3_object` holding `local.jenkins_provision_script`, in a **new private bucket** — *not* `aws_s3_bucket.frontend`, which is served to the internet through CloudFront/OAC.
- A bootstrap in `user_data` that does `aws s3 cp` and executes it.
- A scoped `s3:GetObject` on **that object only** added to the drone instance role.

## Things that will bite, in rough order of nastiness

1. **The instance role has no S3 access today.** Verified: the only `s3:*` grants in `iam.tf` belong to the `aws_iam_user.drone_deploy` *user* and are scoped to the frontend bucket. `aws_iam_role.drone` currently carries SSM parameter reads and `AmazonSSMManagedInstanceCore` only. This task widens the CI host's role — which is exactly what T-005 is trying to narrow. **Coordinate with T-005**, and scope the grant to the single object ARN, not the bucket.
2. **Verify what you fetch.** A bootstrap that blindly executes whatever it downloads converts a size limit into a code-execution path on the CI host, on a box that already mounts the docker socket. Pass the expected SHA-256 as a `templatefile` variable and check it before executing. Do not skip this because "it is our own bucket".
3. **Ordering and the boot-time chicken-and-egg.** The object must exist before the instance boots (`depends_on`), and a fetch failure must be *loud* — an instance that boots with no Jenkins and no error is the same class of silent success that `compute.tf`'s history already records once.
4. **Losing the change signal.** Today, editing the script changes `user_data`, which at least records that something changed. Once the body lives in S3, `user_data` stops moving — so the S3 object's etag/version must become a trigger on `null_resource.jenkins_provision`, or a script edit will apply cleanly and provision nothing.
5. **Decide what the SSM path does.** `null_resource.jenkins_provision` renders the *same* template and pushes it via Run Command, which has no 16 KB limit. Keeping that path inline is simpler and preserves the single-source-of-truth that `ci.tf`'s header comment is careful about. Say which you chose and why.
6. **Do not "fix" this by minifying.** Stripping comments or shortening variable names buys a few hundred bytes and costs the explanatory comments that three separate review rounds asked for. The whole point is to stop paying that toll.

## Out of scope

Splitting Jenkins onto its own instance (that is the alternative T-002 rejected on cost), and any change to what the provisioning script actually *does*.

## Acceptance criteria

- [ ] Rendered `user_data` for `aws_instance.drone` is **under 4 KB**, with the measured figure recorded in the PR.
- [ ] `terraform test` gains an assertion that fails if rendered `user_data` exceeds ~8 KB, so the next person hits a red test rather than an apply-time API error. (Note the current `mock_provider` setup cannot see `aws_eip.drone.public_ip` under `command = plan` — solve it with a `variables`-driven render or a dedicated `run` block rather than dropping the assertion.)
- [ ] The provisioning script is fetched from a **private** bucket, never the frontend bucket, and its integrity is **verified against a checksum** before execution.
- [ ] The instance role's new S3 grant is scoped to the single object ARN; `/security-review` clean, with the widening explicitly reconciled against T-005's intent.
- [ ] A fetch or checksum failure at boot fails **loudly** and visibly, demonstrated — not assumed.
- [ ] Editing `templates/jenkins-provision.sh` still causes a re-provision (the S3 object version/etag is wired as a trigger).
- [ ] A real apply proves it: fresh boot self-provisions Jenkins, and both repos' CI still goes green afterwards.

## Definition of done

PR open against `master` from `feat/provision-script-from-s3`, `terraform fmt`/`validate`/`test` green with the new size assertion, applied for real, and both `cv-domain-service` and `cv-database` verified still posting commit statuses afterwards.

## Housekeeping

~~`T-007`'s "Watch out for" section quotes **91.1%** — stale as of this task's measurement. Correct it to point here instead of restating a number that keeps moving.~~ **Done — closed 2026-08-17.** [T-007](T-007-ecs-agent-cleanup.md)'s watch-out now reads 95.7%, tells the reader to re-measure rather than trust any quoted figure, and points here. The request outlived its own fulfilment.
