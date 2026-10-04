---
id: T-046
title: "Contract: an optional `version` on person and section resources, and a 409 for a stale PUT"
repo: cv-project (meta)
status: done
owner: tech-product-owner
branch: docs/contract-version-409
pr: https://github.com/erfeamor/curriculum/pull/107   # merged 1318822, 2026-10-04 (human sign-off)
depends_on: []
risk: normal
security_review: false   # contract text only
---

## Why

Split out of [T-113](T-113-optimistic-locking-lost-update.md) at its H1 (2026-10-04). Board rule 4: API work matches `docs/api-contract.md` exactly, so the contract changes first.

## H1 — decided by the human, 2026-10-04 (at T-113's H1)

- **Transport: a body field `version`** (an integer), returned on every GET/POST/PUT of **person, experience, education and project**. Not `If-Match`: collection GETs can't carry per-item ETags.
- **Optional on PUT:** when present and not equal to the stored version → **409** (the contract defines the body); when absent → the write wins, as today. The admin always sends it ([T-303](T-303-admin-send-version-handle-409.md)). It can be tightened to required later.
- **The BFF's public payloads never carry `version`** (its normalizers are allowlists since T-205; state it in the BFF section).
- Person-skill assignments are unchanged.

## Acceptance criteria

- [x] `docs/api-contract.md`: `version` in the person and the three section shapes; PUT semantics (optional, mismatch → 409, absent → last write wins); the 409 body in the contract's existing error style; design rule 4's status list gains 409 for these PUTs; the public BFF payloads exclude it; an amendment line in the header.
- [x] Merged before T-113 and T-303 start.
