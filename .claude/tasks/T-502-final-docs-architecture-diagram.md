---
id: T-502
title: "Final documentation and architecture diagram (the roadmap's last unchecked item)"
repo: cv-project (meta)
status: in_review
owner: tech-product-owner
branch: docs/final-architecture
pr: https://github.com/erfeamor/curriculum/pull/122
depends_on: [T-501, T-052, T-054]
risk: low
security_review: false
checkpoint:
  stage: h2   # reviewed (round 1: 8 findings, all fixed); awaiting H2
  repo: cv-project (meta)
  branch: docs/final-architecture
  worktree: none
  commit: see PR head
  pr: https://github.com/erfeamor/curriculum/pull/122
  developer: tech-product-owner   # driver-written docs, as in T-501
  reviewers: [code-review]
  risk: low
  security_review: false
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a
  updated: 2026-10-08T17:00:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 0
    spawns: 0
    status: ok   # human-reported /usage under ~40%
    checked: 2026-10-08T17:00:00+02:00
---

## H1 — decided by the human, 2026-10-08

1. **Diagram:** a Mermaid block **inline in `docs/architecture.md`** (renders on GitHub). **`diagrams/architecture.mmd` is deleted**, and the README layout lines (EN + ES) drop `diagrams/`.
2. **Per-repo READMEs:** audit all 8 siblings' README/CLAUDE.md for claims that contradict the live system, and **file one small docs task per repo with drift**. T-502 stays a meta-repo PR.
3. **Writer:** the driver writes it (as in T-501), checking every claim against Terraform and the account; one `/code-review` pass on the committed diff.
4. **Budget:** `/usage` under ~40%: the whole task this window.

## Done — 2026-10-08 (driver-written, H1 3)

- **`docs/architecture.md` rewritten** against Terraform and the account, with an inline Mermaid diagram:
  - the edge, with its three behaviors;
  - S3 and Vercel;
  - the app host's containers, the MySQL volume and backups;
  - Cognito, users plus the BFF's machine client;
  - CloudWatch Logs and ECR;
  - the CI host with the doorbell and reaper;
  - the GitHub Actions OIDC deploys through the three SSM documents.

  New sections cover Auth (T-043/T-116/T-113/T-025), Deploys (T-044/T-047/T-049/T-050/T-055/T-112/T-158/T-203/T-403/T-404), CI on demand (T-019/T-034/T-041/T-042/T-048/T-005), Data (T-018/T-001/T-503), Observability (T-052/T-054) and cost. Cost figures are **not** repeated; the section points at the two CLAUDE.md files, so T-051's numbers live in one place each. There are no instance ids.
- **Claims checked against Terraform while writing:**
  - The SPA routing is a viewer function on the default behavior.
  - The Drone key may write anywhere in the frontend bucket, plus invalidations. I first wrote "admin prefix only", which was wrong.
  - The reaper decides "idle" from Jenkins' queue plus 20 minutes of quiet CPU. Drone can't be queried, so CPU stands in. I first wrote "Jenkins and Drone idle", which was imprecise.
- **`diagrams/architecture.mmd` deleted** (H1 1); the README layout lines (EN + ES) now point at `docs/`.
- **README, EN + ES:**
  - § Logs and § Auth no longer state design as current (Atlas; "Cognito within the Free Tier").
  - The services-list log line and the observability roadmap item reflect T-054.
  - The roadmap's last item is ticked.
  - The backlog drops the done T-050 and T-052 lines.
- **Per-repo audit (H1 2):** all 8 READMEs and CLAUDE.md files were scanned for stale deployment claims, and each repo's deploy section was read.
  - **Drift in 2 repos, filed:** [T-056](T-056-cv-infra-readme-free-tier-drift.md) (cv-infra README: "Free Tier", "six repos") and [T-057](T-057-cv-observability-docs-reflect-decision.md) (cv-observability: logging "not wired up yet", pipeline "Jenkins or GitHub Actions").
  - cv-database, cv-domain-service, cv-bff-node, cv-admin-react, cv-public-vanilla and cv-public-react match the live system.

- **`/code-review` medium on 9990f1f: 8 findings, all fixed.**
  - The diagram lacked the browser calls: the admin to `/api/*` with a user JWT, and the vanilla site's fetch of `/bff/*`.
  - Webhooks come from the GitHub repos (every push and PR), not from Actions.
  - The doorbell redelivers **only cv-admin-react's Drone hook**; the Jenkins repos rely on Jenkins' scan.
  - Skills and assignments are **not** versioned.
  - One OIDC role per service does both the ECR push and the SSM send, so it can overwrite `:latest`.
  - Any rendered user_data change replaces the host, not only the script.
  - The self-contradicting backlog line ("out of scope") is removed, EN + ES.
  - This checkpoint was stale.
  - The reviewer confirmed the Mermaid syntax by reading, not by rendering; GitHub's render of the PR is the check.

## Why

The README roadmap's last open item: "Final documentation and architecture diagram". Filed by the 2026-10-06 board review, **after** [T-501](T-501-e2e-cv-milestone.md) (which only ticks the domain-model item), so the docs describe the verified system.

## Known drift to fix (narrowed 2026-10-07 by T-501)

[T-501](T-501-e2e-cv-milestone.md)'s PR already corrected the README roadmap and backlog (EN + ES), the CI/CD table (CI and deploy per repo, GitHub Actions ×5), the "Cloud Infrastructure" services list (`t4g.micro` app host, `t3.small` CI host, Paid plan, Vercel, log groups unused), and `docs/architecture.md`'s deployed-state note, observability and Infra bullets. What's left:

- `docs/architecture.md` still lacks: the BFF's Cognito service token (T-043), machine tokens read-only (T-116), optimistic locking (T-113), the S3 bootstrap + `cv-redeploy` (T-044), the deploy and migrate flows via GitHub OIDC + per-service SSM documents (T-047/T-049/T-112/T-158/T-203), the CI host's DNS name + doorbell/reaper (T-034/T-041/T-042/T-048), the observability decision ([T-052](T-052-observability-scope-decision.md): app logs to CloudWatch via [T-054](T-054-app-container-logs-to-cloudwatch.md), metrics local-only by design); `cv-observability`'s own docs (`docs/logging.md`) say the same.
- `diagrams/architecture.mmd` (linked from `architecture.md`) predates all of the above; the new Mermaid diagram replaces or updates it.
- README design-spec sections still written as current (EN + ES): § Logs lists "MongoDB Atlas (free tier)" as the log store (not deployed), and § Auth says "Cognito falls within the **AWS Free Tier**" (the account is on the Paid plan; user MAUs are in Cognito's own free allowance, but the BFF's machine tokens bill, T-043). Found at T-501's review round 2.
- Per-repo README pointers that contradict the live system (not yet audited).

## Scope

- **A current architecture diagram** (Mermaid in `docs/architecture.md` so it renders on GitHub): the edge (CloudFront paths `/`, `/admin/*`, `/api/*`, `/bff/*`), Vercel, the app host's containers, MySQL on its volume, Cognito (users + the BFF's machine client), the CI host (Jenkins, Drone, doorbell, reaper) and the deploy flows.
- Refresh `docs/architecture.md`, the README roadmap (EN + ES mirror) and per-repo README pointers where they contradict the live system.

## Acceptance criteria

- [ ] The diagram matches the live system, checked against the account and Terraform.
- [ ] No doc in the meta repo claims a state the system isn't in; the roadmap's last item ticked.
