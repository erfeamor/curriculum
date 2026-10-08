---
id: T-504
title: "Tag `M2` in all 9 repos, pinned by a manifest in the meta repo, with checkout/verify scripts and immutable tags"
repo: cv-project (meta) + all eight sibling repos (tags and rulesets only)
status: todo
owner:
branch: feat/release-m2-tag
pr:
depends_on: [T-502]   # T-502 (final docs + diagram) is the roadmap's last item; M2 is tagged after it merges
risk: normal   # new tooling, tags pushed to 9 repos, GitHub rulesets: no AWS or app changes
security_review: false
---

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

- [ ] `M2` exists in all 9 repos on GitHub, each on the commit the manifest records (the meta repo's on the manifest's own commit).
- [ ] `release-verify.sh M2` passes on a fresh clone set. After a sibling is checked out elsewhere it fails and names that repo.
- [ ] `release-checkout.sh M2` restores every sibling to its `M2` tag, and refuses a sibling with uncommitted changes.
- [ ] Moving or deleting `M2` is rejected by GitHub in every repo (tried once and rejected).
- [ ] No deploy and no CI-host wake caused by the tag pushes (or, if the doorbell wakes it, recorded and the doorbell change filed).
