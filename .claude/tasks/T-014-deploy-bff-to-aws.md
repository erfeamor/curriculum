---
id: T-014
title: Deploy cv-bff-node to AWS — registry, container, edge route
repo: cv-infra
status: todo
owner:
branch: feat/deploy-bff-node
pr:
depends_on: [T-013, T-202, T-201]   # T-201 added 2026-08-24 on the human's instruction, as a SEQUENCING decision, not a technical one — T-014 can deploy without it. Ruling 7 (below) had this task knowingly deploy an image that 404s the contract's aggregate, with NO task on T-501's path owning the redeploy that fixes it: the task that rebuilds and rolls the BFF container is T-203, which is DOWNSTREAM of this one and is absent from T-501's depends_on (the board calls it "off the critical path"), so the milestone could verify end-to-end against a BFF still 404ing /cv. So a manual redeploy was baked into the plan and assigned to nobody — the hot-potato shape T-404 was filed for. Deploying T-201's code in the FIRST image removes that step and lets this task's one expensive apply verify /cv in the stage-4 run it is already paying for. Encoded as depends_on rather than prose per T-016's precedent ("this board has repeatedly lost gating conditions that lived only in prose"). REVERSIBLE IN ONE LINE: if H1 wants the BFF deployed sooner, drop this edge and file the redeploy as its own task — but do not simply drop it and leave the redeploy unowned again.
risk: high
security_review: true
checkpoint:
  stage: H1
  note: "NOT a fresh todo. Stage 0 refinement completed 2026-08-14 and the seven DoR rulings below are written up (this said 'six' until 2026-08-17 — ruling 7 was added by QA during the same refinement and the count was never updated); whoever picks this up starts at IMPLEMENTATION, not refinement. Deliberately left status:todo with no owner — an H1-complete task with an owner set reads as in-flight and blocks re-pickup under board rule 1. Same pattern T-018 used successfully."
  repo: cv-infra
  branch: feat/deploy-bff-node
  worktree: none   # cv-infra has a local Terraform backend; it cannot be worked from a worktree
  developer: infrastructure-engineer
  reviewers: [code-review, infrastructure-engineer, security-review, quality-assurance]
  risk: high
  security_review: true
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  premises_reverified: "2026-08-14 against cv-infra@774a9fc and cv-bff-node@b63eae2. Every original claim in this task still holds: no BFF ECR repo, no BFF container in user_data, exactly one ordered_cache_behavior (/api/* → domain-service-api), bff_node log group still empty, and compute.tf:1 still falsely claims the box runs the BFF."
  budget_note: "Refinement only — no code, no applies. Stopped deliberately at H1 with the probe at ~70% of ceiling_turns (280/400) and ~120 turns left. T-018 cost ~190 turns from an ALREADY-REFINED start; T-014 is larger (ECR + container + edge + SG + spa-router + forced security review + live public-path verification), so implementation could not have finished in the remaining budget. Stopping at a checkpoint beats being cut off mid-apply. Implementation needs a fresh session."
---

## Why this exists

This is the task that closes the gap. `cv-bff-node` has no registry, no runtime and no route in AWS (evidence table in T-013), while `cv-infra` claims in two places that it is already running. Both the deployment and the correction of those claims live in **this** repo.

The intended approach is the domain service's, per the meta README backlog — *"backend services still deployed manually"*: build image → push to ECR → run it as a container on the existing EC2 box. This task builds the target; T-203 automates the push.

## Two things T-022 established that change ruling 1 (added 2026-08-20)

[T-022](T-022-domain-service-origin-bypasses-cloudfront.md) applied the prefix-list pattern to port 8080 for real, and measuring it turned up two facts ruling 1 was written without:

1. **You cannot put a second prefix-list rule on `aws_security_group.domain_service`.** An AWS-managed prefix list counts against the *"inbound rules per security group"* quota (**60**) as its **entry count**, not as one rule. The CloudFront list held **46 entries** on 2026-08-20. One reference fits with 14 to spare; two (46 + 46 = 92) exceed the quota and **the apply fails**. So port 3000 needs its **own security group** for the BFF — which is cleaner anyway, and is a change to this task's scope §3, not a detail.
2. **The prefix list proves "a CloudFront distribution", not "our distribution"** — it is shared by every CloudFront customer. T-022's `/security-review` raised this as a MEDIUM finding and it applies identically to port 3000. Filed as [T-025](T-025-verify-requests-come-from-our-cloudfront.md); read it before deciding how much this task should carry. It does **not** block this task — ruling 1 is still strictly better than `0.0.0.0/0`.

Ruling 1 stands. Its mechanism is proven and its wording just needs the extra security group.

## Scope

**1. Registry** — `aws_ecr_repository.bff_node` + lifecycle policy in `registry.tf`, mirroring `domain_service`. The header comment there budgets against ECR's 500 MB; a `node:20-alpine` runtime image is ~50-60 MB compressed, so two retained tags fit comfortably. Keep `force_delete = true` for parity.

**2. Runtime** — a `docker run` block in `templates/domain-service-user-data.sh`, on the existing `cv` docker network, with:
- `DOMAIN_SERVICE_URL=http://domain-service:8080` (container-to-container on the `cv` network — **not** the public EIP; do not send BFF→domain traffic out to the internet and back),
- `AUTH_ENABLED` / `COGNITO_ISSUER_URI` per T-013's ratified auth model, issuer read from SSM like the domain service does,
- `CORS_ALLOWED_ORIGINS` including the CloudFront domain (`aws_cloudfront_distribution.frontend.domain_name` is already threaded into this template),
- `--restart unless-stopped`, and the same retry-until-the-image-exists loop the domain service uses — the image will not exist on first boot.

**3. Edge** — a CloudFront origin + `ordered_cache_behavior` in `frontend.tf` for the path T-013 ratified, **declared before** the `/api/*` behavior if the chosen prefix could otherwise be shadowed. Copy the `/api/*` behavior's no-cache posture (TTLs 0) — the aggregate is per-person and revalidated by ISR upstream, so edge caching here would fight `cv-public-react`'s own caching story.

**4. Exposure** — the BFF's port must be reachable by CloudFront but **not** open to the world beyond what that requires. Adding a second internet-facing port to `aws_security_group.domain_service` is the obvious move and the one to justify explicitly in the PR: state why the chosen ingress is no wider than needed. (`observability.tf` already has the `bff_node` log group; it is currently empty and should start receiving logs — wire it or say why not.)

**5. Correct the false claims in this repo** — `compute.tf:1` (*"Runs cv-domain-service and cv-bff-node"*) and `README.md:14` (*"plus cv-bff-node alongside it"*) both assert this task's outcome as already true. They become true with this PR; if any part of the scope is dropped, the comments must say what is actually running. Do not leave them describing an aspiration.

**6. `terraform test`** — `tests/plan.tftest.hcl` uses `mock_provider`; extend the mocks for any new data source and add assertions for what this task pins (the new ECR repo, the new behavior's origin). Per the repo's own review guidance, a task that pins a resource property updates the assertions in the same PR.

## Watch-outs (measured, not hypothetical)

- **RAM.** The box is a `t3.micro` (1 GB) already carrying MySQL 8.4 + a JVM on a 2 GB swapfile; `templates/domain-service-user-data.sh` itself recommends a `t3.small`. Adding a Node process pushes it further into swap. If the plan resizes the instance, `terraform test`'s instance-class assertion and the cost note must change **in the same PR** — and T-010's finding applies: trimming or growing run rate does not change the Free-plan cliff, so argue this on stability, not cost.
- **`user_data_replace_on_change`** is already set on `aws_instance.domain_service` and must stay. Editing the bootstrap without it updates state and never re-provisions the box — this exact bug shipped once (repo review guidance item 3). This task edits `user_data`, so the instance **will** be replaced. ~~MySQL data lives on `/var/lib/cv-mysql` on the host volume and **is lost when the instance is replaced**. Plan for that before applying — this is the sharpest edge in the task.~~ **Superseded by [T-018](T-018-mysql-on-dedicated-ebs-volume.md), struck here 2026-08-17** — `/var/lib/cv-mysql` is now mounted from a dedicated EBS volume that survives replacement, proven by test. The replacement still happens and still has to be verified (§6 of the test plan); it is simply no longer destructive to data. The strike-through is applied *here*, at the watch-out itself, because the supersession was previously recorded only two sections further down — a reader who stopped at the watch-outs got the opposite answer. **The live sharp edge is now `var.db_password`: do not change it during this task (T-021).**
- **No NAT gateway, no new EIP.** ~$32/mo and ~$3.60/mo respectively; the two existing public IPv4s are already ~24% of the bill (T-010).
- **No SSH.** Shell access stays SSM Session Manager. Do not add port 22 or a key pair to debug the container.

## Definition of Ready — refined 2026-08-14

Premises re-verified against `cv-infra@774a9fc` and `cv-bff-node@b63eae2` before refining. **All of the task's original claims still hold**: no `aws_ecr_repository` for the BFF (only `domain_service`), no BFF container anywhere in `templates/domain-service-user-data.sh`, exactly one `ordered_cache_behavior` (`/api/*` → `domain-service-api`), and `observability.tf:10`'s `bff_node` log group still empty. `compute.tf:1` still claims the box "Runs cv-domain-service and cv-bff-node".

**Seven** rulings, plus two corrections that follow them. Each is a place where the obvious implementation is wrong or the task prose is now out of date. (Counted as "six" until 2026-08-17; ruling 7 arrived later in the same refinement, from QA.)

### 1. Do NOT copy the existing security-group pattern for port 3000

`network.tf:40-45` opens **8080 to `0.0.0.0/0`**, so the domain service is directly reachable on the public internet, bypassing CloudFront entirely. Scope §4 says the BFF's ingress must be "no wider than needed" — copying the neighbouring rule would be the obvious move and would fail that test.

**Ruling:** ingress for 3000 is scoped to CloudFront's own origin-facing ranges via the managed prefix list — `data.aws_ec2_managed_prefix_list` with name `com.amazonaws.global.cloudfront.origin-facing`, referenced as `prefix_list_ids` on the ingress rule. Not `0.0.0.0/0`. The PR must state this explicitly, per scope §4.

**Separately:** that pre-existing `0.0.0.0/0` on 8080 is a real exposure and is **out of scope here** — do not fix it in this PR. ~~It wants its own task, and H1 should decide whether to file one now.~~ **Filed 2026-08-14 as [T-022](T-022-domain-service-origin-bypasses-cloudfront.md)** on the human's instruction at H1. Probing it turned up more than an open port: `/v3/api-docs` answers **200 unauthenticated** on the public IP, leaking the whole OpenAPI surface, and it grows automatically as M2 lands resources. T-022 applies the *same* managed-prefix-list fix to 8080 that ruling 1 mandates for 3000 — so **doing T-022 first makes this task follow an established pattern instead of inventing one**, and gives the reviewer one consistent approach across both ports. Not a hard dependency in either direction.

### 2. Behavior ordering is a non-issue — the task prose overstates it

Scope §3 says the new behavior must be "declared before the `/api/*` behavior if the chosen prefix could otherwise be shadowed". `/bff/*` and `/api/*` cannot shadow each other; CloudFront matches by most-specific path pattern and these are disjoint. **Ruling:** no ordering constraint between the two. Both must still precede the default behavior, which is already true structurally.

### 3. The origin is the existing EIP on a different port — no new origin host

`frontend.tf:83` already points the `domain-service-api` origin at `aws_eip.domain_service.public_dns` with `custom_origin_config { http_port = 8080 }`. **Ruling:** the BFF origin is the *same* DNS name with `http_port = 3000` and `origin_protocol_policy = "http-only"`, as a second `origin` block with its own `origin_id`. No new EIP (forbidden by the watch-outs), no NAT, no second instance.

### 4. `/metrics` and `/health` — fix the function, and prove it by request

`functions/spa-router.js` rewrites *every* extension-less URI to an `index.html`, so both paths answer **200 with the public SPA shell** today. Nothing routes them to the BFF and the contract says nothing should — the defect is purely that a monitoring probe aimed at the CloudFront domain reads that 200 as "healthy".

**Ruling:** exclude both in the function so they fall through to a genuine 404. **Capture the current 200 as a baseline before the apply** — otherwise "it 404s now" does not prove the change caused it. Verify by real request against the distribution, never by reading the Terraform.

### 5. `AUTH_ENABLED=true` in AWS, with the issuer from SSM

The BFF defaults `AUTH_ENABLED` **off** (meta CLAUDE.md), which is right for local dev and wrong here: deployed with it off, every route under `/bff/api/v1` would be anonymous, not just the contract's two. **Ruling:** set `AUTH_ENABLED=true` and read `COGNITO_ISSUER_URI` from SSM exactly as the domain service does. The contract's allowlist (`PUBLIC_ROUTES`) is what keeps the two public reads anonymous — it only functions when the guard is actually installed.

### 6. CORS: the browser case is the only one that matters

`CORS_ALLOWED_ORIGINS` must include the CloudFront domain, which is already threaded into the template as `cloudfront_domain`. **Ruling:** note in the PR that `cv-public-react` does **not** need an entry — it fetches the aggregate **server-side** under ISR, and CORS does not apply to server-side fetches. Adding its Vercel domain would be cargo-culting an origin that never appears in an `Origin` header.

### Superseded by T-018 — do not re-derive

The watch-out about `user_data_replace_on_change` destroying MySQL, and acceptance criterion 4 below, are **obsolete**. [T-018](T-018-mysql-on-dedicated-ebs-volume.md) merged 2026-08-14: the datadir is on a dedicated EBS volume and survival across replacement is proven. Criterion 4 becomes *"confirm `/var/lib/cv-mysql` is still mounted from the dedicated volume after the apply"*.

**New precondition in its place:** do **not** change `var.db_password` during this task. Per [T-021](T-021-mysql-password-rotation-persistent-datadir.md), the now-persistent datadir means MySQL keeps its original credentials while the bootstrap reads the new one — Flyway fails auth, `set -e` aborts, and the box comes up with **no domain-service container at all**.

### 7. The deployed BFF will 404 the contract's aggregate endpoint — expected, not a defect

Found by QA while writing the test plan, verified by the driver against `cv-bff-node@b63eae2`. **`T-201` (the `GET /bff/api/v1/people/:id/cv` aggregate) is `todo` and is not in this task's `depends_on`.** `src/routes/people.ts` contains exactly one handler, `router.get('/people/:id')` — there is no `/cv` route in the image this task will deploy.

The subtlety: `src/middleware/auth.ts:53` **already allowlists** `/people/:id/cv`. So the request passes the auth gate and then finds no handler — it returns **404, not 401**.

~~**Ruling:** T-014 deploys the BFF as it exists; the aggregate arrives with T-201, and **no infra change will be needed then** because the route is already allowlisted and the edge behavior is path-prefix based. Acceptance criterion 1 ("a public read route returns 200") is satisfied by `GET /bff/api/v1/people/:id`. Record the `/cv` 404 in the QA report so nobody later reads it as a T-014 deployment bug.~~

> **REVISED 2026-08-24 on the human's instruction — T-201 now precedes this task (see `depends_on`).** The ruling above is *technically* correct and remains so: no **infra** change is needed when T-201 lands. But "no infra change" is not "no work" — **a new container image still has to be built and deployed**, and this ruling left that step off the milestone's path. [T-203](T-203-bff-ci-deploy-stage.md) — *"BFF CI: push to ECR and roll the container on master"* — is the task that would do it, but it is **downstream of this one** and is **not in [T-501](T-501-e2e-cv-milestone.md)'s `depends_on`**; the board explicitly calls it *"off the critical path"*. So the plan as written allowed T-501 to run its end-to-end verification against a live BFF that still 404s the contract's aggregate, with no board line obliged to fix it first.
>
> **What changes:** T-201 merges first, so the image this task deploys already serves `/cv`. **What does not change:** ruling 7's *analysis* — the allowlist genuinely does already cover `/people/:id/cv` (`src/middleware/auth.ts:53`), so no edge or auth work appears here either way.
>
> **Consequences for this task, both in its favour:**
> - Stage-4 §3's auth matrix gains a second real public route to exercise, on an apply already budgeted — verifying `/cv` live otherwise needs an apply nobody has scheduled.
> - **A 404 on `/cv` is now a FAILURE, not an expected observation.** With T-201 in the image, a 404 means the route did not ship or the edge is misrouting. **A 401 remains a real defect for the original reason** (the allowlist regex is not matching) — that half of ruling 7 is unaffected and is still the sharpest check in §3.
>
> Kept struck rather than deleted: the reasoning was sound for the sequencing it assumed, and the failure was the *unowned hand-off*, not the analysis.

**A 401 on that path would be a real defect** — it would mean the allowlist regex is not matching, which is precisely the thing T-202 proved only in unit tests.

### Correction to the QA plan — do not follow its checks 1.4 and 8.4 as written

The test plan (below) assumes port 3000 will likely be `0.0.0.0/0` "since CloudFront has no fixed IP range to scope to". **That is wrong**, and ruling 1 above overrides it: AWS publishes `com.amazonaws.global.cloudfront.origin-facing` as a managed prefix list precisely for this. Checks 1.4/8.4 must assert the ingress **is** prefix-list-scoped, not accept `0.0.0.0/0` on the precedent of the existing 8080 rule. The plan was written before this ruling existed; the ruling wins.

### Open question for the implementer — flag, do not guess

The BFF container must reach the domain service as `http://domain-service:8080` on the `cv` docker network (scope §2). That name only resolves if the domain-service container is running **and** was started with `--name domain-service` on that network. The bootstrap starts MySQL → Flyway → domain-service → (new) BFF in sequence under `set -euo pipefail`, so ordering is likely fine on first boot — but establish what happens when the **BFF starts before the domain service is healthy** (it has `--restart unless-stopped`, so it will retry). Report the behaviour rather than assuming the retry loop makes it moot.

## Acceptance criteria

- [ ] `terraform fmt -check -recursive` clean, `terraform validate` succeeds, `terraform test` passes **offline** (mocks extended, assertions added).
- [ ] Applied for real, and verified against the live account: the BFF container is running, a public read route returns 200 through the **CloudFront domain** (not the origin directly), and `/api/*` still reaches Java so the live admin is unaffected.
- [ ] The domain service, MySQL and the admin are all still working after the apply — explicitly re-checked, given the instance replacement.
- [ ] ~~MySQL data survived the replacement, or its loss was a recorded, accepted decision made **before** the apply.~~ **Superseded by T-018** — now: `/var/lib/cv-mysql` is still mounted from the dedicated EBS volume after the apply, and the data is intact.
- [ ] `compute.tf:1` and `README.md:14` describe what actually runs.
- [ ] **`/metrics` and `/health` are excluded from the `spa_router` CloudFront Function** (`functions/spa-router.js`) so they return 404 at the edge. Added 2026-08-13 from T-013's review: the function rewrites every extensionless URI to `/index.html`, so without this both paths answer **200 with the public SPA shell**. No metrics leak — nothing routes them to the BFF — but a monitoring probe aimed at the CloudFront domain reads that 200 as "healthy". Verify with a real request against the distribution, not by reading the Terraform.
- [ ] No new EIP, no NAT gateway, no port-22 ingress, no secret in a committed file.

## Test plan — authored by `quality-assurance` at stage 0, 2026-08-14

QA authors the plan it later executes. Live values at authoring time: CloudFront `dvdlxl0zqepqi.cloudfront.net`, EIP `15.236.195.130`, instance `i-029dd84261c922f72`. **Read "Correction to the QA plan" above — i.e. ruling 1 — before executing §1.4/§8.4.** (This said "ruling 7's correction" until 2026-08-17; ruling 7 is the `/cv` 404 finding and says nothing about ingress. The correction that overrides §1.4/§8.4 is ruling 1's prefix-list decision.)

### §0 · Baseline — MUST run before the apply, cannot be reconstructed afterwards

- **0.1** `/bff/api/v1/people/1` through CloudFront is **not** 200 today (no `/bff/*` behavior exists). If it already is, the premises are stale — stop.
- **0.2** `/metrics` and `/health` return **200 with the SPA shell**. This is the "before" that makes **acceptance criterion 6**'s 404 meaningful (corrected 2026-08-17 — this said "criterion 4", which is the MySQL criterion T-018 superseded). Capture the body, not just the status.
- **0.3** Snapshot the DB fixture (T-018 left `person id=1`, `T018 Survival Probe`) — the diff target for survival after replacement.
- **0.4** Snapshot the MySQL volume UUID — the one piece of evidence a reformat cannot fake.
- **0.5** Record the EIP and the current SG rules, for the "no new EIP / no widened ingress" checks.

### §1–2 · Edge routing and the prefix-stripping trap

- Person route returns 200 through the **CloudFront domain**, with the BFF's `PublicPerson` shape (`{name, headline, location, summary}` — **no `id`, no `email`**). Getting `fullName`/`id`/`email` back means `/bff/*` is routed to the wrong origin.
- **The discriminator for a stripped prefix:** if the edge 404s, `curl localhost:3000/bff/api/v1/people/1` **on the box** via SSM. 200 on-box + 404 at the edge isolates it to CloudFront; 404 in both places means the app, not the routing. Do this before concluding it is a Terraform bug.
- Confirm no `function_association` rewrites `/bff/*` — the contract explicitly rejects a stripping rewrite.

### §3 · Auth matrix — the first live proof for T-202 as well as this task

Precondition: confirm on-box that the container really has `AUTH_ENABLED=true` and a real issuer. With the gate off, every check below passes for the wrong reason.

- Both allowlisted routes anonymous (`GET`, and `HEAD` — the allowlist includes it).
- **`POST` to the otherwise-public path must 401** — proves the allowlist is method-exact, not prefix-based. This is exactly what T-202 asserted in unit tests and never proved live.
- **A non-existent path under `/bff/api/v1` must 401, not 404** — the guard mounts ahead of route dispatch, so any future non-public route is gated by default. A 404 here means the opposite, and every route added later is open by default.

### §4 · `/metrics` and `/health` at the edge

404, not 200-with-shell — and the body must be a real 404, **not Prometheus text** (which would mean they are now routed to the BFF, contradicting the contract). Then confirm both still answer **in-network** on `localhost:3000`: if they broke there too, the exclusion was implemented in the app instead of at the edge, which breaks `cv-observability`'s scrape. Also confirm ordinary SPA deep links still rewrite — an over-broad exclusion pattern would 404 legitimate client routes.

### §5 · No regression on `/api/*`

`/api/v1/people/1` still 401s (correct — Java's auth is on), and the **live admin UI still loads its people list** with a real Cognito JWT. The admin bypasses the BFF by design, which is why this gap stayed invisible for months; it is also why a regression here would be quiet.

### §6 · Instance replacement

Instance ID **must** change (if it does not, `user_data_replace_on_change` did not fire — itself a defect). EIP unchanged. **Volume ID and volume UUID unchanged**, boot log shows `already has a filesystem -- reattach, not formatting`, DB fixture intact, `/var/lib/cv-mysql` still mounted from the dedicated volume. Confirm `var.db_password` was **not** touched (T-021) and that all three containers are `Up` without restart loops.

### §7 · CORS — why the obvious test is the wrong one

In production `cv-public-vanilla` and the BFF are served from the **same distribution**, so the public site's own fetch is **same-origin** and would work under any CORS config. The check that matters is therefore the negative one: an `Origin: https://evil.example.com` request must **not** be reflected and must not get a wildcard. `cv-public-react` is irrelevant here — ISR fetches server-side, sends no `Origin`, and CORS never applies.

### §8 · Beyond the acceptance criteria

Nonexistent id → 404 passthrough, not 5xx · **T-204's traversal bug is expected to still be present** and is *not* a T-014 defect — record the behavior, do not bounce it · no port 22, no NAT, no second EIP · ECR lifecycle policy mirrors `domain_service` · `compute.tf:1` and `README.md:14` corrected · CloudWatch log group either wired or explicitly justified.

### What proves vs. merely suggests

**Proves:** edge routing shape, the on-box/edge discriminator, the 401-on-POST and 401-on-unknown-path checks, the edge 404s, and the volume UUID match. **Suggests only:** SG rule presence (does not prove CloudFront can actually reach it), absence of log streams, and case-insensitivity behavior.

## Definition of done

PR open against `master` from `feat/deploy-bff-node`, gates green, applied and verified, merged. Unblocks T-203, T-403 and the meta doc close-out (T-015).

## dev-loop notes

- **Developer:** `infrastructure-engineer` (adapter §2 — `cv-infra` Terraform/AWS). **Reviewers:** `/code-review` + `infrastructure-engineer` specialist lens + `quality-assurance`, plus `/security-review` (forced, see below). This is the `high`-risk reviewer set from adapter §7.
- **`security_review: true`, forced by adapter §5**, on three independent paths: security-group ingress, published container ports, and CORS config. Also touches auth env wiring.
- **`risk: high` is deliberate.** Adapter §7: *"a high-risk infra task with a real apply and stage-4 verification against AWS is the expensive shape — budget for the full ceiling and do not start one on a `SOFT` reading."* Probe the budget before starting, and do not run this in a wave with other tasks.
- **H2 must gate the apply, not just the merge.** The instance replacement is destructive to the self-hosted MySQL volume; the human gate is the point where that is accepted or a backup is taken first. ~~T-001 (mysqldump→S3) is the mitigation and is still `todo` — consider doing it first~~ — **stale, corrected 2026-08-14: T-001 is `done`** (applied and restore-verified 2026-08-13, nightly timer live). A nightly dump still does not protect data written between dumps, so re-check the database contents at H2 regardless; see the next two bullets.
- **T-001 was added to `depends_on` earlier on 2026-08-13 and has been removed again the same day.** The reasoning behind adding it was wrong, and the correction is recorded rather than quietly reverted: the dependency rested on an unverified assumption that the MySQL volume held something worth keeping. It does not. The human confirmed the database contains only test data, nothing authored. **The volume loss at this apply is accepted, not mitigated** — there is nothing to mitigate.
- **This is a dated fact, not a permanent property.** The moment the demo holds real CV content, this apply destroys it and no backup task changes that, because a nightly dump does not survive being replaced by an apply that runs between dumps. The durable fix is [T-018](T-018-mysql-on-dedicated-ebs-volume.md) — MySQL on a volume with a lifecycle independent of the instance. Check whether the database still holds only test data **before applying**; if it does not, do T-018 first.
- ~~**T-018 is cheaper if done with this task**, since both replace the instance and one replacement can serve both.~~ **Moot — [T-018](T-018-mysql-on-dedicated-ebs-volume.md) merged 2026-08-14** ([cv-infra#16](https://github.com/erfeamor/cv-infra/pull/16)). Its two applies are spent, and the important consequence for this task is that **the instance replacement here is no longer destructive to the database**: MySQL's datadir is on a dedicated volume that survives replacement, proven by writing rows between two applies and reading them back with the volume UUID unchanged. Scope-3 of the watch-outs above (*"MySQL data lives on /var/lib/cv-mysql on the host volume and is lost when the instance is replaced"*) and acceptance criterion 4 are **superseded** — treat criterion 4 as "confirm the volume is still mounted after the apply", not "accept the loss".
- **New precondition from T-018, though:** do **not** change `var.db_password` as part of this task. The datadir now persists, so MySQL keeps its original credentials while the bootstrap reads the new one — Flyway fails auth, `set -e` aborts, and the domain-service container never starts. Tracked as [T-021](T-021-mysql-password-rotation-persistent-datadir.md), unfixed at time of writing.
- Gates (adapter §3): `terraform fmt -check -recursive` · `terraform validate` · `terraform test`, from `cv-infra/`. No CI system — the gates are the local commands.
- `terraform apply` stays in `ask` in `settings.local.json` **on purpose** — do not allowlist it to speed this up.
