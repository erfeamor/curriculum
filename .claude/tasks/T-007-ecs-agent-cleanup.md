---
id: T-007
title: Remove the crash-looping ecs-agent container from the CI host
repo: cv-infra
status: todo
owner:
branch: chore/remove-ecs-agent
pr:
depends_on: [T-002]
risk: low
security_review: false   # added 2026-08-20 (hygiene): the key was missing entirely while `risk` was set. Value per adapter §5 — the diff touches none of its security paths; A1 forces /security-review anyway if the real diff disagrees, so this is a stage-0 default, not a ruling.
---

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

- **`user_data` is close to EC2's 16 KB limit** — 95.7% as of 2026-08-09, and the figure has moved with every T-002 fix, so do not trust any number quoted here. **Re-measure** before adding lines to `templates/drone-user-data.sh`; a few `systemctl` calls should fit, but do not assume. [T-009](T-009-user-data-size-ceiling.md) exists to remove this constraint — if it has landed, this warning is moot.
- Check whether `aws_instance.domain_service` was launched from the same AMI and has the same stray agent — the gate only inspected the CI host. If so, fix both in one PR.
- Consider whether the right long-term answer is a plain Amazon Linux 2023 AMI rather than the ECS-optimized one. That is an AMI change, so it forces instance replacement — **out of scope here**, but worth recording an opinion in the PR if the AMI filter turns out to be selecting the ECS variant unintentionally.

## Acceptance criteria

- [ ] `ecs` systemd unit disabled and masked, and the `ecs-agent` container removed, on the live CI host.
- [ ] The same change in `templates/drone-user-data.sh` (or the shared provisioning path), so a replacement instance never starts it.
- [ ] Idempotent — safe to re-run against a host where it has already been applied, matching the existing scripts' name-guarded style.
- [ ] `docker ps -a` on the CI host shows no `ecs-agent` entry, and none reappears after a reboot.
- [ ] `aws_instance.domain_service` checked for the same leftover; fixed too if present, or explicitly noted as unaffected.
- [ ] Drone and Jenkins both still healthy afterwards.
- [ ] `user_data` size re-measured and recorded if the template grew.

## Definition of done

PR open against `master` from `chore/remove-ecs-agent`, `terraform fmt`/`validate`/`test` green, reboot persistence demonstrated rather than assumed.
