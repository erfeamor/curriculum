---
id: T-060
title: "The rules allow normalizing CI and put cost first; file M3"
repo: cv-project (meta)
status: in_review
owner: tech-product-owner
branch: docs/m3-policy
pr: https://github.com/erfeamor/curriculum/pull/129
depends_on: []
risk: trivial
security_review: false
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

Two rules forbid M3's Phase B today. The dev-loop adapter says *"Different CI per repo is a feature of the demo … never normalize it"* (`.claude/dev-loop-adapter.md` §3 and its CI column), and the meta `CLAUDE.md` conventions say the same. The human decided on 2026-11-07 to put **money ahead of technical simplicity** and move every pipeline to GitHub Actions.

## Scope

- The meta `CLAUDE.md` conventions: GitHub Actions everywhere (Vercel stays for cv-public-react), cost first.
- The local dev-loop adapter (gitignored, edited in place): the CI column and the "never normalize" sentence.
- M3's 16 task files and the TASKS.md section, plus the Now/Next lanes.

## Acceptance criteria

- [ ] Neither rule still says "never normalize CI".
- [ ] Every M3 task is filed, and `board-check` is clean.
