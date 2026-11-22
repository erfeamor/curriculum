---
id: T-506
title: "Spike: serverless (Lambda + a database off MySQL) priced against the trimmed host"
repo: cross-repo
status: done
owner: tech-product-owner
branch: spike/serverless
pr: https://github.com/erfeamor/curriculum/pull/145
depends_on: [T-069]
risk: normal
security_review: false
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

The human chose to trim the EC2 now and price serverless later.

## Scope

- **Options to prototype and price:**
  - the BFF on Lambda (Node, Function URL behind CloudFront with OAC)
  - the domain service on Lambda with SnapStart (Spring Boot 3.3; the JVM takes 30–40 s to start today)
  - the database on Aurora DSQL (Postgres, permanent free tier of 100k DPUs and 1 GB; no foreign keys) or on DynamoDB (25 GB always free)
- **Cost each option against M3's measured rate,** and list the real price in work and risk:
  - JPA/Hibernate on DSQL
  - rewriting the Flyway migrations
  - the local dev stack
  - cold starts on the public CV

## Acceptance criteria

- [x] A decision document with a recommendation, and a follow-up task only if the saving justifies it.

## DONE

Decision document: [docs/spike-serverless.md](../../docs/spike-serverless.md), 2026-11-21.

- **Verdict: no-go on moving the CV.** It saves ~$6.90/month, only after 2027-07-12 (credits cover the bill until then), and costs a data-layer rewrite (JPA on Aurora DSQL, no foreign keys, Flyway). The CV decision is re-opened by [T-507](T-507-decide-cv-serverless-after-credits.md) (May 2027).
- **Serverless pays off for a new app.** The `budgetPlanner` estimate on Lambda is +$1.30/month ($30 of credits still expire unused); on the app host it would need `t4g.small` (+$6.86/month) and the credits would run out on 2027-05-28.
- Run rate re-measured at $0.25/day (last 5 full days).
