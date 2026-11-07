---
id: T-066
title: "Shrink the MySQL data volume from 8 GB to 2 GB"
repo: cv-infra
status: todo
owner: 
branch: feat/shrink-mysql-volume
pr:
depends_on: [T-065]
risk: high
security_review: true
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

The data is a few MB, and the 8 GB volume costs ~$0.74/month; a 2 GB one costs ~$0.19. The 8 GB root is the AMI's minimum and stays.

## Scope

- Run a planned swap:
  1. `systemctl start mysql-backup.service`, and keep a local copy
  2. create a new 2 GB `aws_ebs_volume`
  3. restore from the dump
  4. switch the attachment
  5. retire the old volume (its `final_snapshot` is kept)
- `prevent_destroy` (`storage.tf:193-195`) means a deliberate two-step change. Document it as a runbook.

## Acceptance criteria

- [ ] Row counts match before and after, and the public CV is unchanged.
