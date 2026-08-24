---
id: T-005
title: Limit CI secret blast radius — block IMDS from containers, then split parameter paths
repo: cv-infra
status: todo
owner:
branch: feat/ci-secret-blast-radius
pr:
depends_on: [T-002]
risk: high
security_review: true
---

## Why this exists

Follow-up to the trust boundary accepted at T-002's human gate. That sign-off was:

> Anyone with push access to `cv-domain-service` or `cv-database` can reach root on the CI host and read every CI secret — including Drone's RPC secret and GitHub OAuth client secret, and vice versa.

Accepted as unavoidable *within T-002's scope*. This task narrows it.

## The naive fix does not work — read this before planning

The obvious idea is "split `ci/*` into `ci/drone/*` and `ci/jenkins/*`, give each system a policy scoped to its own prefix." **That achieves nothing on its own**, and it is worth being precise about why:

Drone and Jenkins run as containers on the **same EC2 instance**, which has **one** instance profile (`cv-project-drone`). IAM identity is attached to the instance, not the container. Both containers reach the same credentials through the instance metadata service, so both can read whatever that single role permits, no matter how the parameter paths are named. Splitting paths without splitting *identity* is documentation, not a control.

## What actually works: stop containers reaching IMDS at all

The credentials-theft path is a build step calling `169.254.169.254` to obtain the instance role. Neither instance currently sets `metadata_options` at all (verified — no `http_tokens`, no `http_put_response_hop_limit` in `compute.tf` or `ci.tf`), so IMDSv2 is not enforced and the hop limit is at provider/AWS default.

```hcl
metadata_options {
  http_endpoint               = "enabled"
  http_tokens                 = "required"   # IMDSv2 only — defeats SSRF-style token-less reads
  http_put_response_hop_limit = 1            # host can reach IMDS; a bridged container cannot
}
```

`http_put_response_hop_limit = 1` is the load-bearing part. A process on the host is one hop from IMDS; a process inside a bridge-networked container is one hop further, and the response TTL expires before it gets back. This is AWS's own documented way to keep containers off the instance role.

**Why this is safe for this box specifically — but must be verified, not assumed:** the provisioning script's `param()` calls run **on the host** via SSM Run Command, not inside a container, so they keep working. The containers get their secrets injected as `docker run -e` values by that host-side script; none of them calls the AWS API itself (verified — the only `aws ssm` invocation in `jenkins-provision.sh` is the host-side `param()` helper). If any container *does* turn out to need AWS access, the answer is a task-scoped role via a credential process, not re-widening the hop limit.

**Risk to check before applying:** the SSM agent, CloudWatch agent, and anything else host-side must still reach IMDS. They run on the host, so hop limit 1 is fine — but a hop limit that breaks the SSM agent would lock you out of the box's only shell access (there is deliberately no SSH ingress). Verify on a throwaway instance, or be ready with the EBS-snapshot rollback from T-002's runbook.

## Then, and only then, split the parameter paths

With IMDS closed to containers, path splitting becomes meaningful defence-in-depth for the *host-side* compromise case:

- `/cv-project/dev/ci/drone/*` — `drone-rpc-secret`, `github-client-id`, `github-client-secret`
- `/cv-project/dev/ci/jenkins/*` — `jenkins-admin-password`, `github-pat`

Renaming an `aws_ssm_parameter` is a destroy-and-recreate. Sequence it so the provisioning scripts' `param()` prefix changes in the same apply, or the boxes fetch a path that no longer exists. Consider `moved` blocks or a two-phase apply, and say which you chose.

## Also worth doing here

- ~~**A GitHub webhook secret.** The `/jenkins/github-webhook/` endpoint is unauthenticated today — anyone can trigger a branch re-scan. Not an exposure (builds still only run repo code, and fork PRs are excluded by T-002's pinned traits) but it is free noise-suppression and a cheap authenticity check.~~ **DONE ELSEWHERE — dropped from this task 2026-08-20.** [T-019](T-019-ci-host-on-demand.md)'s ruling 4 found this bullet, noted it had never been built, and **built it**: a `SecureString` SSM parameter, with the doorbell Lambda validating `X-Hub-Signature-256` by constant-time compare before it will start anything. T-019 said explicitly that *"T-005 should drop that bullet rather than build it twice"*, and nothing here recorded that until now. **Do not re-implement it**; if this task touches the secret at all it is only to fold it into the `/cv-project/dev/ci/*` naming scheme above.
- **Pin `jenkins/jenkins:lts-jdk17` to a digest** rather than a floating tag — raised as non-blocking in T-002's `/security-review`.
- **NOT here: TLS.** T-002's `/security-review` ended its scanning finding with *"carry to T-005 as an argument for scheduling TLS"*, and this task never absorbed it — TLS appears in none of the acceptance criteria below, so for eleven days it was handed here and held by nothing. **Filed 2026-08-24 as [T-033](T-033-ci-host-tls.md)** rather than widened into this task, per board rule 3: adding it here would have repeated the hand-off error instead of fixing it. The two tasks touch the same instance's network surface, so **sequence the applies if both are in flight** — but neither gates the other.

## Explicitly out of scope

Separating Drone and Jenkins onto different hosts — that is the only *complete* fix for shared identity, and it costs another instance, which contradicts T-002's whole rationale. If it is ever wanted it is its own task with its own cost decision. Removing the docker-socket mount is also out: both `Jenkinsfile`s require it.

## Acceptance criteria

- [ ] `metadata_options` with `http_tokens = "required"` and `http_put_response_hop_limit = 1` on **both** `aws_instance.drone` and `aws_instance.domain_service`.
- [ ] Verified: a container on the CI host **cannot** retrieve instance credentials (`curl` to `169.254.169.254` from inside a container times out or is refused), while the host-side `param()` path still works.
- [ ] Verified: SSM Session Manager still connects, and `null_resource.jenkins_provision`'s SSM path still runs. **This is the lock-yourself-out check — do it before trusting the change.**
- [ ] Drone and Jenkins pipelines both still go green after the change.
- [ ] Parameter paths split, with both provisioning scripts and the IAM policy updated in the same apply.
- [ ] `terraform test` gains assertions for the metadata options and the new policy resource ARNs.
- [ ] `/security-review` clean.
- [ ] T-002's recorded trust boundary is updated to describe what is *now* true.

## Definition of done

PR open against `master` from `feat/ci-secret-blast-radius`, `/security-review` clean, container-credential-denial demonstrated empirically rather than asserted, both CI systems verified still working.
