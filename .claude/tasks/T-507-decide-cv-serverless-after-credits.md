---
id: T-507
title: "Decide whether to move the CV to serverless before the credits expire (May 2027)"
repo: cross-repo
status: todo
owner: 
branch: spike/cv-serverless-decision
pr:
depends_on: [T-506]
risk: normal
security_review: false
---

> **Conditional, dated.** Not schedulable before **2027-05-01**. Claim it then, so the decision lands before the credits expire on **2027-07-12** and the bill starts going to the card.

## Why

[T-506](T-506-spike-serverless.md) priced the move ([docs/spike-serverless.md](../../docs/spike-serverless.md)) and said no-go **today**: it saves ~$6.90/month, only after 2027-07-12, for a rewrite of the data layer (JPA on Aurora DSQL, no foreign keys, Flyway, cold starts). That verdict depends on one thing that will change: the human is building budgetPlanner serverless on Aurora DSQL, which proves (or disproves) the same pieces in practice.

## Scope

Re-decide, with measurements instead of estimates:

- **Inputs:** budgetPlanner's real AWS cost (Cost Explorer, tagged by app); how Aurora DSQL behaved there (IAM-token connections, migrations, missing foreign keys, any limits hit); the CV's run rate then (it was **$0.25/day** on 2026-11-20); credits left and the card bill expected from 2027-07-12.
- **Re-price** the CV move with that experience, and list what is reusable (infra modules, migration flow, auth).
- **Also price the cheaper levers** T-506 did not: a one-year Compute Savings Plan on the app host, and any host right-sizing.

## Acceptance criteria

- [ ] A short decision note (update docs/spike-serverless.md or add a dated section) with go / no-go, and the number it rests on.
- [ ] On **go**: follow-up tasks per repo, with the migration order and the date the host can be switched off. On **no-go**: say what the bill will be after 2027-07-12 and that the host stays.
