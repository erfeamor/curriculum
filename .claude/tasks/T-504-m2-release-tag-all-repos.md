---
id: T-504
title: "Tag `M2` in all 9 repos, pinned by a manifest in the meta repo, with checkout/verify scripts and immutable tags"
repo: cv-project (meta) + all eight sibling repos (tags and rulesets only)
status: done
owner: tech-product-owner
branch: feat/release-m2-tag
pr: https://github.com/erfeamor/curriculum/pull/125
depends_on: [T-502]   # T-502 (final docs + diagram) is the roadmap's last item; M2 is tagged after it merges
risk: normal   # new tooling, tags pushed to 9 repos, GitHub rulesets: no AWS or app changes
security_review: false
---

## ✅ DONE 2026-11-04: `M2` is tagged in all 9 repos ([curriculum#125](https://github.com/erfeamor/curriculum/pull/125))

- **Rulesets:** `scripts/release-protect.sh` created "Protect release tags" in all 9 repos. Read back from GitHub, all 9 are identical: active, `refs/tags/M*`, rules `update` + `deletion`, 0 bypass actors, `current_user_can_bypass: never`.
- **Tags:** `scripts/release-tag.sh M2` (14:42Z) tagged the siblings at the manifest's commits and the meta repo at `df3b41d` (#125's merge, the commit that adds `releases/M2.json`). Each sibling's tag is its `origin/master` from 2026-11-03, unchanged at tagging time.
- **Verify:** a fresh HTTPS clone set (`git clone --branch M2` + `./clone-all.sh` + `release-checkout.sh M2`) verified with `all 9 repos at M2`. With one sibling moved to a new commit, verify exited 1 naming `cv-public-react` only. (`clone --branch` on an annotated tag prints a harmless "is not a commit" warning.)
- **Immutability:** tried live on **cv-observability**, through SSH as a repo admin. Both a force-move and a delete were rejected with `GH013` ("Cannot update this protected ref", "Cannot delete this tag"), and the tag was unchanged. The same attempts on the other 8 repos were **not run**, because the session's auto-mode classifier blocks destructive git pushes. The human accepted the identical read-back above as the evidence for those 8.
- **Side effects:** none deployed. There were 0 Actions runs in any repo after tagging, and Vercel's last deployment is still `2c785cb` (10-04). The doorbell woke the CI host **once**, at 14:43:31Z, on the cv-database tag push, as accepted at H1. Jenkins and Drone build branches only, so the reaper stops it on idle. [T-059](T-059-doorbell-skip-tag-pushes.md) removes the wake before `M3`.

## H1 — approved 2026-11-03

- **CI wake:** accepted. The tag pushes to cv-admin-react, cv-database and cv-domain-service wake the CI host once through the doorbell; record it. The doorbell fix is filed as [T-059](T-059-doorbell-skip-tag-pushes.md).
- **Verify wiring:** standalone, run by hand and documented in CLAUDE.md. No `post-checkout` hook, and not wired into `test-all.sh` or `board-check` (verify fails whenever a sibling isn't on its tag, which is normal day to day). The scripts' offline tests (`scripts/test_release.py`) do run in `test-all.sh`.
- **Lock scope:** one ruleset per repo on `refs/tags/M*`: blocks update and deletion, no bypass, creation allowed.
- **Stage-0 facts** (checked 2026-11-03): Drone's `trigger.event` is `[push, pull_request]` (a tag push is a `tag` event, so no build); both Jenkins jobs use `gitHubBranchDiscovery` only; every GitHub Actions workflow is master-only; no repo had tags or a tag ruleset.
- **Implementation:** the driver implements (meta repo tooling), plus `release-manifest.sh` and `release-tag.sh` so that the manifest and tags are generated, never typed. `release-protect.sh` applies the ruleset idempotently.


## Review round 1 (2026-11-03)

`/code-review` (10 findings) and the infrastructure-engineer lens (no blockers, 3 should-fix) agreed on the substance. All accepted and fixed test-first:
- A manifest parsed inside `< <(…)` failed silently. It is now captured with `|| die` and must name exactly the eight siblings with full commit ids.
- `ls-remote` failures read as "no tag". They are now fatal in tag, reported as `can't read origin` in verify, and refused in checkout.
- Checkout's pre-check now refuses untracked files and compares every local tag with origin's.
- The meta tag now goes on the commit that **added** the manifest, not a later `master` HEAD, and is refused if the manifest changed after it was added.
- `release-protect.sh` lists only the repo's own rulesets (`includes_parents=false`), across every page.
- Added tests: a push rejected midway leaves the meta repo untagged and a re-run completes; a sibling that isn't cloned is refused.

38 release tests. Every guard is mutation-checked except `release-tag.sh`'s "can't read origin", which is redundant behind pass 1's fetch and kept as defence in depth.

## Why

Requested by the human, 2026-10-08. The demo is a deliberate multi-repo, **not** submodules, so a tag in one repo knows nothing about the others. The human wants an `M2` tag on every repo **and** a mechanism such that when the meta repo is at `M2`, every other repo is at its `M2` too.

**When:** right after [T-502](T-502-final-docs-architecture-diagram.md) merges. T-501 verified the milestone, and T-502 closes the roadmap's last item, so `M2` marks each repo's `master` at that point.

## Design (proposed 2026-10-08; confirm at H1)

1. **A manifest:** `releases/M2.json` in the meta repo, mapping each of the 8 siblings to the exact commit its `M2` tag points at (plus the GitHub repo). The meta repo's own `M2` tag is the commit that contains this file, so the meta repo at `M2` defines what `M2` means everywhere.
2. **`scripts/release-checkout.sh <name>`:** puts every sibling at its `<name>` tag (detached HEAD). It refuses a sibling with uncommitted changes, a missing tag, or a tag whose commit differs from the manifest. It never touches `master`.
3. **`scripts/release-verify.sh <name>`** (read-only) checks, for every repo:
   - the tag exists locally **and** on GitHub;
   - it points at the manifest's commit;
   - and reports whether the working copy is currently on it.

   It exits non-zero on any mismatch. Wire it into `board-check` and/or `test-all.sh` (an H1 decision).
4. **Immutable tags:** a GitHub tag ruleset in each of the 9 repos that blocks updating and deleting `M2` (or the `M*` release pattern, an H1 decision), applied with `gh api`. Without it, the "ensures" part is only a convention.
5. **Optional (H1):** a `post-checkout` hook, installed by a script because hooks aren't versioned, that runs the verify step, or the checkout, when the meta repo's HEAD lands on a release tag.
6. **Docs:** CLAUDE.md (meta) gets a short "Releases" section on how to reproduce M2 (`git checkout M2 && scripts/release-checkout.sh M2`), and the README roadmap mentions the tag.

## Watch-outs (stage 0)

- **Tag pushes and CI:** every GitHub Actions workflow triggers only on `branches: [master]`, and Vercel deploys branches, so tag pushes deploy nothing there. But a tag push to cv-admin-react, cv-database or cv-domain-service sends a GitHub `push` event to the **doorbell**, which may wake the CI host. **Drone** may also build a tag event: confirm that cv-admin-react's deploy step (`when: branch: [master]`) can't fire on a tag event before pushing. Consider making the doorbell skip `refs/tags/*` (a small cv-infra change, its own task if needed).
- Tag after T-502's merge, **from each repo's up-to-date `origin/master`**, and generate the manifest from the same commits, never by hand.
- `master` is protected everywhere. The tags are separate refs, but the ruleset must not interfere with branch rules (`--admin` merges keep working).

## Acceptance criteria

- [x] `M2` exists in all 9 repos on GitHub, each on the commit the manifest records (the meta repo's on the manifest's own commit).
- [x] `release-verify.sh M2` passes on a fresh clone set. After a sibling is checked out elsewhere it fails and names that repo.
- [x] `release-checkout.sh M2` restores every sibling to its `M2` tag, and refuses a sibling with uncommitted changes.
- [x] Moving or deleting `M2` is rejected by GitHub in every repo. Tried live on cv-observability; the other 8 are evidenced by the ruleset read back from each, as accepted by the human 2026-11-04.
- [x] No deploy and no CI-host wake caused by the tag pushes (or, if the doorbell wakes it, recorded and the doorbell change filed).
