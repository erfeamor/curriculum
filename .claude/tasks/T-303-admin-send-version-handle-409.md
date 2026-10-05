---
id: T-303
title: "Admin: keep each row's `version`, send it on PUT, and handle a 409 (changed elsewhere — reload)"
repo: cv-admin-react
status: in_progress
owner: tech-product-owner
branch: feat/version-409
pr:
depends_on: [T-046]
risk: normal
security_review: false
checkpoint:
  stage: implement   # H1 decided 2026-10-05 (wave with T-044)
  repo: cv-admin-react
  branch: feat/version-409
  worktree: none
  commit:
  pr:
  developer: fullstack-developer
  reviewers: [code-review]
  risk: normal
  security_review: false
  review_round: 0
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a
  updated: 2026-10-05T00:30:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 0
    spawns: 0
    status: ok   # human-reported /usage 40–75%
    checked: 2026-10-05T00:30:00+02:00
---

## H1 — decided by the human, 2026-10-05

- **On a 409:** show "This entry was changed elsewhere" by the form, **keep the user's edits**, and offer a **Reload** button that fetches the latest (with its `version`) and discards the stale edit, with explicit wording. A **404** says the entry was deleted. Use the existing `domain/errors.ts` / `presentation/errorMessages.ts` pattern (it already handles the skill-name 409). Never retry automatically.
- **Always replace the stored `version` with the one in each PUT response** (every successful PUT bumps it, even a no-op).
- Ships before T-113 is deployed: the live server ignores an unknown `version` (Spring Boot's default), and its GETs don't return one yet, so the admin sends none. Confirm in a test that `undefined` is omitted from the JSON body.
- **Budget:** merge and Drone-deploy this window.

## Why

Split out of [T-113](T-113-optimistic-locking-lost-update.md) at its H1 (2026-10-04). The contract (T-046) makes `version` optional on PUT; the admin is the only writer, so it must **always** send it to get the protection. Today `sectionHttpRepository.update` sends the form-built `*Input`, which drops any field the form doesn't own.

## Scope

- The domain types gain `version`; list/get keep it; update sends the row's `version` with the input (person and the three sections).
- A 409 shows a clear "this entry changed elsewhere — reload" notice and doesn't lose the user's form state silently. Tests for both.
- Shippable before the domain change: the current server ignores an unknown `version` field (Jackson's default in Spring Boot); confirm it rather than assume.

## Acceptance criteria

- [ ] Every PUT for person and the three sections carries the row's `version`.
- [ ] A 409 renders the notice; tests cover both paths.
- [ ] Gates green; Drone green; deployed.
