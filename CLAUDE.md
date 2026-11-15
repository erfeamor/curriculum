# CLAUDE.md

This file guides Claude Code when working in the **cv-project meta repo**. Each sibling product repo has its own CLAUDE.md with stack-specific commands — read that one before working there.

## What this workspace is

"Currículum Interactivo": an interactive CV system built as a **multi-repo** demo (seven product repos + infra), each with its own git history, CI system, and deploy pipeline — deliberately *not* a monorepo. This directory is the meta repo (orchestration only, no app code); its eight sibling repos (seven products + `cv-infra`) live as subdirectories on disk but are **independent git repositories**, not submodules — a `git` command here never sees their files.

| Repo | Layer | Stack | CI |
|---|---|---|---|
| `cv-database` | Data | MySQL 8.4 + Flyway 13.7.0 (production still on 10 until T-014) | GitHub Actions |
| `cv-domain-service` | Domain API (source of truth) | Java 17, Spring Boot 3 | GitHub Actions |
| `cv-bff-node` | BFF for the public site | Node 20 + Express + TypeScript | GitHub Actions |
| `cv-admin-react` | Admin CRUD UI | React 18 + Vite | GitHub Actions |
| `cv-public-vanilla` | Public landing | Vanilla JS + Vite | GitHub Actions |
| `cv-public-react` | Public site (optimized, ISR) | Next.js 14, React 18, TS | Vercel |
| `cv-observability` | Metrics stack | Prometheus + Grafana | GitHub Actions |
| `cv-infra` | IaC | Terraform, AWS (credit-funded) | — |

Flow: public sites (cv-public-vanilla, and cv-public-react via ISR) → BFF → domain service → MySQL. cv-public-react is runtime-decoupled from the domain service: it only fetches the BFF's aggregate endpoint server-side and revalidates in the background. Admin UI → domain service directly. Auth: AWS Cognito JWTs, with a shared `AUTH_ENABLED` toggle (Java defaults **on**, BFF defaults **off**) so local stacks run without a user pool.

## Git workflow — non-negotiable

**`master` is protected in every repo (including this one). Never commit to it. Never push it.** Every change: feature branch → push → PR → merge after CI. Branch names: `feat/…`, `fix/…`, `docs/…`, `chore/…`. GitHub org is `erfeamor`; use `gh` for PRs.

## Task board for agent teams

`.claude/tasks/` holds the shared task board — **read `.claude/tasks/README.md` before picking up any work**, claim tasks by editing their frontmatter, and honor `depends_on`. API work must match `docs/api-contract.md` exactly.

## Commands (from this directory)

```bash
python3 scripts/board-check.py     # validate the task board (read-only; see .claude/tasks/README.md)
./scripts/lint-all.sh              # lint every repo per its own stack
./scripts/test-all.sh              # every repo's test suite
./scripts/build-all.sh             # every repo's build
docker compose -f docker-compose.dev.yml up --build   # full local stack
curl localhost:3000/bff/api/v1/people/1                # E2E smoke: BFF → Java → MySQL
```

Dev stack ports: BFF :3000, domain API :8080 (Swagger at `/swagger-ui.html`), MySQL :3306, Prometheus :9090, Grafana :3001 (admin/admin). Frontends run separately: `npm run dev` in their repos (:5173 admin, :4173 public).

**Switching an existing `cv-dev-mysql-data` volume between MySQL versions.** `docker-compose.dev.yml` pins `mysql:8.4`, matching production (`cv-infra/templates/domain-service-provision.sh`) and the migration gate in `cv-database`. The two directions are **not** symmetric (verified on this stack, 2026-08-22):

- **8.0 → 8.4 succeeds silently.** The server performs an in-place upgrade on first start (`Data dictionary upgrading from version '80023' to '80300'`, `Server upgrade from '80046' to '80411' completed`) and comes up healthy. The datadir survives the upgrade — hand-authored rows (including anything written through `cv-admin-react`) are preserved. A wipe is **optional** going this direction, not required.
- **8.4 → 8.0 fails hard and is not recoverable in place.** Re-pinning to `8.0` after `8.4` has touched the volume aborts startup with `[ERROR] [MY-014061] [InnoDB] Invalid MySQL server downgrade: Cannot downgrade from 80411 to 80046. Downgrade is only permitted between patch releases.` The container exits 1 and never reports healthy. A wipe is **required** to recover going this direction.

For a clean slate — required going backward, optional going forward (e.g. to shed local cruft) — `down -v` is the fastest route, but it is not free:

```bash
# `down -v` drops EVERY named volume in this project, including
# cv-dev-grafana-data — UI-created dashboards live only in that volume's
# grafana.db (cv-observability/grafana/provisioning/dashboards/ ships
# dashboards.yml only, no dashboard JSON), so they are not recoverable
# from the repo.
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up --build
```

Only Flyway's seed rows regenerate automatically (`cv-database/sql/dev-seeds/`, the `afterMigrate` callback). Anything written since — through `cv-admin-react`, or a Grafana dashboard built in the UI — is destroyed along with the version-mismatched datadir, not preserved.

To touch only the MySQL datadir and leave Grafana (and everything else in the stack) alone:

```bash
docker compose -f docker-compose.dev.yml down
docker volume rm curriculum_cv-dev-mysql-data   # real name carries the
  # compose project prefix (this checkout's directory name by default) —
  # confirm with `docker volume ls`; the bare `cv-dev-mysql-data` name
  # above is not what Docker stores it under
```

## Releases (T-504)

A release is a tag of the same name (`M2`, `M3`, …) in all nine repos. `releases/<name>.json` records each sibling's commit, and the meta repo's tag is the commit that adds that file, so **the meta repo at `M2` defines `M2` everywhere**. A GitHub tag ruleset, "Protect release tags", in every repo blocks updating or deleting `refs/tags/M*` with no bypass, admins included. The only way back from a wrong tag is deliberate: an admin disables or deletes that repo's ruleset, fixes the tag, and re-runs `scripts/release-protect.sh`.

```bash
git checkout M2 && scripts/release-checkout.sh M2   # every sibling at its M2 tag (detached); refuses dirty repos, moves none
scripts/release-verify.sh M2                        # read-only: tags local + on GitHub, on the manifest's commits, working copies on them
```

Cutting the next one:
1. `scripts/release-manifest.sh M3` on a branch (it fetches each sibling's `origin/master`; never edit the JSON by hand).
2. Merge it through a PR.
3. On the meta repo's updated `master`, run `scripts/release-tag.sh M3`. It checks everything before tagging anything, and a re-run is a no-op.
4. Run `scripts/release-protect.sh` only if the ruleset itself changes. It's idempotent.

Tag pushes deploy nothing and build nothing: Actions and Vercel only act on `master`. (The CI host, its doorbell and its Jenkins/Drone triggers are gone since T-064.) `scripts/test_release.py` covers all five scripts offline.

## Environment gotchas (this machine)

- Toolchains are user-space in `~/.local`: `mvn` is a wrapper pinning Temurin JDK 17 (system `java` is a bare JRE 25 — don't use it directly), Node 20 via nvm symlinks, Terraform 1.9.8.
- Flyway bundles the MariaDB driver (both 10.22.0 and 13.7.0 ship only `mariadb-java-client-2.7.14`, verified 2026-09-23 in T-155): MySQL 8 JDBC URLs **must** carry `?allowPublicKeyRetrieval=true` or migrate hangs retrying silently.
- Prometheus/anything in Docker reaching the host needs `extra_hosts: ["host.docker.internal:host-gateway"]` (Linux).

## Conventions across repos

- TDD everywhere; a PR without tests for its code path is incomplete.
- **Cost first (M3, decided 2026-11-07):** money comes before technical simplicity. CI is **GitHub Actions in every repo** (Vercel for cv-public-react) and the CI host (Jenkins, Drone, the doorbell and reaper Lambdas) was deleted on 2026-11-09 (T-064, after T-117, T-159 and T-305). "Different CI per repo" is no longer a goal.
- AWS cost: this account is on the **Paid plan since 2026-09-29** (upgraded from the post-July-2025 Free Tier it was created on, 2026-07-12). **The Free plan's protection against charges beyond the credits is gone: anything the credits don't cover bills the card.** The budget alarms (T-011, two budgets, SNS to a confirmed email) are the only guard, so keep them working. There is no free EC2 allowance; every instance-hour bills and is paid from the remaining signup/activity credits first (net invoice $0 so far). **Run rate $0.287/day, measured 2026-11-15 (T-069)**: flat for each full day 2026-11-10..13, after M3's cuts (the CI host deleted in T-064, the app host's Elastic IP released in T-068, the MySQL data volume shrunk to 2 GB in T-066). **It is made of** the app host `t4g.micro` $0.226 (on demand; T-065 dropped Spot), EBS $0.056 (8 GB root + 2 GB data + the old detached 8 GB volume until T-069 deletes it), S3 storage $0.003 and Cognito machine tokens $0.002; the Route 53 zone ($0.50/month) posts on the 1st. **Once the old volume is gone: ~$0.28/day ≈ $8.5/month**, plus the domain renewal (~$15/year, billed separately). That is down from ~$0.51/day (~$15.5/month) at M2 (T-051). **$99.47 of credits remained on 2026-11-15** (grant $200, all five $20 activities done); at this rate only ~$67 is spent by their expiry on **2027-07-12**, so ~$32 of credits expire unused, and from then on the bill is real money (~$8.5/month). Keep resources modest because every dollar past the credits is paid, not because a class is "free". **The endgame decision is T-012, the model T-020.** See cv-infra/CLAUDE.md for the full cost model.
- Dev seed data lives only in `cv-database/sql/dev-seeds/` (Flyway callback), never in versioned migrations.
