# CLAUDE.md

This file guides Claude Code when working in the **cv-project meta repo**. Each sibling product repo has its own CLAUDE.md with stack-specific commands — read that one before working there.

## What this workspace is

"Currículum Interactivo": an interactive CV system built as a **multi-repo** demo (seven product repos + infra), each with its own git history, CI system, and deploy pipeline — deliberately *not* a monorepo. This directory is the meta repo (orchestration only, no app code); its eight sibling repos (seven products + `cv-infra`) live as subdirectories on disk but are **independent git repositories**, not submodules — a `git` command here never sees their files.

| Repo | Layer | Stack | CI |
|---|---|---|---|
| `cv-database` | Data | MySQL 8 + Flyway 10 | Jenkins |
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
./scripts/lint-all.sh              # lint every repo per its own stack
./scripts/test-all.sh              # every repo's test suite
./scripts/build-all.sh             # every repo's build
docker compose -f docker-compose.dev.yml up --build   # full local stack
curl localhost:3000/api/v1/people/1                    # E2E smoke: BFF → Java → MySQL
```

Dev stack ports: BFF :3000, domain API :8080 (Swagger at `/swagger-ui.html`), MySQL :3306, Prometheus :9090, Grafana :3001 (admin/admin). Frontends run separately: `npm run dev` in their repos (:5173 admin, :4173 public).

**Switching an existing `cv-dev-mysql-data` volume between MySQL versions — wipe it.** `docker-compose.dev.yml` pins `mysql:8.4`, matching production (`cv-infra/templates/domain-service-user-data.sh`) and the Jenkins migration gate in `cv-database`. A `cv-dev-mysql-data` volume left over from an older `8.0` pin holds an 8.0-formatted datadir. The supported route when the pin moves is to throw the volume away:

```bash
docker compose -f docker-compose.dev.yml down -v   # discard the old datadir (all services)
docker compose -f docker-compose.dev.yml up --build   # fresh datadir; Flyway + the dev-seed callback regenerate everything
```

Nothing is lost: dev seed data regenerates via the Flyway `afterMigrate` callback (`cv-database/sql/dev-seeds/`), never hand-maintained.

Why wiping is the rule rather than a nicety — the two directions are **not** symmetric (verified on this stack, 2026-08-22):

- **8.0 → 8.4 succeeds silently.** The server performs an in-place upgrade on first start (`Data dictionary upgrading from version '80023' to '80300'`, `Server upgrade from '80046' to '80411' completed`) and comes up healthy. Convenient, but it is a one-way door: the volume is now 8.4-formatted.
- **8.4 → 8.0 fails hard and is not recoverable in place.** Re-pinning to `8.0` after `8.4` has touched the volume aborts startup with `[ERROR] [MY-014061] [InnoDB] Invalid MySQL server downgrade: Cannot downgrade from 80411 to 80046. Downgrade is only permitted between patch releases.` The container exits 1 and never reports healthy. The fix is `docker compose down -v`.

## Environment gotchas (this machine)

- Toolchains are user-space in `~/.local`: `mvn` is a wrapper pinning Temurin JDK 17 (system `java` is a bare JRE 25 — don't use it directly), Node 20 via nvm symlinks, Terraform 1.9.8.
- Flyway 10 bundles the MariaDB driver: MySQL 8 JDBC URLs **must** carry `?allowPublicKeyRetrieval=true` or migrate hangs retrying silently.
- Prometheus/anything in Docker reaching the host needs `extra_hosts: ["host.docker.internal:host-gateway"]` (Linux).

## Conventions across repos

- TDD everywhere; a PR without tests for its code path is incomplete.
- Different CI per repo is a **feature** of the demo, not drift to fix.
- AWS cost: this account is on AWS's **post-July-2025 Free Tier** (created 2026-07-12) — a finite pot of credits and a 6-month window, **not** the legacy 12-month/750-hour allowance. There is no free EC2 allowance here; every instance-hour bills and is paid from credits (net invoice $0). **Run rate ~$0.68/day ≈ $21/month, measured 2026-08-19** (T-020) — this assumes `cv-project-domain-service` `t3.micro` running and the `cv-project-drone` CI host **stopped except during builds**. Starting that CI host and leaving it up takes the rate to ~$1.23/day ≈ $37/month and moves the cliff forward by ~8 weeks, so it is a runway decision, not a convenience one. **$111.08 of credits remain and the Free-plan window closes 2027-01-12** — at the current rate the *window* binds first. Keep resources modest because the credits are finite and expire, not because a class is "free" — **runway and cliff tracked in T-010/T-012, the model itself in T-020**. See cv-infra/CLAUDE.md for the full cost model.
- Dev seed data lives only in `cv-database/sql/dev-seeds/` (Flyway callback), never in versioned migrations.
