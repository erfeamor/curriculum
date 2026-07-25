🌐 **Language:** [English](README.md) | [Español](README.es.md)

---

# 📘 Project: Interactive Résumé — Full-Stack Technology Demo

This project is a **comprehensive technology demo** designed to showcase mastery of multiple technologies, architectures, patterns, and modern development practices.
The system is composed of several independent layers, each living in its own repository and deployed via distinct pipelines (Jenkins, GitHub Actions, and DroneCI).

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
- NodeJS + Express
- Jest for TDD
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
  - **MongoDB Atlas (free tier)** for events and auditing.
  - Alternative: CloudWatch Logs to simplify within AWS.

**Repository:** `cv-observability`

---

## 🔐 Authentication and Authorization

The system uses **AWS Cognito** to manage users and sessions.

- React Admin → Cognito Hosted UI or SDK.
- Java Domain Service → JWT validation.
- Node BFF → JWT validation and claims propagation.

Cognito falls within the **AWS Free Tier**, making it suitable for this demo.

---

## 🧪 Testing Strategy (TDD across all layers)

Every repository implements TDD from the start:

- **Java:** JUnit + Mockito
- **Node:** Jest
- **React:** Jest + React Testing Library
- **Vanilla JS:** Vitest or Jest
- **Infra:** Basic tests with Terraform Validate / CDK Assertions (if applicable)

---

## 🚀 CI/CD — Jenkins, GitHub Actions, and DroneCI

Each repository uses a different pipeline to demonstrate mastery of multiple tools:

| Repository | Pipeline |
|-------------|----------|
| cv-domain-service | Jenkins |
| cv-bff-node | GitHub Actions |
| cv-admin-react | DroneCI |
| cv-public-vanilla | GitHub Actions |
| cv-public-react | Vercel |
| cv-database | Jenkins |
| cv-observability | GitHub Actions |

The pipelines include:
- Linter
- Tests (TDD)
- Build
- Docker image
- Deploy to AWS (dev/prod)

---

## ☁️ Cloud Infrastructure (AWS Free Tier)

Deployment is done on AWS, making the most of the free tier:

### Services used
- **EC2 t2.micro/t3.micro**
  For Java, Node, and Prometheus/Grafana (if desired).
- **RDS MySQL Free Tier**
  Main database.
- **S3 + CloudFront**
  Hosting for the React and Vanilla frontends.
- **AWS Cognito**
  Authentication.
- **CloudWatch Logs**
  Basic logging.
- **MongoDB Atlas Free Tier**
  NoSQL logs/events.
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
  docs/                architecture notes
  diagrams/            architecture.mmd
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
curl http://localhost:3000/api/v1/people/1   # vanilla-site path: BFF → domain service → MySQL
```

Brings up MySQL, Flyway migrations (+dev seeds), the Java domain service, the Node BFF, Prometheus (:9090), and Grafana (:3001, admin/admin), with auth disabled via `AUTH_ENABLED=false`. Frontends run separately with `npm run dev` in their repos.

Each product repo also ships its own `.devcontainer/devcontainer.json` for working on that stack alone. The global config under `devcontainers/full-stack/` bootstraps Java, Node, Docker, Terraform, and the AWS CLI in one container for cross-repo work — see [devcontainers/README.md](devcontainers/README.md).

---

## 📌 Roadmap

- [x] Define the initial data model (person/experience/education/skill/project)
- [x] Create initial migrations
- [x] Implement the Java API with TDD (person resource; remaining entities pending)
- [x] Integrate Cognito (user pool + Hosted UI live in eu-west-3; JWT validation in Java/BFF; admin PKCE Hosted UI flow implemented)
- [x] Create the Node BFF
- [x] Create React Admin (person CRUD)
- [x] Create the Vanilla Landing page
- [x] Create the Next.js optimized public site (person view; ISR from the BFF)
- [x] Configure observability (metrics; structured-logging pipeline pending)
- [x] Deploy AWS infrastructure — Terraform applied in eu-west-3 (EC2 domain service, RDS MySQL, S3+CloudFront frontends, Cognito, ECR, Drone CI server)
- [x] Configure CI/CD pipelines (Jenkins ×2, GitHub Actions ×3, DroneCI ×1, Vercel ×1)
- [ ] Final documentation and architecture diagram

### Backlog

- Automated backend deploy stages in CI (EC2/RDS provisioned and live; frontends deploy via DroneCI, backend services still deployed manually)
- Remaining domain entities (experience, education, skill, project) across API/BFF/frontends
- Structured JSON logging to MongoDB Atlas or CloudWatch (see `cv-observability/docs/logging.md`)
- Grafana starter dashboard
- Vanilla-site animations / Web Components
