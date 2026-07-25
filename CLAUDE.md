# CLAUDE.md

This file guides Claude Code when working in the **cv-project meta repo**. Each sibling product repo has its own CLAUDE.md with stack-specific commands — read that one before working there.

## What this workspace is

"Currículum Interactivo": an interactive CV system built as a **multi-repo** demo (seven product repos + infra), each with its own git history, CI system, and deploy pipeline — deliberately *not* a monorepo. This directory is the meta repo (orchestration only, no app code); its eight sibling repos (seven products + `cv-infra`) live as subdirectories on disk but are **independent git repositories**, not submodules — a `git` command here never sees their files.

| Repo | Layer | Stack | CI |
|---|---|---|---|
| `cv-database` | Data | MySQL 8 + Flyway 10 | Jenkins |
| `cv-domain-service` | Domain API (source of truth) | Java 17, Spring Boot 3 | Jenkins |
| `cv-bff-node` | BFF for the public site | Node 20 + Express | GitHub Actions |
| `cv-admin-react` | Admin CRUD UI | React 18 + Vite | DroneCI |
| `cv-public-vanilla` | Public landing | Vanilla JS + Vite | GitHub Actions |
| `cv-public-react` | Public site (optimized, ISR) | Next.js 14, React 18, TS | Vercel |
| `cv-observability` | Metrics stack | Prometheus + Grafana | GitHub Actions |
| `cv-infra` | IaC | Terraform, AWS Free Tier | — |

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

## Environment gotchas (this machine)

- Toolchains are user-space in `~/.local`: `mvn` is a wrapper pinning Temurin JDK 17 (system `java` is a bare JRE 25 — don't use it directly), Node 20 via nvm symlinks, Terraform 1.9.8.
- Flyway 10 bundles the MariaDB driver: MySQL 8 JDBC URLs **must** carry `?allowPublicKeyRetrieval=true` or migrate hangs retrying silently.
- Prometheus/anything in Docker reaching the host needs `extra_hosts: ["host.docker.internal:host-gateway"]` (Linux).

## Conventions across repos

- TDD everywhere; a PR without tests for its code path is incomplete.
- Different CI per repo is a **feature** of the demo, not drift to fix.
- AWS resources stay within Free Tier limits.
- Dev seed data lives only in `cv-database/sql/dev-seeds/` (Flyway callback), never in versioned migrations.
