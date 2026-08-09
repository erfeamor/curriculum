---
id: T-002
title: Host Jenkins on the existing Drone CI instance
repo: cv-infra
status: done
owner: infrastructure-engineer
branch: feat/jenkins-on-ci-host
pr: https://github.com/erfeamor/cv-infra/pull/11
depends_on: []
risk: high
security_review: required
checkpoint:
  stage: pr
  repo: cv-infra
  branch: feat/jenkins-on-ci-host
  a1: pass   # fmt/validate/test green; no new drone-SG ingress; compute.tf+iam.tf untouched; no tfstate/tfvars/secrets tracked
  a1_caveat: resolved   # was: "no real terraform plan — worktree has no state". Gate run 2026-08-08 from the main clone (where the local-backend tfstate + tfvars live); see pre_apply_gate below.
  worktree: none   # REMOVED 2026-08-09 (was /home/erfeamor/work/cvdl-worktrees/T-002; clean, detached, nothing unique). Do not recreate one for cv-infra.
  worktree_rationale: "cv-infra cannot be worked from a worktree while the backend is local: providers.tf has the S3 backend commented out, so terraform.tfstate AND terraform.tfvars exist only in the main clone and are both gitignored. A worktree gets the .tf files and nothing else — it can never run plan/apply, which is exactly what a1_caveat recorded for three review rounds. Copying state in would give two local state files with no locking (the failure mode T-004 exists to fix). Worktrees remain correct for T-101..T-104 (cv-domain-service) and T-151 (cv-database), which have no shared singleton. Revisit only after T-004 moves state to S3 with locking — and then create a fresh one."
  pr: https://github.com/erfeamor/cv-infra/pull/11
  commit: 25dfff7
  signed_off: "trust boundary accepted 2026-08-06, conditional on trait pinning (done)"
  developer: infrastructure-engineer
  reviewers: [code-review, infrastructure-engineer, quality-assurance, security-review]
  risk: high
  security_review: true
  review_round: 3
  open_findings: 0
  review_status: CONVERGED
  review_trail: "R1 on a155c52: 6 blocking (JENKINS_HOME ownership, JCasC abort into Unsecured, 100s SSM waiter, no SSM-agent wait, no docker CLI, JENKINS_HOME path mismatch) → fixed in b28d327. R2: /security-review converged 0 blocking (fail-closed restored via init.groovy.d, verified to run after JOB_LOADED and before InitMilestone.COMPLETED); correctness found 3 blocking → fixed in 929a51f. R3 verified by the driver: A1 green; nginx proxy_pass has no URI part; Maven archive URLs both HTTP 200 with sha512 check; PAT credential restored to usernamePassword; all six ${...} occurrences are intended tf vars, no escaping bugs; user_data 14,017 B = 85.6% of limit."
  po_note: "The round-2 PAT-credential blocker was caused by the driver: round 1's non-blocking finding 12 was wrong and was promoted into scope anyway. a155c52's original usernamePassword/x-access-token form was correct and has been restored. Lesson: do not promote a reviewer's non-blocking finding without independently checking the claim it rests on."
  review_note: "Round 1 first attempt (2026-08-04) was interrupted by user request before any pass produced findings. Re-spawned in full 2026-08-06 against the same commit a155c52 — worktree verified clean and unchanged. Not a second round: the first produced nothing to build on."
  qa_bounces: 0
  fix_attempts: 0
  env_slot: 5
  pre_apply_gate:
    run: 2026-08-08
    commit: 546c580
    plan: "Plan: 4 to add, 2 to change, 0 to destroy"
    steps_1_4: pass   # domain_service refresh-only; eip_association refresh-only; drone ~ in-place (t3.micro→t3.small, user_data hash); zero 'must be replaced' anywhere
    steps_5_6: pass   # 2026-08-08: no build in flight (0 pending/0 running, 27 success + 4 failure); cv-admin-react is the only active repo; EBS snapshot snap-0d7f5ae272ce0cef5 completed
    blocker_found: "aws_security_group.drone planned for replacement — description is ForceNew, no create_before_destroy, referenced by aws_instance.drone.vpc_security_group_ids ⇒ DependencyViolation mid-apply. Reverted in 546c580."
    drone_state_location: "/var/lib/drone bind-mounted to /data (NOT a docker volume — `docker volume ls` is empty). Single 1.35 MB database.sqlite holding the activated-repo list AND the drone-deploy aws_access_key_id/aws_secret_access_key, which exist nowhere else — not in SSM, not reconstructable without re-issuing an IAM key. Verified jenkins-provision.sh:291 re-specifies the bind mount on the drone-server recreate, and that the live container's extra DRONE_DATABASE_* vars are drone/drone:2 image ENV defaults rather than runtime overrides, so the recreate cannot silently open a new empty DB."
    ebs_snapshot: snap-0d7f5ae272ce0cef5   # 30 GiB from vol-0c82f0d4725b608c2, unencrypted (the volume is), tagged Task=T-002
    ebs_snapshot_decision: "RETAINED deliberately 2026-08-09 — do NOT delete as routine post-verification cleanup. It is the ONLY snapshot of vol-0c82f0d4725b608c2, and that volume holds the sole copy of Drone's drone-deploy aws_access_key_id/aws_secret_access_key (see drone_state_location). Deleting it would leave that credential with zero backups. Release it only once T-008 has put a real backup in place; that is T-008's first acceptance criterion. Cost of holding: ~$0.40-0.50/mo."
    incidental_finding_confirmed: "T-007 confirmed empirically by the reboot test: ecs-agent was Exited (1) 1 second after boot, proving it is started by the AMI's systemd unit and that removing the container alone would never hold. Original note: ecs-agent container is crash-looping on the CI host (Exited (1), continuous restart) — pre-existing ECS-optimized-AMI leftover, unrelated to T-002, deliberately out of scope. Burns RAM on the box being resized for RAM pressure; worth its own cleanup task."
    evidence: "steps 1-4: https://github.com/erfeamor/cv-infra/pull/11#issuecomment-5225135292 | steps 5-6: https://github.com/erfeamor/cv-infra/pull/11#issuecomment-5225415994"
  apply:
    run: 2026-08-08
    commit: edd9aae
    result: converged   # 2nd attempt; `terraform plan` after it: "No changes. Your infrastructure matches the configuration."
    first_attempt: failed   # jenkins-provision health probe: "/jenkins/login never came up through ci-proxy within 120s"
    defects_found: "(1) Jenkins could not boot AT ALL: plugins.txt pins no versions, so the provision pulled a github-branch-source whose GitHubSCMSource ctor requires repositoryUrl + configuredByUrl; Job DSL rejected the script, which aborts the ENTIRE JCasC document → BootFailure, 14 container restarts, proxy 502. (2) Only visible once (1) was fixed: no unclassified.location.url, so Jenkins' root URL was empty → github-branch-source has no target URL for the commit status it posts, and GHHook registration was skipped. Both fixed in edd9aae."
    method: "Each fix was applied to /var/lib/jenkins-casc/jenkins.yaml on the live box and Jenkins restarted alone (Drone untouched) BEFORE committing and re-applying — a Drone outage was not spent on an unverified fix. Final host state is the template render, not the hand-patch: the provision rewrote the file and recreated the container on the changed config hash, so what is proven working is what is committed."
    live_state: "jenkins restarts=0, /jenkins/login 200 through the proxy; drone-server 303; ci-proxy + drone-runner up; 0 SEVERE/DslScriptException/BootFailure since boot; jobs cv-domain-service + cv-database created; aws_instance.drone = t3.small"
    root_cause_note: "THIRD JCasC-abort defect on this task (after adoptOpenJdkInstaller in R1). Common cause: plugins.txt pins nothing, so the JCasC/Job DSL contract moves under us and fails only at runtime, invisible to terraform validate/test. Plugin pinning is non-blocking in T-005 and should be promoted."
    user_data_bytes: 15460   # 94.4% of the 16 KB limit, 924 B headroom (was 91.1% pre-fix; the board's earlier 85.6% was stale)
    ssm_timeout_note: "null_resource reported 5h37m44s because the LOCAL machine suspended mid-poll; the SSM invocation itself was PT30.007S. The script's 1800s timeout counts loop iterations, not wall clock, so it cannot bound a real run."
    evidence: https://github.com/erfeamor/cv-infra/pull/11#issuecomment-5226866019
  post_apply:
    status: pass   # 2026-08-08 — the acceptance criterion is MET
    proof: |
      cv-domain-service PR #3  continuous-integration/jenkins/pr-merge  success  total_count=1
      cv-database       master continuous-integration/jenkins/branch    success  total_count=1
      gh pr checks 3 => pass; target_url http://13.39.59.12/jenkins/job/cv-domain-service/job/PR-3/2/display/redirect
      (pre-fix builds emitted http://unconfigured-jenkins-location/... — confirms the edd9aae location fix landed)
    webhooks: "created manually 2026-08-08 on both repos (push + pull_request, json); both pings 200 and logged by Jenkins as 'PING webhook received from repo'"
    defects_found: "Every one of the first 7 builds failed, two unrelated causes, both fixed in 25dfff7 and verified by real green builds before committing. (1) 'No such DSL method junit' — the junit plugin was absent from plugins.txt and workflow-aggregator does not pull it in. (2) 'docker: not found' exit 127 — jenkins/jenkins:lts-jdk17 now rebases on Debian 13, where docker.io only *Recommends* docker-cli, so --no-install-recommends yielded an image with no /usr/bin/docker while the image build reported success. R1 had raised 'no docker CLI' and it LOOKED fixed. Now installs docker-cli, which is also correct: only the client is wanted, the daemon is the host's via the socket."
    probe_choice: "Rebuilt the EXISTING cv-domain-service PR #3 rather than opening a throwaway probe PR — it is T-101's PR, it was blocked on exactly this, so the verification produced a useful green check instead of litter."
    checks_passed: "commit status on both repos; Jenkins anonymous posture 403 on /jenkins/, /jenkins/api/json, /jenkins/manage with no job data leaked; raw :8080 and :50000 refused from the internet; Drone OAuth /login 303 to github.com/login/oauth/authorize with correct client_id/state/scopes; Drone survived all three applies; terraform plan converged"
    reboot_test: "PASS 2026-08-08. Real aws ec2 reboot-instances; box genuinely rebooted (uptime 1 min, docker unit enabled at boot) and everything back in ~62s. All four containers incl. ci-proxy — the one this task added to own host :80, whose absence would leave the box serving nothing. Persistence held: Jenkins' 2 jobs + all 9 builds, Drone's cv-admin-react activation, and the drone-deploy AWS secrets that exist ONLY in /var/lib/drone/database.sqlite. Jenkins 200 / Drone 303, 0 boot errors, docker CLI still present. Idle mem after: 769/1913 MB used."
    jenkins_login: "CONFIRMED by the repo owner in a browser using the admin credential from terraform.tfvars — exercises the JCasC securityRealm and the SSM-sourced password end to end. NOTE this is Jenkins' own login, NOT the Drone OAuth callback; do not conflate them."
    oauth_callback: "VERIFIED 2026-08-08 17:07 UTC. Proxy log carries the full round trip: GET /login -> 303 out to GitHub, then GET /login?code=2517f14d...&state=dee6be45... -> 303 back, session established; owner confirmed landing in Drone as their GitHub user. Proves two things that were live risks when Drone moved off host :80 onto the internal network: the proxy does not mangle query strings (so the OAuth state check passes), and the EIP-based DRONE_SERVER_HOST still matches the registered callback URL after two stop/starts and a reboot."
    still_open: "NOTHING — every post-apply item passes. Unmeasured but explicitly not a gate: memory during a real Maven build concurrent with a Drone pipeline (769/1913 MB at idle post-reboot)."
    scanning_note: "The proxy log shows the CI host under steady untargeted internet scanning — of 1,161 lines, most traffic is not ours (117 req from 20.113.142.140, 98 from 20.218.73.95, 85 from 64.23.252.42, plus raw TLS ClientHello sent to plain-HTTP :80 and probes for /geoserver/web/). Verified nothing is reachable: Jenkins 403 to anonymous on every path, :8080/:50000 refused, Drone gated by OAuth + DRONE_USER_FILTER; the 200 on /geoserver/web/ is Drone's SPA catch-all, not a leak. Not a finding against this PR, but it is the environment the accepted trust boundary sits in — carry to T-005 as an argument for scheduling TLS."
    reconciliation_apply: "3rd apply, from the COMMITTED template rather than the hand-patched box: rewrote plugins.txt + Dockerfile from source, rebuilt, and reproduced the hand-verified state exactly (docker 26.1.5 present, junit installed, restarts=0, 0 boot errors, both jobs). terraform plan after: No changes. This is what proves the branch as committed reproduces the working state."
    evidence: https://github.com/erfeamor/cv-infra/pull/11#issuecomment-5227099959
  merged: "cv-infra PR #11 merged 2026-08-09T06:47:58Z as b30c20c"
  budget_premise_corrected: "The H1 'Free Tier exception, net +$8/mo' framing in this file is WRONG and is left in place only as a record of what was decided. This account (created 2026-07-12) is on AWS's post-July-2025 Free Tier — credits + a 6-month window, no 750h/month EC2 allowance. Verified: aws freetier get-free-tier-usage returns only Always Free entries (Glue/SQS/KMS), no 12-Month-Free rows. So there was no allowance to make an exception TO, and every instance-hour bills. Real run rate is ~$0.92/day ~= $28/mo (not the ~$16.60 projected), fully covered by credits — July usage $22.90/credit -$22.90, August $16.06/credit -$16.06, net $0 both months, which is why no billing warning ever fired. The t3.small DECISION stands and was correct; only its justification was mis-framed. Real constraint is credit runway + the 6-month cliff: T-010."
  followups_warranted:
    user_data_ceiling: "95.7% of the 16 KB limit (15,681 B, 703 B headroom). THREE consecutive fixes each needed comment-trimming to fit. Shaving comments is not a strategy — the real fix is staging the provisioning script in S3 and fetching it at boot instead of embedding it. Deserves its own task; the next person to touch either template will likely be the one who blows the limit."
    pin_everything: "Nothing is pinned — not plugins (plugins.txt has no versions), not the base image (jenkins/jenkins:lts-jdk17 is a floating tag). This caused THREE of the five defects on this task: adoptOpenJdkInstaller (R1), repositoryUrl/configuredByUrl and missing junit (apply time). The Debian 13 rebase that removed the docker CLI is the same class one layer down. T-005 carries pinning as non-blocking — PROMOTE IT."
  gate_note: "Gate checks 1–4 as originally written only grepped the two instances and the EIP association, so the security-group replacement passed straight through them. Check 1 is now a whole-plan grep for 'must be replaced'/'forces replacement' with zero expected hits — carry that phrasing to future infra gates."
  updated: 2026-08-08
---

## Why this exists

`cv-domain-service` and `cv-database` both carry a `Jenkinsfile`, and both the adapter and `docs/architecture.md` name **Jenkins as their authoritative CI** — but **Jenkins has never been provisioned**. `cv-infra/ci.tf` contains only three resources, all Drone (`aws_eip.drone`, `aws_instance.drone`, `aws_eip_association.drone`); no `.tf` file and no doc mentions Jenkins anywhere.

Consequence, observed on **T-101's PR #3**: `gh pr checks` reports "no checks reported", the combined commit status is `pending` with `total_count: 0`, and `cv-domain-service` has **zero webhooks**. The pipeline's stage-3 exit condition — green authoritative CI before merge — is unsatisfiable for these two repos. Every remaining backend task (T-102, T-103, T-104, T-151) hits the same wall.

## Decision (chosen 2026-08-04)

**Co-locate Jenkins on the existing Drone host**, rather than adding a third EC2 instance.

Rationale: no new instance and no new EIP; reuses a box that is already provisioned, already internet-reachable, and already integrated with GitHub. Rejected alternatives, for the record:
- *A dedicated Jenkins instance* — a third t3.micro roughly doubles the current overage (see budget below) for a box that idles most of the day.
- *Ephemeral EC2 build agents* — correct at scale, pay-per-build-minute, but needs an AMI with JDK 17 + Maven plus meaningful IAM and Terraform work. Disproportionate for a demo.
- *Moving these repos to GitHub Actions* — **explicitly rejected.** Different CI per repo is a deliberate feature of this demo, not drift to normalize.

## H1 ratified decisions (2026-08-04) — these are binding

1. **Provisioning: out-of-band via SSM.** SSM Run Command / `remote-exec` over SSM against the live instance. `user_data` and `aws_instance.drone`'s lifecycle stay untouched, so Drone's SQLite state is never wiped and no replacement occurs. **Must be idempotent** — name-guarded containers, safe to re-run.
   - **Consequence to handle, not ignore:** the box is now only partially reproducible from Terraform — a future instance replacement would come back without Jenkins. Mitigate by *also* adding the Jenkins provisioning to `user_data` for future boots **without** `user_data_replace_on_change`, so a fresh instance self-provisions while the live one is handled out-of-band. Document the split explicitly.
2. **Sizing: `t3.small`.** Set `var.drone_instance_type = "t3.small"`. In-place update (stop → modify → start), so no new instance id, EIP and EBS survive — **but Drone is down for the cycle.** Say so in the PR.
3. **Ingress: reverse proxy on the existing 80/443.** No new SG rule, no new internet-facing port.
   - **This is the fiddliest part:** port 80 is currently bound directly by `docker run -p 80:80 drone-server`. The proxy must take 80, and Drone must move to an internal port. `DRONE_SERVER_HOST` stays the EIP so the OAuth callback URL is unchanged — but the proxy must not mangle `Host` or the path prefix, or Drone's login breaks. Re-test the full OAuth flow (`/login` → GitHub → callback), not just that the UI loads.
   - The raw Jenkins port must **not** be reachable from the internet — QA probes for exactly this.
4. **Free Tier exception: GRANTED**, with the actual monthly cost recorded in the docs (via T-003). Net delta ≈ **+$8/mo** (~$16.60 vs ~$8.30). This supersedes the workspace's standing "AWS resources stay within Free Tier" rule **for this resource only** — it is not a general licence.

## Budget reality — read before sizing

AWS Free Tier grants **750 h/month** of t2.micro/t3.micro: one instance running 24/7. This account already runs **two** (`domain_service` + `drone`) ≈ 1460 h/month, so ~710 h is **already billable** — roughly **$8/month** in eu-west-3 at t3.micro rates.

**t3.micro (1 GB) cannot host Jenkins plus Maven.** A Jenkins controller alone wants ~1 GB before surefire forks a JVM for the Spring Boot suite. The existing Drone runner is already pinned `DRONE_RUNNER_CAPACITY=1` for this exact reason, and Jenkins would now be sharing that RAM.

Sizing decision required at H1 — pick one and record it:
- **t3.small (2 GB)** ≈ $16.60/mo, i.e. **net +$8/mo** over today. Real headroom for Maven. *Recommended.*
- **Stay t3.micro + 2 GB swap + capped `-Xmx`.** No cost change, but slow and OOM-prone. Acceptable only if the goal is to *demonstrate* Jenkins rather than run it hard.

Either way this **exceeds Free Tier**, which contradicts the workspace's standing "AWS resources stay within Free Tier" rule. That rule needs an explicit, recorded exception before apply — it is not the implementer's call to make silently.

## Scope

1. **`cv-infra/ci.tf`** — Jenkins container on the existing `aws_instance.drone`, with a persistent volume for `JENKINS_HOME` so config and job history survive a reboot. Set `var.drone_instance_type` per the H1 sizing decision.
2. **`cv-infra/templates/drone-user-data.sh`** (or a sibling template) — provision the Jenkins container alongside the existing Drone server/runner containers, reading secrets from SSM exactly as Drone already does (`param <name>`), never from literals or tfvars committed to git.
3. **`cv-infra/ssm.tf`** — a new SSM parameter for the **GitHub PAT** Jenkins uses to post commit statuses, following the existing `/${project_name}/${environment}/ci/...` naming. Mark `sensitive`, mirroring `drone_rpc_secret`.
4. **`cv-infra/network.tf`** — ingress for the Jenkins port on `aws_security_group.drone`. The SG currently opens **80 and 443 to `0.0.0.0/0`** and deliberately has **no SSH ingress** (shell access is SSM Session Manager). Preserve that posture — see the security constraints below.
5. **GitHub wiring** — webhooks on `cv-domain-service` and `cv-database` pointing at the Jenkins endpoint, matching the working Drone pattern (`cv-admin-react` → `http://13.39.59.12/hook`, events `push` + `pull_request`).
6. **Jobs** — a multibranch pipeline per repo so PR branches build and report, with JDK 17 and Maven tool definitions matching what the `Jenkinsfile`s already declare (`jdk 'jdk17'`, `maven 'maven3'`).
**Split out at refinement:** correcting `docs/architecture.md` and the adapter's CI table lives in the meta repo, so it is **T-003** (`depends_on: [T-002]`) — document what was actually built, not what was planned. This task touches `cv-infra` only.

## Security constraints (this task forces `/security-review`)

It touches IAM, network ingress, secrets, and CI config simultaneously — four of the adapter's forced-review paths at once.

- **Do not expose Jenkins on `0.0.0.0/0` port 8080.** Prefer a reverse proxy on the existing 80/443 under a path, or restrict the new port to GitHub's published webhook CIDRs. An unauthenticated internet-facing Jenkins is a remote-code-execution surface, not a misconfiguration.
- **Preserve the no-SSH-ingress posture.** Shell access stays on SSM Session Manager.
- **Enable Jenkins security on first boot** — an admin user from SSM, never the setup wizard's default unauthenticated state, and never a password in user-data or tfvars.
- The GitHub PAT must be **least-privilege** (commit status only; `repo:status`, not full `repo` if the repos are public) and stored in SSM as a `SecureString`.
- Jenkins builds run Docker; confirm what the Drone host's IAM instance profile grants, since Jenkins would inherit it. Widening that profile for image pushes needs justification in the review.

## Acceptance criteria

- [ ] `terraform fmt -check -recursive` and `terraform validate` pass.
- [ ] `terraform plan` shows no destroy/recreate of `aws_instance.domain_service` and does not drop the Drone EIP association.
- [ ] Jenkins reachable and **authenticated** — an anonymous request to the UI does not reach a usable Jenkins.
- [ ] Jenkins survives an instance reboot with jobs and credentials intact (persistent `JENKINS_HOME`).
- [ ] Drone still works: `cv-admin-react`'s existing pipeline runs green after the change.
- [ ] A PR opened against `cv-domain-service` triggers a Jenkins build **and posts a commit status visible in `gh pr checks`**. This is the acceptance test that matters — a Jenkins that builds but does not report back does not unblock the pipeline.
- [ ] Same verified for `cv-database`.
- [ ] `/security-review` run and clean, with the ingress decision explicitly justified.
- [ ] The Free Tier exception is recorded with its monthly cost (docs correction itself is **T-003**).

## Explicitly out of scope

TLS/ACM in front of Jenkins (the SG already anticipates 443 but Drone runs `DRONE_SERVER_PROTO=http` today — a separate task); migrating any repo off its current CI; changing the `Jenkinsfile`s themselves beyond what tool definitions require.

## Verification plan (QA-authored at refinement; QA executes it at stage 4)

### 0. THE BLOCKING RISK — how does Jenkins actually get installed?

`aws_instance.drone` has **no `user_data_replace_on_change = true`** and its `lifecycle.ignore_changes` covers only `ami`. `compute.tf`'s own comment records that this exact bug "shipped once": editing `user_data` without that flag **updates Terraform state only — the running instance never re-executes cloud-init, so Jenkins silently never installs**. A plain `apply` looks successful and delivers nothing.

The PR must take one path *deliberately*, and say so:

- **(a) `user_data_replace_on_change = true`** → `terraform plan` shows `aws_instance.drone` `# forces replacement`. This **destroys and recreates the box**, wiping Drone's SQLite state at `/var/lib/drone` (bind-mounted to local disk, no persistent volume). The manual "activate cv-admin-react in the Drone UI" step documented in `ci.tf`'s header **must be redone**. Needs a rollback/re-activation runbook.
- **(b) Out-of-band provisioning** against the live instance (SSM Run Command, or `null_resource` + `remote-exec` over SSM), leaving `user_data` and the instance lifecycle untouched. **Safer; preferred.** Must be idempotent — re-running must not duplicate containers.

**If `plan` shows `user_data` changed, `aws_instance.drone` not marked for replacement, and no out-of-band mechanism exists → blocking defect. Jenkins will never boot.**

### 1. Static gates
`terraform fmt -check -recursive` · `terraform validate` · `terraform test` (offline, `tests/plan.tftest.hcl` via `mock_provider`). A Jenkins-shaped diff adding **zero** new test assertions is a coverage gap — flag at review.

Read the `plan` **text**, not just the exit code:
- `aws_instance.domain_service` — no changes. Any update or replacement is a failure; this task has no business touching that box.
- `aws_eip_association.drone` — must not be destroyed/recreated.
- `aws_instance.drone` — `instance_type` is **not** a ForceNew attribute: a `t3.micro → t3.small` change is an **in-place update**, which AWS implements as **stop → modify → start**. No new instance id, no EIP re-association, EBS root volume (and `/var/lib/drone`) survives — but there **is** a real Drone outage window. Confirm no `replacement` marker from `instance_type` alone, and check separately whether another attribute forces replacement anyway (§0).
- No new `0.0.0.0/0` rule on a bare 8080.

### 2. Idempotency
`apply` → `plan` shows "No changes." → `apply` again is a genuine no-op. If provisioning runs via a script rather than Terraform, **re-run the script directly** — a `docker run` without a name guard fails on "container name already in use" even when Terraform reports no changes.

### 3. Security verification (highest priority)

**a. Jenkins must not be anonymously usable.** Probe the public path *and* the raw port:
- **PASS** — `403` with a Jenkins body / `X-Jenkins` header, or `302` to `/login`.
- **FAIL, setup wizard exposed** — `200` containing "Unlock Jenkins". Worse than unsecured-yet: the unlock secret is readable from the host and this is a known RCE path.
- **FAIL, anonymous read** — `200` serving the dashboard.
- Distinguish `403` (reachable, correctly locked) from connection-refused (nothing listening / port correctly unexposed). Confirm the raw `:8080` probe **refuses**, proving Jenkins isn't dual-exposed alongside the proxied path. Check `X-Jenkins` to be sure you're hitting Jenkins, not nginx's default page or Drone.

**b. No-SSH posture** — resulting SG has no port 22; any new Jenkins port is either folded into the existing 80/443 via proxy path routing, or restricted to GitHub's webhook CIDRs (`api.github.com/meta` → `hooks`). A bare `0.0.0.0/0:8080` is a **blocking finding**. `terraform test` should gain an assertion mirroring the existing `!contains(..., 22)` check.

**c. No secret leakage** — `terraform.tfstate`/`.backup` are present in the working tree but **correctly gitignored and untracked today**; re-verify no `git add -f` slip. New PAT must be fetched via the existing `param()` SSM pattern — grep the templates for literal secrets. `terraform.tfvars` (real, not `.example`) must not exist on the branch.

**d. PAT least-privilege** — `SecureString` in SSM, mirroring `drone_rpc_secret`. Scopes limited to `repo:status` (classic) or fine-grained "Commit statuses: read/write" on those two repos only. Bare `repo` is a **blocking finding**.

**e. IAM inheritance** — the Drone role is `AmazonSSMManagedInstanceCore` + inline `read-ci-parameters` scoped to `parameter/cv-project/dev/ci/*`. The `Jenkinsfile` Deploy stage is an explicit placeholder, so there is **no legitimate need** for ECR push rights yet. Any IAM widening is scope creep, not a convenience.

### 4. Functional acceptance — the criterion that unblocks the pipeline

Push a throwaway branch to `cv-domain-service`, open a probe PR, then:
`gh pr checks <n>` must list a check reaching `success`/`failure` — **not** stay at `total_count: 0`, today's failure mode. Confirm via `gh api repos/erfeamor/cv-domain-service/commits/<sha>/status` that `total_count >= 1`.

**A build that runs in Jenkins but posts no status is a FAILURE of this task.** Check both sides independently: the Jenkins build log *and* the GitHub status API. Close the probe PR without merging. Repeat for `cv-database` — using a comment-only edit to a **non-migration** file, never a throwaway file under `sql/migrations/`.

### 5. Drone regression (without merging anything)
Drone UI still reachable; `cv-admin-react` still listed/activated (the state at risk under §0 path (a)); a scratch PR still goes green; the webhook at `http://13.39.59.12/hook` shows a `200` recent delivery. **If Jenkins now shares port 80 behind a proxy, specifically re-test Drone's OAuth login flow** (`/login` → GitHub → callback) — the part most likely to break if the proxy mangles `Host` or the path prefix.

### 6. Persistence
Create a throwaway job/credential, `reboot-instances`, then via SSM Session Manager (no SSH) confirm `drone-server`, `drone-runner`, and Jenkins are all `Up` with a restart policy, `JENKINS_HOME` is mounted from a **host path** (not the container's writable layer), and the job survived. Note: a reboot does not touch EBS, so this does **not** validate the §0 replacement risk — that needs its own check.

### 7. Resource contention — most likely to pass now and fail later
During a real Maven build (surefire forks a JVM), from an SSM session: `free -m`, `vmstat 1 10` (watch `si`/`so`), `docker stats`, `dmesg -T | grep -i 'killed process'`, and `docker inspect --format '{{.State.OOMKilled}}'` per container.

**Fail thresholds:** any `OOMKilled: true`, any OOM-killer dmesg entry, sustained (>30 s) available memory under ~100 MB, or persistent swap I/O on a t3.small. Under the t3.micro+swap option, slow is acceptable per that recorded trade-off — **OOM-killed is a task failure either way**, since a build that never finishes posts no status (§4). Run it **concurrently with a Drone pipeline** — that is the realistic contention case.

### 8. Rollback
Revert + re-apply is itself another stop/start or replace cycle — **not free**. If the forward apply already replaced the instance and wiped Drone's SQLite state, rollback does **not** restore it; the manual cv-admin-react re-activation must be redone. Document this in the PR rather than discovering it live. If only the security posture is wrong, `docker stop jenkins` over SSM closes the exposure window fastest — then fix forward.

### QA corrections to this plan (round 1 — the plan itself had a defect)

- **§3a probe path was wrong and would have produced a FALSE PASS.** The plan said "probe the public path" without naming it. Jenkins sits at `--prefix=/jenkins` behind nginx, with `/` routed to **Drone**. Hitting `http://<eip>/` returns Drone's `302` to login — indistinguishable at a glance from a correctly-locked Jenkins, which also returns `302`. **Apply the PASS/FAIL matrix at `http://<eip>/jenkins/`**, and separately confirm `http://<eip>/` still serves Drone. The raw-port probe is `http://<eip>:8080/`, which must refuse at both the SG layer and the host layer (nothing listening) — there is no published Jenkins port at all.
- **§6 persistence must include the `ci-proxy` container.** The original wording listed only `drone-server`, `drone-runner`, `jenkins`. Without `ci-proxy` also `Up` with a restart policy, nothing is reachable even if all three backends are healthy.
- **§8 rollback: "`docker stop jenkins` closes the exposure window fastest" is now wrong.** Jenkins was never independently internet-exposed, so stopping it only 502s the `/jenkins/` path. The equivalent fast action is dropping the `/jenkins/` location block from `ci-proxy` and reloading — kills Jenkins access while keeping Drone up.
- **`terraform test` cannot prove the raw port is unreachable.** The SG assertions prove no *Terraform-managed* rule opens 8080; the actual control is the *absence* of `-p 8080:8080` in a shell script, invisible to Terraform. If a future edit added that flag, every assertion would keep passing while the control broke. Only the live probe proves the runtime half.
- **`user_data_replace_on_change` is a meta-argument, not a readable attribute**, so no plan test can assert "this instance won't be force-replaced". Only a human reading a real plan's `# forces replacement` annotation can.

### Pre-apply gate — human-run, output pasted verbatim into the PR, not summarized

1. `terraform plan` against the **real** state (not the worktree, which has none). Grep for `forces replacement` — must not appear on `aws_instance.domain_service` or `aws_instance.drone`.
2. `aws_instance.domain_service` shows **no changes at all**.
3. `aws_eip_association.drone` shows no `-/+` and no `destroy`.
4. `aws_instance.drone` shows `~ update in-place`, with only `instance_type`, `user_data`, tags changed.
5. `null_resource.jenkins_provision` plans as a create (expected on first apply).
6. Sign-off that 1–5 were actually **read**, not merely that `plan` exited 0. Only then does the checkpoint's `a1` move from caveated to unconditional.
7. **Snapshot live Drone state — not reconstructable afterward:** `docker ps --format '{{.Names}}\t{{.Ports}}\t{{.Image}}\t{{.ID}}'` (proves the current `0.0.0.0:80->80/tcp` binding and pre-migration container id); the activated-repo list from Drone's UI/API (must include `cv-admin-react`); confirm no Drone build is in flight.
8. **EBS snapshot of the Drone root volume.** The one true undo button, and cheap — two risky operations stack in this window (the `t3.small` stop/modify/start *and* the live container remediation).
9. Recorded PO acceptance of the docker-socket trust boundary (see below).

### Post-apply gate — verifiable no other way

1. §3a rewritten probe at `/jenkins/`, plus raw `:8080` refusal.
2. §4 functional acceptance on both repos, checked via the Jenkins build log **and** `gh api .../status` independently.
3. §5 Drone regression, specifically the OAuth `/login` → GitHub → callback round trip.
4. §6 persistence across reboot, `ci-proxy` included.
5. §7 resource contention during a real Maven build, concurrent with a Drone pipeline.
6. §2 idempotency: re-run the provisioning script over SSM; no duplicate or errored containers.
7. Confirm the SSM command reached a genuine terminal `Success` — not a client-side waiter timeout masking a still-running command.
8. Re-check the Drone activation list and container id against the step-7 baseline, proving nothing was lost across the `docker rm -f drone-server` remediation.

### PO decision 2026-08-06 — pin PR-discovery traits BEFORE the trust-boundary sign-off

Raised at the sign-off review, not by a reviewer. **All three repos are public** (`cv-domain-service`, `cv-database`, `cv-infra` — verified `visibility=public`, 0 forks), and the JCasC `multibranchPipelineJob` blocks declare a `github` branch source with **no `traits {}` block at all**, so whatever `github-branch-source` defaults to governs which PRs are discovered and whose `Jenkinsfile` is executed.

That combination is the problem: on a public repo, any GitHub user can fork and open a PR, and a discovered PR's own `Jenkinsfile` is the build script — executing against a container that holds the host Docker socket. Leaving that to plugin defaults is not a decision anyone made.

**Required before sign-off:** declare `traits {}` explicitly on both job definitions. Specifying traits replaces the defaults, so omitting fork-PR discovery is what disables it. Branch discovery plus origin-PR discovery only; no fork-PR discovery (or, if fork PRs are ever wanted, an explicit trust policy of write-permission holders — never "everyone").

This narrows the accepted trust boundary from *"anyone on GitHub"* to *"anyone with push access to the repo"*, which is a normal thing to accept for this demo.

**Implemented and verified in `4015558`.** Both jobs now declare:

```groovy
traits {
  gitHubBranchDiscovery  { strategyId(1) }   // EXCLUDE_PRS
  gitHubPullRequestDiscovery { strategyId(1) }   // origin PRs only, MERGE strategy
}
```

No `gitHubForkDiscovery` trait in the file (verified: 2 traits blocks present, 0 occurrences of fork discovery). Symbols and `strategyId` semantics were confirmed against the plugin's own Java source (`BranchDiscoveryTrait`, `OriginPullRequestDiscoveryTrait`, `ForkPullRequestDiscoveryTrait`), not from recall — `gitHubPullRequestDiscovery` is specifically the *origin*-PR trait, so fork PRs are not discovered at all.

> **Known gap, accepted:** no automated test guards this. `terraform test` cannot evaluate any condition against `local.jenkins_provision_script` because it embeds `aws_eip.drone.public_ip`, which is unknown-until-apply under `command = plan`. So the traits block is protected only by the explanatory comment above it. Re-adding fork discovery, or deleting the block so plugin defaults resurface, would pass every gate silently. Future work: a `command = apply` run under `mock_provider`, or a test-only parallel render.

### Accepted trade-off requiring recorded PO sign-off

**SIGNED OFF by the human 2026-08-06**, conditional on the trait pinning above, which is now implemented and verified. Accepted boundary: **anyone with push access to `erfeamor/cv-domain-service` or `erfeamor/cv-database` can reach root on the CI host and read every CI secret.** Not "anyone on GitHub" — fork PRs are not discovered. Must be reproduced in the PR body.

**Docker socket + shared IAM role collapses the Drone/Jenkins trust boundary.** The mount is *required* — both `Jenkinsfile`s use `agent any` and shell out to `docker`, and this task may not change them — and `drone-runner` already mounts the same socket. But T-002 is the first time the socket is attached to something that **auto-builds branch-controlled `Jenkinsfile` content**, so a PR author gains root-equivalent host access, and one shared role with a `ci/*` policy means either CI system can read the other's secrets. Not a code blocker (no in-scope change fixes it), but it must be written into the PR body as the accepted trust boundary, with IAM segmentation (`ci/drone/*` vs `ci/jenkins/*`) filed as a follow-up task.

### Flagged up front
1. **§0 is the biggest risk** — silent no-op install, or destructive replacement wiping Drone's state. Must be an explicit documented decision.
2. **Port 80 is already fully claimed** by `docker run -p 80:80 drone-server`. "Reverse proxy under a path" therefore requires introducing a real proxy container in front of **both** Drone and Jenkins — not a one-line SG change.
3. The Free Tier exception must be durable (task file / docs / a `variables.tf` comment) with the actual monthly delta.

## Definition of done

PR open against `master` from `feat/jenkins-on-ci-host`, `terraform validate` + `terraform test` green, `/security-review` clean, both backend repos demonstrably **reporting checks** on a real probe PR, Drone regression clean, cost exception recorded.
