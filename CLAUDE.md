# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status

This repository currently contains only `README.md` — a Spanish-language architecture spec for a planned multi-repo project. No source code, build tooling, tests, or CI configuration exist yet. There is nothing to build, lint, or test at this time. When implementation work begins, update this file with the real commands and structure that emerge.

## Project concept

"Currículum Interactivo" is a full-stack technology demo: an interactive CV/résumé system built to showcase multiple stacks, architectures, and CI/CD tools working together. It is designed as **six independent repositories**, each deployed via its own pipeline, not as a monorepo:

| Repo | Layer | Stack | Pipeline |
|---|---|---|---|
| `cv-database` | Data | MySQL + Flyway/Liquibase migrations | Jenkins |
| `cv-domain-service` | Core domain API | Java 17+, Spring Boot, JPA/Hibernate, OpenAPI, JUnit+Mockito | Jenkins |
| `cv-bff-node` | Backend-for-Frontend | Node.js + Express, Jest | GitHub Actions |
| `cv-admin-react` | Admin frontend (CRUD) | React + Hooks, React Router, Jest + RTL | DroneCI |
| `cv-public-vanilla` | Public landing page | Vanilla HTML/CSS/JS, optional Web Components, Vitest/Jest | GitHub Actions |
| `cv-observability` | Metrics + logs | Prometheus/Grafana (Micrometer, prom-client), MongoDB Atlas or CloudWatch for logs | Jenkins or Actions |

A separate `cv-infra` repo holds infrastructure-as-code (Terraform or AWS CDK).

## Architecture flow

`cv-public-vanilla` (public site) → `cv-bff-node` (BFF: aggregates/normalizes) → `cv-domain-service` (Java REST API, source of truth) → `cv-database` (MySQL).

`cv-admin-react` (admin CRUD UI) talks directly to `cv-domain-service`, bypassing the BFF.

Auth: **AWS Cognito** issues JWTs. `cv-admin-react` uses the Cognito Hosted UI/SDK to authenticate; `cv-domain-service` validates JWTs; `cv-bff-node` validates JWTs and propagates claims downstream.

Observability is deliberately split: metrics go to Prometheus/Grafana (via Micrometer in Java, prom-client in Node), while structured JSON logs go to MongoDB Atlas or CloudWatch — these are treated as two separate concerns, not a unified stack.

## Conventions to carry into each new repo

- TDD is the stated practice in every layer: JUnit+Mockito (Java), Jest (Node/React), Vitest or Jest (vanilla JS), Terraform Validate/CDK Assertions (infra).
- Each repo intentionally uses a different CI system (Jenkins, GitHub Actions, DroneCI) — this is a deliberate demo goal, not an inconsistency to fix.
- Target infra is AWS Free Tier throughout (EC2 t2/t3.micro, RDS MySQL Free Tier, S3+CloudFront, Cognito, CloudWatch, SSM Parameter Store) — keep resource choices within free-tier limits.
