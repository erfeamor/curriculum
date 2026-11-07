---
id: T-506
title: "Spike: serverless (Lambda + a database off MySQL) priced against the trimmed host"
repo: cross-repo
status: todo
owner: 
branch: spike/serverless
pr:
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

- [ ] A decision document with a recommendation, and a follow-up task only if the saving justifies it.
