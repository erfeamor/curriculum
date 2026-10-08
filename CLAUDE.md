# CLAUDE.md

This file guides Claude Code when working in the **cv-project meta repo**. Each sibling product repo has its own CLAUDE.md with stack-specific commands — read that one before working there.

## What this workspace is

"Currículum Interactivo": an interactive CV system built as a **multi-repo** demo (seven product repos + infra), each with its own git history, CI system, and deploy pipeline — deliberately *not* a monorepo. This directory is the meta repo (orchestration only, no app code); its eight sibling repos (seven products + `cv-infra`) live as subdirectories on disk but are **independent git repositories**, not submodules — a `git` command here never sees their files.

| Repo | Layer | Stack | CI |
|---|---|---|---|
| `cv-database` | Data | MySQL 8.4 + Flyway 13.7.0 (production still on 10 until T-014) | Jenkins |
| `cv-domain-service` | Domain API (source of truth) | Java 17, Spring Boot 3 | Jenkins |
| `cv-bff-node` | BFF for the public site | Node 20 + Express + TypeScript | GitHub Actions |
| `cv-admin-react` | Admin CRUD UI | React 18 + Vite | DroneCI |
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

**Switching an existing `cv-dev-mysql-data` volume between MySQL versions.** `docker-compose.dev.yml` pins `mysql:8.4`, matching production (`cv-infra/templates/domain-service-user-data.sh`) and the Jenkins migration gate in `cv-database`. The two directions are **not** symmetric (verified on this stack, 2026-08-22):

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

## Environment gotchas (this machine)

- Toolchains are user-space in `~/.local`: `mvn` is a wrapper pinning Temurin JDK 17 (system `java` is a bare JRE 25 — don't use it directly), Node 20 via nvm symlinks, Terraform 1.9.8.
- Flyway bundles the MariaDB driver (both 10.22.0 and 13.7.0 ship only `mariadb-java-client-2.7.14`, verified 2026-09-23 in T-155): MySQL 8 JDBC URLs **must** carry `?allowPublicKeyRetrieval=true` or migrate hangs retrying silently.
- Prometheus/anything in Docker reaching the host needs `extra_hosts: ["host.docker.internal:host-gateway"]` (Linux).

## Conventions across repos

- TDD everywhere; a PR without tests for its code path is incomplete.
- Different CI per repo is a **feature** of the demo, not drift to fix.
- AWS cost: this account is on the **Paid plan since 2026-09-29** (upgraded from the post-July-2025 Free Tier it was created on, 2026-07-12). **The Free plan's protection against charges beyond the credits is gone: anything the credits don't cover bills the card.** The budget alarms (T-011, two budgets, SNS to a confirmed email) are the only guard, so keep them working. There is no free EC2 allowance; every instance-hour bills and is paid from the remaining signup/activity credits first (net invoice $0 so far). **Run rate ~$0.51/day ≈ $15.5/month, measured 2026-10-08** (T-051, on 10-06, the first full day after the EIP release and Graviton; it was ~$0.69/day in T-020's model). **Fixed ~$0.47/day:** app host `t4g.micro` $0.226, EBS $0.108, the app host's EIP $0.120, the Route 53 zone ~$0.016, and ~$0.005 other (Cognito machine tokens, ECR storage). **The CI host is the variable part:** about $0.04/day typical, because the reaper stops it except during builds; left up all day it adds about $0.7 (its `t3.small` hours plus its public IPv4), for ~$1.2/day ≈ $35/month. **$116.15 of credits remain (2026-10-08; all five $20 credit activities are done, grant $200)**, enough until about late May 2027 at this rate. That is before they expire on 2027-07-12, so after that the bill (~$15–16/month) is real money. Keep resources modest because every dollar past the credits is paid, not because a class is "free". **The endgame decision is T-012, the model T-020.** See cv-infra/CLAUDE.md for the full cost model.
- Dev seed data lives only in `cv-database/sql/dev-seeds/` (Flyway callback), never in versioned migrations.
