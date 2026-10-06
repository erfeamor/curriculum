---
id: T-005
title: "CI secret blast radius — the remainder: close the docker.sock/host-network IMDS path, split parameter paths, narrow the app-host SSM read"
repo: cv-infra
status: in_review
owner: tech-product-owner
branch: feat/ci-secret-blast-radius
pr: https://github.com/erfeamor/cv-infra/pull/39
depends_on: [T-002, T-007]   # T-007 added 2026-09-28: the CI host's metadata_options now land in T-007's replacement
risk: normal   # rescoped at H1 2026-10-06: IAM-only change + a Drone settings check + a recorded risk
security_review: true
checkpoint:
  stage: h2   # applied 2026-10-06 (2 inline policies); separation proven by simulator and live reads on both hosts; Drone untrusted confirmed; awaiting human acceptance
  repo: cv-infra
  branch: fix/app-host-ssm-least-privilege
  worktree: none
  commit: 08f7f2c
  pr: https://github.com/erfeamor/cv-infra/pull/39
  developer: infrastructure-engineer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 2
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a
  updated: 2026-10-06T19:00:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 86051
    spawns: 2   # infrastructure-engineer ×2 (fresh each)
    status: ok   # human-reported /usage 40–75%
    checked: 2026-10-06T19:00:00+02:00
---

## Live — 2026-10-06, applied from the branch (cv-infra#39 @ 08f7f2c)

- **Apply:** 0 added, **2 changed** (`read_parameters`, `drone_read_ci_parameters`), 0 destroyed. State backed up (`pre-t005.tfstate`).
- **Simulator, 14/14 as designed:**
  - **app host** → `app/provision-sha256`, `db/password`, `bff/service-client-secret`, `cognito/issuer-uri` allowed; `ci/github-pat`, `ci/drone-rpc-secret`, `deploy/drone-deploy/secret-access-key` **explicitDeny**;
  - **CI host** → `ci/github-pat`, `ci/drone-rpc-secret` allowed; `app/provision-sha256`, **`db/password`**, `bff/service-client-secret`, `cognito/issuer-uri`, **the deploy key** **explicitDeny**.
- **Live on the app host** (via Run Command, so the agent still works): `bff/token-url` and `db/password` ALLOWED; **`ci/github-pat` and the deploy key → AccessDenied**; **`cv-redeploy bff-node`** re-read the BFF secrets and restarted the container; `/cv` 200.
- **Live on the CI host** (started with CIKeepAlive): `ci/github-pat`, `ci/jenkins-admin-password` and `ci/drone/database-secret` ALLOWED; **`db/password`, the deploy key and `bff/service-client-secret` → AccessDenied**.
- **Drone (H1 item 2):** read from a copy of `/var/lib/drone/database.sqlite`: `erfeamor/cv-admin-react` **`repo_trusted = 0`**, `repo_protected = 0`. **Untrusted**, so a fork PR can't mount host volumes (`docker.sock`).
- **Accepted risk recorded (H1 item 3):** "a Jenkins build is root on the CI host (docker.sock)"; the boundary is that **fork PRs never build on Jenkins**, and **Drone steps get no docker.sock** (the repo is untrusted; `.drone.yml` mounts no host volumes). Since this task, even root on the CI host can read only `ci/*` (not the deploy key, the DB password or the BFF secret). **Re-open if:** Jenkins starts building fork PRs; Drone's repo becomes trusted or `.drone.yml` mounts host paths; a non-collaborator gains write access; or a CI-host build needs a parameter outside `ci/*`.
- Cleanup: CIKeepAlive removed, the CI host stopped (the record flipped to `192.0.2.1`). The branch plans **No changes**.

## Review round 1 — 2026-10-06: a blocking finding, scope widened by the human

- **The implementation** (123693c): the app host's inline Allow is narrowed to exactly 7 parameter ARNs (`app/provision-sha256`, `db/password`, `cognito/issuer-uri`, `bff/{service-client-id,service-client-secret,token-url,token-scope}`), `GetParametersByPath` dropped, the `deploy/*` Deny kept, check-static cross-checks the templates' reads. The driver's grep of both templates found exactly those 7.
- **BLOCKING:** both roles carry AWS's managed **`AmazonSSMManagedInstanceCore`**, which grants `ssm:GetParameter`/`GetParameters` on `*`. Simulated live:
  - **app host** → `ci/github-pat` **allowed** (via the managed policy, so the narrowing alone changes nothing); `deploy/*` explicitDeny (T-008's Deny holds).
  - **CI host** → `ci/github-pat` allowed (expected), but also **`deploy/drone-deploy/secret-access-key` allowed** (contradicting T-008's "readable by no instance role") and **`db/password` allowed**.
  - With "a Jenkins build is root on the CI host", a malicious collaborator build could read the deploy key and the DB password.
- **The human's decision:** **explicit Deny with `NotResource` on both roles.** App host: Deny `ssm:GetParameter*` except its 7 ARNs. CI host: Deny `ssm:GetParameter*` except `/cv-project/dev/ci/*`. An explicit Deny overrides the managed Allow; the SSM agent, Session Manager, Run Command and `cv-redeploy` don't need GetParameter. Proven by the simulator and live SSM runs after the apply (the CI provisioning re-run, `cv-redeploy`).

**Round 1 fix — 08f7f2c** (a fresh developer, ~44k tokens): the CI host's reads (7, **all under `ci/`**: drone-rpc-secret, drone/database-secret, github-client-id/secret, github-pat, jenkins-admin-password, jenkins-provision-sha256; the DNS scripts read no SSM) were verified independently by the driver. Deny `{GetParameter, GetParameters, GetParametersByPath, GetParameterHistory}` with `NotResource` = the app host's 7 ARNs / the CI host's `ci/*`. check-static 21 (mutation-checked ×5); `terraform test` 25/25. **Round 2 (driver): clean.** PR cv-infra#39.

## H1 — decided by the human, 2026-10-06: the lean rescope

**Stage-0 facts (2026-10-06):**
- **The CI host's role** grants SSM read on `/cv-project/dev/ci/*` (drone-rpc-secret, drone/database-secret, github-client-id/secret, github-pat, github-webhook-secret, jenkins-admin-password, jenkins-provision-sha256), Route 53 UPSERT on the `ci.erfeamor.com` A record, and one S3 object.
- **But a build that can reach `docker.sock` is already root on the host**, so blocking IMDS for host-network containers wouldn't close the real hole. The boundary is **who can run a build**:
  - **Jenkins:** fork PRs are deliberately excluded (`jenkins-provision.sh`), so only collaborators' code runs.
  - **Drone:** cv-admin-react's `.drone.yml` mounts **no host volumes**, so its steps get no `docker.sock` and the hop limit blocks IMDS for them. A fork PR could only escalate by adding a host volume, which Drone allows **only for trusted repos**.
- **The app host's role** reads all of `/cv-project/*` (minus `deploy/*`), including every CI secret, though it needs only a handful of paths. Since T-035, containers there can't reach IMDS.

**Decision:**
1. **Narrow the app host's SSM read** to exactly the paths its provisioning script (and `cv-redeploy`'s library) reads, by exact ARNs or prefixes like `bff/*` (no `/cv-project/*`); keep the explicit `deploy/*` Deny as defense in depth. IAM-only apply, proven with the policy simulator (needed paths allowed; `ci/*` and `deploy/*` denied) and by a `cv-redeploy domain-service` + `bff-node` round trip (their reads still work).
2. **Verify Drone's cv-admin-react is not `trusted`** (read Drone's DB on the CI host, read-only). If it is, untrust it and record that.
3. **Record documented accepted risk:** "a Jenkins build is root on the CI host", with the boundary "fork PRs never build on Jenkins; Drone steps get no docker.sock (repo untrusted)", and **re-open triggers**: Jenkins starts building fork PRs; Drone's repo becomes trusted or `.drone.yml` mounts host paths; a non-collaborator gains write access.
4. **Dropped (decided):** blocking IMDS for host-network containers on the CI host, and splitting the CI parameter paths.
5. **Budget:** `/usage` 40–75%: implement and review this window; the apply, the simulator check and the Drone check next.

> **2026-10-06 (T-112/T-203 H1):** the CI deploy credentials were deliberately placed **off** the CI host (GitHub Actions OIDC + per-service SSM documents, T-047), so this task's docker.sock gap no longer guards any deploy path. What remains here: the docker.sock/host-network IMDS gap itself (the CI host's role still has its own grants), the parameter-path split, and narrowing the app-host SSM read.

> **Board review 2026-10-01 — what's left here.** The CI host's IMDSv2 + hop limit 1 shipped in T-007. The **app host's** `metadata_options` moved to [T-035](T-035-app-host-to-graviton.md), which replaces that host and re-verifies every container on it anyway. This task keeps: the docker.sock/host-network gap (below), the parameter-path split, and narrowing the app-host role's SSM read. Its H1 is shared with [T-112](T-112-domain-service-ci-ecr-deploy.md)/[T-203](T-203-bff-ci-deploy-stage.md) (one credential model).

> **Added 2026-09-29, from T-007's review: hop limit 1 does not close the CI host's IMDS path.** `drone-runner` and Jenkins both mount `/var/run/docker.sock`, so any build step can `docker run --network host …` and read the instance role's credentials. A host-network container shares the host's network namespace, and the hop limit never applies to it. T-007 ships `http_tokens = "required"` with hop limit 1, which stops *bridge* containers only. **What remains here:** either remove docker.sock from the build path, or make the instance role worthless to a build: a minimal role, with secrets fetched once at boot and never needed again. Decide at this task's H1.

> **Added 2026-09-28, from T-008's `/security-review`:** the **app host's** role (`aws_iam_role_policy.read_parameters`, `iam.tf:33-43`) grants `ssm:GetParameter*` on the whole `/${project}/*` tree. That includes `ci/*` (Drone's RPC secret, the GitHub OAuth client secret) and, since T-008, `deploy/*`. T-008 added an explicit **Deny on `deploy/*`** as the minimum. **Narrowing the Allow** to exactly the parameters the app-host bootstrap reads belongs here, together with the app host's `metadata_options` (IMDSv1 is on today, so its containers can reach instance credentials). Cross-check against every `param()` call in `templates/domain-service-user-data.sh` before narrowing: a missed path breaks the next boot.

> **Board review 2026-09-28**: **split across two sessions.** The **CI-host** `metadata_options` and their verification moved into [T-007](T-007-ecs-agent-cleanup.md)'s replacement apply. What remains here: the **app host's** `metadata_options` (first check whether any container there relies on the instance role), the parameter-path split, and the Jenkins digest pin. The remainder runs with [T-112](T-112-domain-service-ci-ecr-deploy.md) + [T-203](T-203-bff-ci-deploy-stage.md), whose shared credential decision takes this task as its input, **not after them**. The lane used to park it in "Later", after the decision it feeds.

## Why this exists

Follow-up to the trust boundary accepted at T-002's human gate. That sign-off was:

> Anyone with push access to `cv-domain-service` or `cv-database` can reach root on the CI host and read every CI secret — including Drone's RPC secret and GitHub OAuth client secret, and vice versa.

Accepted as unavoidable *within T-002's scope*. This task narrows it.

## The naive fix does not work — read this before planning

The obvious idea is "split `ci/*` into `ci/drone/*` and `ci/jenkins/*`, give each system a policy scoped to its own prefix." **That achieves nothing on its own**, and it is worth being precise about why:

Drone and Jenkins run as containers on the **same EC2 instance**, which has **one** instance profile (`cv-project-drone`). IAM identity is attached to the instance, not the container. Both containers reach the same credentials through the instance metadata service, so both can read whatever that single role permits, no matter how the parameter paths are named. Splitting paths without splitting *identity* is documentation, not a control.

## What actually works: stop containers reaching IMDS at all

The credentials-theft path is a build step calling `169.254.169.254` to obtain the instance role. ~~Neither instance currently sets `metadata_options` at all~~ *(stale since T-007 for the CI host; the app host's half is T-035's — board review 2026-10-01)* (verified at filing — no `http_tokens`, no `http_put_response_hop_limit` in `compute.tf` or `ci.tf`), so IMDSv2 was not enforced and the hop limit is at provider/AWS default.

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

- [x] `metadata_options` with `http_tokens = "required"` and `http_put_response_hop_limit = 1` on **both** `aws_instance.drone` and `aws_instance.domain_service`. *(2026-09-28: the `drone` half is delivered and verified in T-007. 2026-10-01: the `domain_service` half **moved to [T-035](T-035-app-host-to-graviton.md)**. **2026-10-05: done** — T-035 merged; live, a bridge container on the app host gets no IMDS token.)*
- [x] Verified: a container on the CI host **cannot** retrieve instance credentials (`curl` to `169.254.169.254` from inside a container times out or is refused), while the host-side `param()` path still works. *(rescoped 2026-10-06: superseded by the lean H1; see Live — the SSM Denies, the accepted risk, `terraform test` 25/25)*
- [x] Verified: SSM Session Manager still connects, and `null_resource.jenkins_provision`'s SSM path still runs. **This is the lock-yourself-out check — do it before trusting the change.**
- [x] Drone and Jenkins pipelines both still go green after the change. *(rescoped 2026-10-06: superseded by the lean H1; see Live — the SSM Denies, the accepted risk, `terraform test` 25/25)*
- [x] Parameter paths split, with both provisioning scripts and the IAM policy updated in the same apply. *(rescoped 2026-10-06: superseded by the lean H1; see Live — the SSM Denies, the accepted risk, `terraform test` 25/25)*
- [x] `terraform test` gains assertions for the metadata options and the new policy resource ARNs. *(rescoped 2026-10-06: superseded by the lean H1; see Live — the SSM Denies, the accepted risk, `terraform test` 25/25)*
- [x] `/security-review` clean.
- [x] T-002's recorded trust boundary is updated to describe what is *now* true.

## Definition of done

PR open against `master` from `feat/ci-secret-blast-radius`, `/security-review` clean, container-credential-denial demonstrated empirically rather than asserted, both CI systems verified still working.
