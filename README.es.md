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
- NodeJS + Express
- Jest para TDD
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

### 6. **Observabilidad — Métricas + Logs**
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

| Repositorio | Pipeline |
|-------------|----------|
| cv-domain-service | Jenkins |
| cv-bff-node | GitHub Actions |
| cv-admin-react | DroneCI |
| cv-public-vanilla | GitHub Actions |
| cv-database | Jenkins |
| cv-observability | Jenkins o Actions |

Los pipelines incluyen:
- Linter
- Tests (TDD)
- Build
- Docker image
- Deploy a AWS (dev/prod)

---

## ☁️ Infraestructura Cloud (AWS Free Tier)

El despliegue se realiza en AWS aprovechando al máximo el free tier:

### Servicios utilizados
- **EC2 t2.micro/t3.micro**  
  Para Java, Node y Prometheus/Grafana (si se desea).
- **RDS MySQL Free Tier**  
  Base de datos principal.
- **S3 + CloudFront**  
  Hosting del frontend React y Vanilla.
- **AWS Cognito**  
  Autenticación.
- **CloudWatch Logs**  
  Logs básicos.
- **MongoDB Atlas Free Tier**  
  Logs/eventos NoSQL.
- **SSM Parameter Store**  
  Gestión de secretos.

### Infraestructura como código
- Terraform o AWS CDK (recomendado para claridad).
- Repositorio: `cv-infra`

---

## 📂 Estructura Recomendada del Proyecto General

Este repositorio (`cv-project`) es el **meta repo**: no contiene código de aplicación, solo orquestación. Los siete repos de producto son repos git normales, clonados como sus hermanos:

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
cv-observability/
cv-infra/
```

### Primeros pasos

```bash
./clone-all.sh          # clona los 7 repos de producto como hermanos (https por defecto; pasa "ssh" para usar SSH)
./update-all.sh          # hace pull fast-forward de todos los repos, incluido este
./scripts/lint-all.sh    # lintea cada repo según su propio stack
./scripts/test-all.sh    # ejecuta la suite de tests de cada repo
./scripts/build-all.sh   # construye cada repo
```

Cada repo de producto también incluye su propio `.devcontainer/devcontainer.json` para trabajar únicamente en ese stack. La configuración global en `devcontainers/full-stack/` levanta Java, Node, Docker, Terraform y la AWS CLI en un solo contenedor para trabajo cruzado entre repos — ver [devcontainers/README.md](devcontainers/README.md).

---

## 📌 Roadmap

- [ ] Definir modelo de datos completo  
- [ ] Crear migraciones iniciales  
- [ ] Implementar API Java con TDD  
- [ ] Integrar Cognito  
- [ ] Crear BFF Node  
- [ ] Crear React Admin  
- [ ] Crear Vanilla Landing  
- [ ] Configurar observabilidad  
- [ ] Desplegar infraestructura AWS  
- [ ] Configurar pipelines CI/CD  
- [ ] Documentación final y diagrama de arquitectura  
