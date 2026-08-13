---
id: T-013
title: Contract — settle the BFF's public edge path and anonymous read semantics
repo: cv-project (meta)
status: in_progress
owner: tech-product-owner
branch: docs/contract-bff-public-routing
pr:
depends_on: []
risk: normal
security_review: false
checkpoint:
  stage: H1
  repo: cv-project (meta)
  branch: docs/contract-bff-public-routing
  worktree: none   # docs-only change in the meta repo; no build, no stack, nothing to isolate
  developer: tech-product-owner
  reviewers: [code-review, infrastructure-engineer, fullstack-developer]
  risk: normal          # task file explicitly refuses the docs fast-path — decision 2 is a security boundary
  security_review: false   # fires on T-202/T-014, which implement the decisions
  wave: [T-006, T-013]
  wave_slot: 1
  merge_order: 1        # lands first — larger § BFF rewrite; T-006 rebases its one-line addition on top
  file_conflict: "docs/api-contract.md — shares § BFF and the status/version line with T-006"
  qa_stage_4: waived    # docs-only: no stack to exercise; substituted by consumer-buildability review
---

## Why this exists

`cv-bff-node` **is not deployed to AWS** — verified against the live account on 2026-08-11, not inferred:

| Check | Result |
|---|---|
| `aws ecr describe-repositories` (eu-west-3) | only `cv-project-domain-service`; no BFF image exists anywhere |
| `cv-infra/templates/domain-service-user-data.sh` | boots MySQL 8.4, Flyway, `domain-service` — **no BFF container** |
| `cv-infra/frontend.tf` `/api/*` behavior | origin is `domain-service-api` (EIP **:8080**) — straight to Java, past the BFF |
| `cv-infra/network.tf` SG | opens 8080 only; port 3000 is unreachable even if something listened |
| `cv-bff-node/.github/workflows/ci.yml` | builds the image, then stops: *"Placeholder until cv-infra exposes a registry + deploy target"* |
| Terraform state (50 resources) | the only BFF-named object in AWS is the empty log group `/cv-project/cv-bff-node` |

Nobody filed this because **the IaC asserts it is already done**: `cv-infra/compute.tf:1` says *"Runs cv-domain-service and cv-bff-node"* and `cv-infra/README.md:14` says *"plus `cv-bff-node` alongside it for the demo"*. Same failure class as T-010 — a documented assumption nobody re-checked against the account.

The admin UI working in AWS is **not** evidence to the contrary: `cv-admin-react` bypasses the BFF by design (`docs/architecture.md:28`), building with `VITE_DOMAIN_SERVICE_URL=""` so calls go same-origin → CloudFront `/api/*` → Java. Only the two public sites need the BFF, and neither has a working data path in AWS.

Deploying it is **not** just adding a container, and that is why this contract task is sequenced ahead of everything else. Two blockers are contract-level decisions, not implementation details:

### Blocker A — path collision

`cv-bff-node/src/app.ts:26` mounts `peopleRouter` at `/api/v1`, so the BFF serves `GET /api/v1/people/:id` — **byte-identical** to the domain-service path that CloudFront already routes to Java for the admin. One path, two required targets, one distribution. The T-201 aggregate (`/api/v1/people/:id/cv`) does not collide; the *existing* endpoint does, and it is the one `cv-public-vanilla` calls today.

### Blocker B — auth

`cv-bff-node/src/app.ts:22-25` applies `requireAuth()` to **all** of `/api/v1` when `AUTH_ENABLED=true`. The public site is anonymous, so a production-correct `AUTH_ENABLED=true` would 401 every visitor; `AUTH_ENABLED=false` leaves the whole surface open. `docs/api-contract.md` § Non-goals currently says *"Auth changes — the existing `AUTH_ENABLED` behavior in both services covers these routes as-is"*, which papers over exactly this. That sentence is wrong for a deployed public BFF and has to change here.

Per the adapter (§2), a contract change is its own PR against `docs/api-contract.md`, sequenced first via `depends_on` — never improvised inside a consuming task.

## What has to be decided

Both need a definite answer written into the contract. Listed as questions because **refinement (H1) settles them**, not because implementers may choose.

**1. How the edge distinguishes BFF traffic from domain traffic.** Options, with the trade-off stated:

| Option | Mechanism | Cost |
|---|---|---|
| **(a) Distinct edge prefix — recommended** | BFF served under its own prefix (e.g. `/bff/*`), a new CloudFront behavior ahead of `/api/*` | Smallest change. `/api/*` → Java stays byte-identical, so the **already-deployed and working** admin is untouched. Both public sites change one env var. |
| (b) Behavior on the more specific path | `/api/v1/people/*/cv` → BFF, rest → Java | Does **not** solve it: the existing `GET /api/v1/people/:id` still collides, and that is the endpoint public-vanilla calls today. |
| (c) Move the admin to its own prefix | `/admin-api/*` → Java | Largest blast radius — re-deploys and re-tests a live, working admin to fix a problem it does not have. |

If (a): the contract must state the public base path, whether the BFF keeps `/api/v1/...` *internally* (with the prefix stripped at the edge or carried in the route mount), and which of the two the published contract paths describe. Ambiguity here is what produces a deploy that 404s.

**2. Anonymous public reads.** The BFF's public read routes must serve unauthenticated traffic while `AUTH_ENABLED=true` remains meaningful for anything non-public. Proposed, to be confirmed: mirror the Java side's explicit exemption list (`SecurityConfig.java:38-41` permits `/actuator/health`, `/actuator/prometheus`, swagger) — enumerate the public read routes as exempt rather than flipping the global toggle off. The contract must say **which routes are public** and that this is deliberate, so a future reviewer does not "fix" it.

State the consequence explicitly too: a public, unauthenticated aggregate is the payload where the § "no `id`, `personId`, `skillId` or `email`" rule stops being cosmetic and becomes the only thing standing between the domain DB and the internet.

**3. `/metrics` exposure.** The BFF's `/metrics` (`app.ts:28-31`) is mounted outside `/api/v1` and is therefore unauthenticated regardless of the toggle. Decide whether it is reachable at the edge at all (recommendation: **no** — cv-observability scrapes it in-network, and it does not need a CloudFront behavior). Write the answer down; it is a one-line decision that is otherwise made by accident in `frontend.tf`.

## Acceptance criteria

- [ ] `docs/api-contract.md` § BFF states the **public edge base path** and how BFF routes map onto it, unambiguously enough that `cv-infra` and both public sites can be built from it without asking.
- [ ] The contract enumerates which BFF routes are **public/anonymous** and states that this is deliberate.
- [ ] The § Non-goals sentence *"Auth changes — the existing `AUTH_ENABLED` behavior in both services covers these routes as-is"* is corrected or removed — it is currently false for a deployed BFF.
- [ ] `/metrics` edge exposure is decided and recorded.
- [ ] The decisions are consistent with the **already-deployed** admin path (`/api/*` → Java), or the PR states explicitly that the admin must be redeployed and says why.
- [ ] `docs/architecture.md` § flow diagram reflects the chosen edge paths.

## Definition of done

PR open against `master` from `docs/contract-bff-public-routing`, ratified at H2, merged. Consumers (T-202, T-014) become claimable.

## dev-loop notes

- **Developer:** `tech-product-owner` (contract-only change; no repo persona implements a docs PR). **Reviewers:** `infrastructure-engineer` (owns the edge/CloudFront surface that consumes decision 1) + `fullstack-developer` (owns the BFF that implements decisions 2 and 3).
- **Risk `normal`, not `trivial`:** the fast-path (adapter §5) covers docs, but this doc is the source of truth three downstream repos build from, and decision 2 defines a security boundary. Do not one-line-confirm the gates.
- `security_review: false` — no code or config changes here. It fires on T-202 and T-014, which implement the decisions.
- **H1 must produce a decision, not a survey.** Every option above is written with a recommendation; refinement picks one and records why the others lost, so this is not re-litigated in the consuming tasks.
