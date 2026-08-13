---
id: T-015
title: Correct the meta docs that claim the BFF and public site are deployed
repo: cv-project (meta)
status: todo
owner:
branch: docs/reflect-deployed-bff
pr:
depends_on: [T-014, T-403]
risk: trivial
security_review: false
---

## Why this exists

The reason the BFF deployment gap went unfiled for months is that **every document describing it says it is done**. The `cv-infra`-side claims are corrected inside T-014 (same repo, same PR). What remains are the meta repo's:

| Location | Claim | Reality |
|---|---|---|
| `README.md` § Roadmap | *"[x] Create the Node BFF"* | created, never deployed — the checkbox is true but reads as shipped |
| `README.md` § Roadmap | *"[x] Deploy AWS infrastructure — … S3+CloudFront frontends …"* | only `cv-admin-react` is published; the public site prefix is empty |
| `README.md` § Backlog | *"frontends deploy via DroneCI, backend services still deployed manually"* | accurate for admin + domain service; silent on the BFF and public-vanilla having **no** deploy path at all |
| `docs/architecture.md:23-24` | `cv-public-vanilla → cv-bff-node → …` | the runtime flow diagram describes a path that does not exist in AWS |

None of these is wrong about *intent*. All of them are wrong about *state*, and stating intent in the present tense is exactly what produced this class of defect twice now (see also T-010, where `CLAUDE.md` asserted a Free Tier model the account was not on).

This is the close-out task: it lands **after** T-014 and T-403 make the claims true, and its job is to make sure they are true rather than to keep asserting them.

## Scope

- Re-read each row above against what is actually deployed after T-014 and T-403 merge, and correct anything still aspirational.
- Where a document describes intended architecture rather than deployed state, say which it is. `docs/architecture.md` is allowed to describe the target design — it just must not read as a deployment inventory.
- Update the roadmap/backlog to reflect what the T-013…T-403 chain actually delivered, including anything deliberately left undone (e.g. T-203 if the CI deploy stage was deferred, `cv-domain-service`'s still-manual deploy).
- Add the BFF and public-vanilla to whatever the README says about deploy pipelines, so the next reader can tell deployed from merely built.

## Acceptance criteria

- [ ] Every claim in the table above matches the live account at the time of the PR.
- [ ] Anything deferred out of the T-013…T-403 chain is named in the backlog with its task ID, not dropped.
- [ ] `docs/architecture.md` distinguishes target design from deployed state where it matters.
- [ ] No new claim is added that was not verified against the account.

## Definition of done

PR open against `master` from `docs/reflect-deployed-bff`, merged.

## dev-loop notes

- **Developer:** `tech-product-owner` (meta-repo docs). **Reviewer:** `/code-review` only — `risk: trivial` per adapter §5 (docs/markdown only), so H1/H2 are one-line confirms.
- **A1 will re-check the trivial flag** (§5): if the diff exceeds 150 lines or 5 files, or touches a non-doc file, `trivial` is revoked and the gates tighten. Docs-only here, so it should hold.
- **Verify, do not transcribe.** The one thing that makes this task worth a PR is checking each claim against the live account rather than against the merged task files. Copying T-014's acceptance criteria into the README would reproduce the original defect in a new place.
