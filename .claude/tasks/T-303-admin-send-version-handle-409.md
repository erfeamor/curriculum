---
id: T-303
title: "Admin: keep each row's `version`, send it on PUT, and handle a 409 (changed elsewhere — reload)"
repo: cv-admin-react
status: todo
owner:
branch: feat/version-409
pr:
depends_on: [T-046]
risk: normal
security_review: false
---

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
