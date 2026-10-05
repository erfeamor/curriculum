---
id: T-303
title: "Admin: keep each row's `version`, send it on PUT, and handle a 409 (changed elsewhere — reload)"
repo: cv-admin-react
status: done
owner: tech-product-owner
branch: feat/version-409
pr: https://github.com/erfeamor/cv-admin-react/pull/17
depends_on: [T-046]
risk: normal
security_review: false
checkpoint:
  stage: done   # merged 22ea9a4 (squash of cv-admin-react#17), 2026-10-05 — H2 accepted; Drone deployed /admin/ (bundle carries the conflict UI)
  repo: cv-admin-react
  branch: feat/version-409
  worktree: none
  commit: 22ea9a4
  pr: https://github.com/erfeamor/cv-admin-react/pull/17
  developer: fullstack-developer
  reviewers: [code-review]
  risk: normal
  security_review: false
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a
  updated: 2026-10-05T00:30:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 94710
    spawns: 1   # fullstack-developer (fresh)
    status: ok   # human-reported /usage 40–75%
    checked: 2026-10-05T00:30:00+02:00
---

## H1 — decided by the human, 2026-10-05

- **On a 409:** show "This entry was changed elsewhere" by the form, **keep the user's edits**, and offer a **Reload** button that fetches the latest (with its `version`) and discards the stale edit, with explicit wording. A **404** says the entry was deleted. Use the existing `domain/errors.ts` / `presentation/errorMessages.ts` pattern (it already handles the skill-name 409). Never retry automatically.
- **Always replace the stored `version` with the one in each PUT response** (every successful PUT bumps it, even a no-op).
- Ships before T-113 is deployed: the live server ignores an unknown `version` (Spring Boot's default), and its GETs don't return one yet, so the admin sends none. Confirm in a test that `undefined` is omitted from the JSON body.
- **Budget:** merge and Drone-deploy this window.

## Implement + review — 2026-10-05 (720beaa, cv-admin-react#17)

- Developer (fresh fullstack-developer, ~95k tokens). `version?` on the four domain types; `*Input` omits it (POST never sends one). **The PUT sends the version captured when the edit started** (better than the brief's "the row's version at save": a mid-edit list refresh can't silently overwrite). `withVersion` adds the key only when known. After a PUT the store keeps the response row (the new version). On 409, `ConflictAlert` keeps the edits and offers "Reload and discard my edits" (sections via `sectionStore.reload`, person via `selectPerson`). A 404 drops the row or person, with the existing "no longer exists" wording (kept over the brief's literal text, for consistency). `isChangedElsewhere` = update + 409 only, so the skill-name 409 (a create) stays distinct.
- Red first (23 tests / 8 suites) → 274/274. Driver-verified: lint, typecheck, 274 tests, build; **Drone green** (push + pr).
- **Review round 1: clean.**

## Why

Split out of [T-113](T-113-optimistic-locking-lost-update.md) at its H1 (2026-10-04). The contract (T-046) makes `version` optional on PUT; the admin is the only writer, so it must **always** send it to get the protection. Today `sectionHttpRepository.update` sends the form-built `*Input`, which drops any field the form doesn't own.

## Scope

- The domain types gain `version`; list/get keep it; update sends the row's `version` with the input (person and the three sections).
- A 409 shows a clear "this entry changed elsewhere — reload" notice and doesn't lose the user's form state silently. Tests for both.
- Shippable before the domain change: the current server ignores an unknown `version` field (Jackson's default in Spring Boot); confirm it rather than assume.

## Acceptance criteria

- [x] Every PUT for person and the three sections carries the row's `version`.
- [x] A 409 renders the notice; tests cover both paths.
- [x] Gates green; Drone green; deployed. *(2026-10-05: the live `/admin/` bundle `index-CpV62ryg.js` carries the conflict UI; the vanilla root files are untouched.)*
