🌐 **Language:** [English](README.md) | [Español](README.es.md)

---

# 📘 Project: Interactive Résumé — Full-Stack Technology Demo

This project is a **comprehensive technology demo** designed to showcase mastery of multiple technologies, architectures, patterns, and modern development practices.
The system is composed of several independent layers, each living in its own repository and deployed through its own pipeline (GitHub Actions everywhere, plus Vercel for the Next.js site).

---

## 🏗️ General Architecture

The project is organized into **decoupled layers**, each with clear responsibilities:

### 1. **Data Layer — MySQL + Migrations**
- Relational database in **MySQL**.
- Migrations managed with **Flyway** or **Liquibase**.
- Résumé data model: person, experience, education, skills, projects, etc.
- Repository: `cv-database`

---

### 2. **Domain Service — Java (Spring Boot)**
The system's main backend.

**Responsibilities:**
- RESTful API for full CRUD of the résumé.
- Data validation.
- Authentication and authorization via **AWS Cognito**.
- Metrics exposure via **Micrometer** for Prometheus.
- Emission of structured logs to the observability layer.

**Technologies:**
- Java 17+
- Spring Boot
- JPA/Hibernate
- OpenAPI/Swagger
- TDD with JUnit + Mockito

**Repository:** `cv-domain-service`

---

### 3. **Backend For Frontend (BFF) — NodeJS**
Intermediate layer optimized for the end-user experience.

**Responsibilities:**
- Aggregation and adaptation of data coming from the Java service.
- Lightweight caching (optional).
- Normalization of responses for the public frontend.
- Exposure of metrics and logs.

**Technologies:**
- NodeJS + Express + TypeScript
- Jest + Supertest for TDD
- OpenAPI (optional)

**Repository:** `cv-bff-node`

---

### 4. **Admin Frontend — React**
Application for editing and managing the résumé.

**Responsibilities:**
- Full CRUD of the CV.
- Authentication via AWS Cognito Hosted UI or SDK.
- Advanced forms and validations.
- Direct consumption of the Java service.

**Technologies:**
- React + Hooks
- React Router
- Axios / Fetch
- Jest + React Testing Library (TDD)

**Repository:** `cv-admin-react`

---

### 5. **Public Frontend — Vanilla JS**
Public résumé landing page, lightweight and dynamic.

**Responsibilities:**
- Rendering the CV by consuming the Node BFF.
- Animations and responsive design.
- Fast, optimized loading.

**Technologies:**
- HTML5 + CSS3 + pure JS
- Optional Web Components
- TDD with Vitest or Jest

**Repository:** `cv-public-vanilla`

---

### 6. **Public Frontend (Optimized) — Next.js/React (SSR/ISR)**
A second public résumé site, optimized for performance via server rendering.

**Responsibilities:**
- Fast, optimized rendering of the CV via **ISR (Incremental Static Regeneration)**.
- Server-side fetch of the BFF aggregate (`GET /api/v1/people/:id/cv`), so pages are statically served and revalidated in the background.
- Decoupled from `cv-domain-service` at runtime — it only talks to the BFF.

**Technologies:**
- Next.js 14 (App Router)
- React 18
- TypeScript
- Jest + React Testing Library (TDD)

**Repository:** `cv-public-react`

---

### 7. **Observability — Metrics + Logs**
Explicit separation between metrics and logs.

#### Metrics
- Prometheus (self-hosted on EC2 or a container).
- Dashboards in Grafana.
- Exporters:
  - Java: Micrometer
  - Node: prom-client

#### Logs
- Structured logs in JSON.
- Storage:
  - Design: **MongoDB Atlas (free tier)** for events and auditing, or CloudWatch Logs within AWS.
  - **Deployed (T-052/T-054):** the domain service's and the BFF's container output goes to CloudWatch Logs. Structured JSON logging and Atlas are not built.

**Repository:** `cv-observability`

---

## 🔐 Authentication and Authorization

The system uses **AWS Cognito** to manage users and sessions.

- React Admin → Cognito Hosted UI or SDK.
- Java Domain Service → JWT validation.
- Node BFF → JWT validation and claims propagation.

Cognito's free allowance covers this demo's users. The BFF's machine-to-machine tokens bill per request, which is cents a month (T-043). The account itself is on AWS's Paid plan.

---

## 🧪 Testing Strategy (TDD across all layers)

Every repository implements TDD from the start:

- **Java:** JUnit + Mockito
- **Node:** Jest
- **React:** Jest + React Testing Library
- **Vanilla JS:** Vitest or Jest
- **Infra:** Basic tests with Terraform Validate / CDK Assertions (if applicable)

---

## 🚀 CI/CD — GitHub Actions (and Vercel)

Every repository runs its checks on GitHub Actions, except the Next.js site, which builds on Vercel. (Jenkins and Drone ran on a dedicated CI host until 2026-11-09; they were retired to cut cost.)

| Repository | CI | Deploy (from `master`) |
|-------------|----------|----------|
| cv-domain-service | GitHub Actions | GitHub Actions (`deploy.yml`): once the shared test gate is green, multi-arch image → ECR → SSM `cv-redeploy-domain-service` |
| cv-bff-node | GitHub Actions | the same workflow: multi-arch image → ECR → SSM `cv-redeploy-bff-node` |
| cv-admin-react | GitHub Actions | the same workflow (OIDC): build → S3 `admin/` → CloudFront invalidation |
| cv-public-vanilla | GitHub Actions | the same workflow (OIDC): build → S3 root → CloudFront invalidation |
| cv-public-react | Vercel | Vercel (ISR from the deployed BFF) |
| cv-database | GitHub Actions | GitHub Actions (`migrate.yml`), only when a push changes `sql/migrations/**`: once the migration gate (Flyway against a MySQL 8.4 service container) is green, SSM `cv-redeploy-migrate` runs Flyway in production |
| cv-observability | GitHub Actions | — (local dev stack only) |

The CI column runs lint, tests (TDD) and the build; cv-observability's only validates its compose file and Prometheus config. The deploys assume master-only OIDC roles and hold no stored credential; none is kept anywhere.

---

## ☁️ Cloud Infrastructure (AWS, eu-west-3)

Deployed with Terraform. The account is on AWS's Paid plan since 2026-09-29, paid from credits first (cost model in `cv-infra`). Verified against the account on 2026-10-07:

### Services used
- **EC2 `t4g.micro` (Graviton) app host**
  Runs the domain service (Java) and the BFF (Node) as containers.
- **Self-hosted MySQL 8.4 (container on the domain-service EC2)**
  Main database — runs alongside the app instead of RDS, which avoids the RDS instance cost and the MySQL 8.0 Extended Support charge.
- **S3 + CloudFront**
  Hosting for the admin and the vanilla site; the same distribution fronts the BFF (`/bff/*`) and the domain service (`/api/*`). The Next.js site is on Vercel.
- **AWS Cognito**
  Authentication.
- **CloudWatch Logs**
  The domain service's and the BFF's container logs (since T-054). MongoDB Atlas is a design option, not deployed. Prometheus/Grafana run only in the local dev stack, by design (T-052).
- **SSM Parameter Store**
  Secrets management.

### Infrastructure as code
- Terraform or AWS CDK (recommended for clarity).
- Repository: `cv-infra`

---

## 📂 Recommended Overall Project Structure

This repository (`cv-project`) is the **meta repo**: it holds no application code, only orchestration. The eight product repos are ordinary git repos, cloned as its siblings:

```
cv-project/          ← this repo (meta repo, no submodules)
  scripts/            lint-all.sh, test-all.sh, build-all.sh
  docs/                architecture notes and the system diagram (Mermaid)
  devcontainers/       global, multi-stack devcontainer
  clone-all.sh
  update-all.sh
  README.md
cv-database/
cv-domain-service/
cv-bff-node/
cv-admin-react/
cv-public-vanilla/
cv-public-react/
cv-observability/
cv-infra/
```

### Getting started

```bash
./clone-all.sh          # clone all 8 product repos as siblings (https by default; pass "ssh" to use SSH)
./update-all.sh          # fast-forward pull every repo, including this one
./scripts/lint-all.sh    # lint every repo, per its own stack
./scripts/test-all.sh    # run every repo's test suite
./scripts/build-all.sh   # build every repo
```

### Run the whole stack locally

```bash
docker compose -f docker-compose.dev.yml up --build
curl http://localhost:3000/bff/api/v1/people/1   # vanilla-site path: BFF → domain service → MySQL
```

Brings up MySQL, Flyway migrations (+dev seeds), the Java domain service, the Node BFF, Prometheus (:9090), and Grafana (:3001, admin/admin), with auth disabled via `AUTH_ENABLED=false`. Frontends run separately with `npm run dev` in their repos.

Each product repo also ships its own `.devcontainer/devcontainer.json` for working on that stack alone. The global config under `devcontainers/full-stack/` bootstraps Java, Node, Docker, Terraform, and the AWS CLI in one container for cross-repo work — see [devcontainers/README.md](devcontainers/README.md).

---

## 📌 Roadmap

- [x] Define the initial data model (person/experience/education/skill/project)
- [x] Create initial migrations
- [x] Implement the Java API with TDD (person + experience, education, skills, projects; optimistic locking with `version` / 409)
- [x] Integrate Cognito (user pool + Hosted UI live in eu-west-3; JWT validation in Java/BFF; admin PKCE Hosted UI flow implemented)
- [x] Create the Node BFF (deployed behind CloudFront `/bff/*`; public aggregate `/cv`; reads the domain service with a Cognito service token)
- [x] Create React Admin (CRUD for the person and all four sections; deployed at `/admin/`)
- [x] Create the Vanilla Landing page (full CV; deployed at the CloudFront root)
- [x] Create the Next.js optimized public site (full CV; ISR from the deployed BFF; on Vercel)
- [x] Configure observability (app logs to CloudWatch in production; metrics in the local dev stack only, by design: T-052/T-054)
- [x] Deploy AWS infrastructure — Terraform applied in eu-west-3 (an EC2 app host running the domain service and the BFF beside a self-hosted MySQL 8.4 container, S3+CloudFront for the admin and the vanilla site, Cognito, ECR)
- [x] Configure CI/CD pipelines (GitHub Actions ×6, Vercel ×1); the domain service and the BFF deploy themselves on a master push, cv-database migrates production when a migration lands on master, and the admin and the vanilla site deploy from GitHub Actions
- [x] Final documentation and architecture diagram ([docs/architecture.md](docs/architecture.md))

The finished roadmap is tagged **`M2`** in all nine repos. [`releases/M2.json`](releases/M2.json) pins each repo's commit, and the tags can't be moved or deleted. To reproduce it: `git checkout M2 && scripts/release-checkout.sh M2 && scripts/release-verify.sh M2`.

### Backlog

- Grafana starter dashboard
- Vanilla-site animations / Web Components
