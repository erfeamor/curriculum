🌐 **Idioma:** [English](README.md) | [Español](README.es.md)

---

# 📘 Proyecto: Currículum Interactivo — Demo Tecnológica Full‑Stack

Este proyecto es una **demo tecnológica integral** diseñada para mostrar dominio de múltiples tecnologías, arquitecturas, patrones y prácticas modernas de desarrollo.  
El sistema se compone de varias capas independientes, cada una ubicada en su propio repositorio y desplegada mediante pipelines distintos (Jenkins, GitHub Actions y DroneCI).

---

## 🏗️ Arquitectura General

El proyecto se organiza en **capas desacopladas**, cada una con responsabilidades claras:

### 1. **Capa de Datos — MySQL + Migraciones**
- Base de datos relacional en **MySQL**.
- Migraciones gestionadas con **Flyway** o **Liquibase**.
- Modelo de datos del currículum: persona, experiencia, educación, habilidades, proyectos, etc.
- Repositorio: `cv-database`

---

### 2. **Servicio de Dominio — Java (Spring Boot)**
Backend principal del sistema.

**Responsabilidades:**
- API RESTful para CRUD completo del currículum.
- Validación de datos.
- Autenticación y autorización mediante **AWS Cognito**.
- Exposición de métricas vía **Micrometer** para Prometheus.
- Emisión de logs estructurados hacia la capa de observabilidad.

**Tecnologías:**
- Java 17+
- Spring Boot
- JPA/Hibernate
- OpenAPI/Swagger
- TDD con JUnit + Mockito

**Repositorio:** `cv-domain-service`

---

### 3. **Backend For Frontend (BFF) — NodeJS**
Capa intermedia optimizada para la experiencia del usuario final.

**Responsabilidades:**
- Agregación y adaptación de datos provenientes del servicio Java.
- Cacheo ligero (opcional).
- Normalización de respuestas para el frontend público.
- Exposición de métricas y logs.

**Tecnologías:**
- NodeJS + Express + TypeScript
- Jest + Supertest para TDD
- OpenAPI opcional

**Repositorio:** `cv-bff-node`

---

### 4. **Frontend de Administración — React**
Aplicación para editar y gestionar el currículum.

**Responsabilidades:**
- CRUD completo del CV.
- Autenticación mediante AWS Cognito Hosted UI o SDK.
- Formularios avanzados y validaciones.
- Consumo directo del servicio Java.

**Tecnologías:**
- React + Hooks
- React Router
- Axios / Fetch
- Jest + React Testing Library (TDD)

**Repositorio:** `cv-admin-react`

---

### 5. **Frontend Público — Vanilla JS**
Landing pública del currículum, ligera y dinámica.

**Responsabilidades:**
- Renderizado del CV consumiendo el BFF Node.
- Animaciones y diseño responsive.
- Carga rápida y optimizada.

**Tecnologías:**
- HTML5 + CSS3 + JS puro
- Web Components opcionales
- TDD con Vitest o Jest

**Repositorio:** `cv-public-vanilla`

---

### 6. **Frontend Público (Optimizado) — Next.js/React (SSR/ISR)**
Un segundo sitio público del currículum, optimizado para rendimiento mediante renderizado en servidor.

**Responsabilidades:**
- Renderizado rápido y optimizado del CV vía **ISR (Incremental Static Regeneration)**.
- Fetch en servidor del agregado del BFF (`GET /api/v1/people/:id/cv`), de modo que las páginas se sirven de forma estática y se revalidan en segundo plano.
- Desacoplado de `cv-domain-service` en tiempo de ejecución — solo se comunica con el BFF.

**Tecnologías:**
- Next.js 14 (App Router)
- React 18
- TypeScript
- Jest + React Testing Library (TDD)

**Repositorio:** `cv-public-react`

---

### 7. **Observabilidad — Métricas + Logs**
Separación explícita entre métricas y logs.

#### Métricas
- Prometheus (self‑hosted en EC2 o contenedor).
- Dashboards en Grafana.
- Exporters:
  - Java: Micrometer
  - Node: prom-client

#### Logs
- Logs estructurados en JSON.
- Almacenamiento:
  - **MongoDB Atlas (free tier)** para eventos y auditoría.
  - Alternativa: CloudWatch Logs para simplificar en AWS.

**Repositorio:** `cv-observability`

---

## 🔐 Autenticación y Autorización

El sistema utiliza **AWS Cognito** para gestionar usuarios y sesiones.

- React Admin → Cognito Hosted UI o SDK.
- Java Domain Service → Validación de JWT.
- Node BFF → Validación de JWT y propagación de claims.

Cognito entra dentro del **AWS Free Tier**, por lo que es adecuado para esta demo.

---

## 🧪 Estrategia de Testing (TDD en todas las capas)

Cada repositorio implementa TDD desde el inicio:

- **Java:** JUnit + Mockito  
- **Node:** Jest  
- **React:** Jest + React Testing Library  
- **Vanilla JS:** Vitest o Jest  
- **Infra:** Tests básicos con Terraform Validate / CDK Assertions (si aplica)

---

## 🚀 CI/CD — Jenkins, GitHub Actions y DroneCI

Cada repositorio usa un pipeline distinto para demostrar dominio de varias herramientas:

| Repositorio | CI | Deploy (desde `master`) |
|-------------|----------|----------|
| cv-domain-service | Jenkins | GitHub Actions (`deploy.yml`): con Jenkins en verde, imagen multi-arch → ECR → SSM `cv-redeploy-domain-service` |
| cv-bff-node | GitHub Actions | el mismo workflow: imagen multi-arch → ECR → SSM `cv-redeploy-bff-node` |
| cv-admin-react | DroneCI | Drone: build → S3 `admin/` → invalidación de CloudFront |
| cv-public-vanilla | GitHub Actions | el mismo workflow (OIDC): build → raíz de S3 → invalidación de CloudFront |
| cv-public-react | Vercel | Vercel (ISR desde el BFF desplegado) |
| cv-database | Jenkins | GitHub Actions (`migrate.yml`), solo cuando un push cambia `sql/migrations/**`: con Jenkins en verde, SSM `cv-redeploy-migrate` ejecuta Flyway en producción |
| cv-observability | GitHub Actions | — (solo stack local de desarrollo) |

La columna de CI ejecuta lint, tests (TDD) y build; la de cv-observability solo valida su fichero compose y la configuración de Prometheus. Los deploys de GitHub Actions asumen roles OIDC limitados a master y no guardan ninguna credencial. El deploy del admin desde Drone es la excepción: usa una clave de acceso IAM estática guardada en Drone, en el host de CI.

---

## ☁️ Infraestructura Cloud (AWS, eu-west-3)

Desplegada con Terraform. La cuenta está en el plan Paid de AWS desde el 2026-09-29 y se paga primero con créditos (modelo de costes en `cv-infra`). Verificado contra la cuenta el 2026-10-07:

### Servicios utilizados
- **Host de aplicación EC2 `t4g.micro` (Graviton)**  
  Ejecuta el servicio de dominio (Java) y el BFF (Node) como contenedores. Un host de CI `t3.small` aparte ejecuta Jenkins y Drone y solo se arranca para los builds.
- **MySQL 8.4 autoalojado (contenedor en la EC2 del servicio de dominio)**  
  Base de datos principal — corre junto a la app en lugar de RDS, lo que evita el coste de la instancia RDS y el cargo de Extended Support de MySQL 8.0.
- **S3 + CloudFront**  
  Hosting del admin y del sitio vanilla; la misma distribución da acceso al BFF (`/bff/*`) y al servicio de dominio (`/api/*`). El sitio Next.js está en Vercel.
- **AWS Cognito**  
  Autenticación.
- **CloudWatch Logs**  
  Existen grupos de logs para ambos servicios, pero ningún contenedor les envía logs todavía (solo las Lambdas doorbell y reaper del host de CI escriben logs allí). MongoDB Atlas es una opción de diseño, no desplegada, y Prometheus/Grafana solo corren en el stack local de desarrollo (decisión de alcance: T-052).
- **SSM Parameter Store**  
  Gestión de secretos.

### Infraestructura como código
- Terraform o AWS CDK (recomendado para claridad).
- Repositorio: `cv-infra`

---

## 📂 Estructura Recomendada del Proyecto General

Este repositorio (`cv-project`) es el **meta repo**: no contiene código de aplicación, solo orquestación. Los ocho repos de producto son repos git normales, clonados como sus hermanos:

```
cv-project/          ← este repo (meta repo, sin submódulos)
  scripts/            lint-all.sh, test-all.sh, build-all.sh
  docs/                notas de arquitectura
  diagrams/            architecture.mmd
  devcontainers/       devcontainer global multi-stack
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

### Primeros pasos

```bash
./clone-all.sh          # clona los 8 repos de producto como hermanos (https por defecto; pasa "ssh" para usar SSH)
./update-all.sh          # hace pull fast-forward de todos los repos, incluido este
./scripts/lint-all.sh    # lintea cada repo según su propio stack
./scripts/test-all.sh    # ejecuta la suite de tests de cada repo
./scripts/build-all.sh   # construye cada repo
```

### Levantar todo el stack en local

```bash
docker compose -f docker-compose.dev.yml up --build
curl http://localhost:3000/bff/api/v1/people/1   # ruta del sitio público: BFF → servicio de dominio → MySQL
```

Levanta MySQL, las migraciones de Flyway (+seeds de desarrollo), el servicio Java de dominio, el BFF Node, Prometheus (:9090) y Grafana (:3001, admin/admin), con la autenticación desactivada vía `AUTH_ENABLED=false`. Los frontends se ejecutan aparte con `npm run dev` en sus repos.

Cada repo de producto también incluye su propio `.devcontainer/devcontainer.json` para trabajar únicamente en ese stack. La configuración global en `devcontainers/full-stack/` levanta Java, Node, Docker, Terraform y la AWS CLI en un solo contenedor para trabajo cruzado entre repos — ver [devcontainers/README.md](devcontainers/README.md).

---

## 📌 Roadmap

- [x] Definir modelo de datos inicial (person/experience/education/skill/project)
- [x] Crear migraciones iniciales
- [x] Implementar API Java con TDD (person + experience, education, skills, projects; bloqueo optimista con `version` / 409)
- [x] Integrar Cognito (user pool + Hosted UI activos en eu-west-3; validación JWT en Java/BFF; flujo Hosted UI con PKCE implementado en el admin)
- [x] Crear BFF Node (desplegado tras CloudFront `/bff/*`; agregado público `/cv`; lee el servicio de dominio con un token de servicio de Cognito)
- [x] Crear React Admin (CRUD de la persona y de las cuatro secciones; desplegado en `/admin/`)
- [x] Crear Vanilla Landing (CV completo; desplegado en la raíz de CloudFront)
- [x] Crear el sitio público optimizado con Next.js (CV completo; ISR desde el BFF desplegado; en Vercel)
- [x] Configurar observabilidad (métricas solo en el stack local de desarrollo; aún sin métricas ni pipeline de logs en la nube, decisión de alcance T-052)
- [x] Desplegar infraestructura AWS — Terraform aplicado en eu-west-3 (un host EC2 de aplicación con el servicio de dominio y el BFF junto a un contenedor MySQL 8.4 autoalojado, S3+CloudFront para el admin y el sitio vanilla, Cognito, ECR, un host de CI bajo demanda para Jenkins y Drone)
- [x] Configurar pipelines CI/CD (Jenkins ×2, GitHub Actions ×5, DroneCI ×1, Vercel ×1); el servicio de dominio y el BFF se despliegan solos en cada push a master, cv-database migra producción cuando llega una migración a master, el admin se despliega desde Drone y el sitio vanilla desde GitHub Actions
- [ ] Documentación final y diagrama de arquitectura

### Backlog

- Logging JSON estructurado hacia MongoDB Atlas o CloudWatch (ver `cv-observability/docs/logging.md`); si se hace o no es T-052
- ECR conserva todas las imágenes de deploy `:<sha>`; la regla de retención es T-050
- Dashboard inicial de Grafana
- Animaciones / Web Components del sitio público
