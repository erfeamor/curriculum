---
id: T-007
title: "CI host: move to a plain AL2023 AMI with a MEASURED root — drops the crash-looping ecs-agent for good and trims the 30 GB disk (widened 2026-09-24, premise corrected 2026-09-25)"
repo: cv-infra
status: todo
owner:
branch: chore/remove-ecs-agent
pr:
depends_on: [T-002, T-008]   # T-008 added 2026-09-24: the AMI swap REPLACES the CI host, and Drone's credentials live only on its root disk until T-008 moves them to SSM and proves a restore
risk: normal   # raised 2026-09-24 from low: the widened scope replaces the CI host
security_review: false   # added 2026-08-20 (hygiene): the key was missing entirely while `risk` was set. Value per adapter §5 — the diff touches none of its security paths; A1 forces /security-review anyway if the real diff disagrees, so this is a stage-0 default, not a ruling.
---


## ⚠ PREMISE CORRECTED 2026-09-25 (board review) — read before planning; verified against Terraform state and EC2

1. **The filter is not the problem, and editing it does nothing.** `ci.tf:81` already resolves `data.aws_ami.al2023`, a **plain** AL2023 filter (`al2023-ami-2023.*-x86_64`). The live host runs `ami-07b263f0fe8404e30` = `al2023-ami-ecs-hvm-2023.0.20260714` only because `ci.tf:150` carries `lifecycle { ignore_changes = [ami, …] }`. **The swap therefore needs an explicit `terraform apply -replace=aws_instance.drone`.** A plan will never propose it by itself. Keep the `ignore_changes`: it is what stops every unrelated apply from replacing the host.
2. **A replacement with no `root_block_device` gets the plain AMI's default: 8 GB.** `aws_instance.drone` sets no root size. Its 30 GB comes from the ECS AMI's default (`terraform state show`: `volume_size = 30`), and the current plain AL2023 image defaults to **8 GB**. With ~17 GiB in use (next section), a bare `-replace` builds a host that cannot hold its own images. **Add an explicit `root_block_device { volume_size = … }`** sized from the measurement.
3. **The "~10 GB" and "−$1.90/month" figures are unproven** until that measurement exists. Re-derive them from the board's own measured rate. T-012 prices the 30 GB root at $2.82/month, which is ≈ $0.094/GB-month: 30 → 20 GB saves ~$0.94/month, and 30 → 12 GB saves ~$1.69/month.
4. **The app host is already on plain AL2023** (`i-029dd84261c922f72`: `al2023-ami-2023.12.20260803.3`). The *"check `aws_instance.domain_service` for the same leftover"* AC below is therefore answered: it is unaffected.

## Disk measured 2026-09-24 (from T-156's review) — read before sizing the new root

The CI host's root is **30 GiB gp3 with 12.8 GiB free**, from Jenkins' disk monitor during cv-database PR-6. About **17 GiB is in use**, so a ~10 GB root **would not fit today's contents**. Nothing on the host prunes images (`templates/jenkins-provision.sh` has no `docker image prune`/`rmi`), and every image bump adds a layer set: Flyway 13.7.0 is 428 MB and now sits beside `:10`'s 283 MB. Either measure what a fresh AL2023 host actually needs after a full build of every Jenkins/Drone repo, or add a scheduled prune in the same change. Do not size from the AMI's default.

## ⤴ WIDENED 2026-09-24 — the AMI swap is now in scope ([T-012](T-012-aws-endgame-decision.md) chose A)

The *Watch out for* note below calls a plain Amazon Linux 2023 AMI *"the right long-term answer … out of scope here"* because it forces a replacement. Under decision A it pays for itself: the ECS-optimized AMI **requires a 30 GB root**, and that root costs **$2.82/month while the host sits stopped**. On a plain AL2023 AMI a ~10 GB root is enough → **≈ −$1.90/month**, and the ecs-agent problem this task was filed for disappears with the AMI instead of being masked.

**Added scope:** swap `aws_instance.drone` to the latest AL2023 AMI (the AL2023 AMI-filter gotcha is in the memory notes — filter `al2023-ami-2023.*-x86_64`, not a wildcard that matches the ECS image); size the root to what Drone + Jenkins + Docker images actually use, measured on the live host (`df`, `docker system df`) plus headroom, not guessed.

**Added acceptance criteria:**
- [ ] The CI host runs a plain AL2023 AMI; `docker ps -a` shows no `ecs-agent` because nothing installs it (the original ACs below then hold trivially — record that rather than re-implementing the mask).
- [ ] Root volume sized from measured usage, with the measurement in the PR.
- [ ] After replacement, restored from [T-008](T-008-drone-host-backup-and-snapshot.md)'s backup: Drone logs in, `cv-admin-react` still active with its secrets, Jenkins jobs present — and a push to each goes green.
- [ ] `user_data` size re-measured (the 16 KB wall, T-009).


## Why this exists

Found while running T-002's pre-apply gate (step 5, live `docker ps -a` on `i-073e5284ca2a1ceed`):

```
ecs-agent   Exited (1) 8 seconds ago   amazon/amazon-ecs-agent:latest
```

It is not exiting once — it is **restart-looping**, exiting non-zero within seconds, continuously. It has evidently been doing so since the instance came up (21 days uptime at the time of the gate).

Nothing in this project uses ECS. `cv-infra` has no `aws_ecs_*` resource of any kind, and neither `templates/drone-user-data.sh` nor `templates/jenkins-provision.sh` starts this container. It is a leftover from the ECS-optimized Amazon Linux AMI the instance was launched from, where `ecs.service` is enabled by default and starts the agent, which then fails because there is no cluster to join.

**Pre-existing and unrelated to T-002** — deliberately left out of that PR's scope rather than fixed opportunistically.

## Why it is worth a task rather than ignoring

It is not merely cosmetic on this box specifically:

- **It burns RAM and CPU on the instance being resized *because of* RAM pressure.** T-002 pays ≈ +$8/month to go `t3.micro` → `t3.small` purely for Maven headroom (see T-002's budget section). A container in a tight restart loop is a small but permanent tax on exactly the resource that money buys.
- **It is continuous noise in `docker ps -a` and the docker daemon logs**, on the one host where `docker ps` is now a diagnostic tool for two CI systems. Anyone debugging Jenkins or Drone has to first learn that this one failure is expected.
- It will reappear on any future instance replacement unless the fix is in code.

## The fix must survive instance replacement

`docker rm -f ecs-agent` on the live box is the *smaller half* of the job and is not sufficient on its own:

1. The container is started by the AMI's `ecs` systemd service, so removing the container without disabling the unit just means it comes back on the next boot.
2. T-002 deliberately splits provisioning: `user_data` is updated for a *future* clean boot while the live box is handled out-of-band via SSM (`null_resource.jenkins_provision`). Any fix here has to follow the same split, or it fixes exactly one of those two paths — which is the failure mode `compute.tf`'s git history already records once.

So: disable and mask the `ecs` unit in the user-data template *and* apply the same change to the live instance, idempotently.

## Watch out for

- ~~**`user_data` is close to EC2's 16 KB limit** — 95.7% as of 2026-08-09, and the figure has moved with every T-002 fix, so do not trust any number quoted here. **Re-measure** before adding lines to `templates/drone-user-data.sh`; a few `systemctl` calls should fit, but do not assume. [T-009](T-009-user-data-size-ceiling.md) exists to remove this constraint — if it has landed, this warning is moot.~~ **Moot: T-009 is `done`.** Re-measuring the size stays an AC of the widened scope.
- Check whether `aws_instance.domain_service` was launched from the same AMI and has the same stray agent — the gate only inspected the CI host. If so, fix both in one PR.
- ~~Consider whether the right long-term answer is a plain Amazon Linux 2023 AMI rather than the ECS-optimized one. That is an AMI change, so it forces instance replacement — **out of scope here**, but worth recording an opinion in the PR if the AMI filter turns out to be selecting the ECS variant unintentionally.~~ **Superseded by the 2026-09-24 widening:** the AMI swap is now the scope. The filter was *not* selecting the ECS variant; `ignore_changes` kept the original ECS image (see the correction at the top).

## Acceptance criteria

> **These are the ORIGINAL ACs, written for the mask-the-unit approach.** Under the widened scope, the AMI swap removes the agent instead. The first four then hold trivially on the new host; record that rather than implementing the mask (the widened ACs above say so too).

- [ ] `ecs` systemd unit disabled and masked, and the `ecs-agent` container removed, on the live CI host.
- [ ] The same change in `templates/drone-user-data.sh` (or the shared provisioning path), so a replacement instance never starts it.
- [ ] Idempotent — safe to re-run against a host where it has already been applied, matching the existing scripts' name-guarded style.
- [ ] `docker ps -a` on the CI host shows no `ecs-agent` entry, and none reappears after a reboot.
- [x] `aws_instance.domain_service` checked for the same leftover; fixed too if present, or explicitly noted as unaffected. *Unaffected: it runs plain AL2023 (checked 2026-09-25, see the correction at the top).*
- [ ] Drone and Jenkins both still healthy afterwards.
- [ ] `user_data` size re-measured and recorded if the template grew.

## Definition of done

PR open against `master` from `chore/remove-ecs-agent`, `terraform fmt`/`validate`/`test` green, reboot persistence demonstrated rather than assumed.
