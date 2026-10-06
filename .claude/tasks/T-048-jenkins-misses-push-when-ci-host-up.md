---
id: T-048
title: "A push to a Jenkins repo while the CI host is already running never reaches Jenkins — the doorbell says 'already running; nothing to do'"
repo: cv-infra
status: todo
owner:
branch: fix/jenkins-push-when-host-up
pr:
depends_on: []
risk: normal
security_review: true   # webhook targets / doorbell behaviour on the CI host — adapter §5 CI-config path
---

## Why this exists

Found live on 2026-10-06 while merging [T-112](T-112-domain-service-ci-ecr-deploy.md) (cv-domain-service#17 → master f487615 at 10:23:43Z):

- The CI host was **already running** (woken at 10:01 for the PR's Jenkins build).
- 10:23:45Z, the doorbell log: `i-0ee24b3d917501c4d already running for erfeamor/cv-domain-service; nothing to do`.
- **Jenkins never built master:** the Jenkins repos' only GitHub webhook points at the doorbell, and Jenkins discovers changes by **scanning when the host starts**. A push that arrives while the host is up is therefore invisible to Jenkins. The reaper then stopped the idle host.
- T-112's `wait-for-jenkins` kept waiting for a status that would never come. The driver unblocked it by starting the CI host by hand (Jenkins scans on boot).

This affects **every** Jenkins-built push (cv-domain-service, cv-database) that lands while the host is up, which is likely during any busy session. Since T-112, it also silently blocks domain-service deploys until the 30-minute wait expires.

## Options (decide at H1)

1. **A second GitHub webhook on each Jenkins repo** → `https://ci.erfeamor.com/jenkins/github-webhook/`, beside the doorbell hook (the cv-admin-react pattern: Drone hook + doorbell hook). When the host is up, Jenkins gets the push directly; when it's down, that delivery fails and the doorbell's wake + scan-on-boot covers it. Needs Jenkins' GitHub-hook trigger configured (JCasC) and the hook's secret; possibly the doorbell's redelivery extended to the Jenkins repos.
2. **The doorbell triggers a Jenkins scan when the host is already running** (call Jenkins' multibranch scan API with credentials from SSM). Keeps a single hook, but the doorbell now needs Jenkins credentials.
3. **A periodic multibranch scan** (e.g. every 5 min) while the host is up. The simplest, but adds latency and isn't event-driven.

## Acceptance criteria

- [ ] A push to cv-domain-service **while the CI host is up** gets a Jenkins build and a commit status within a few minutes (proven live).
- [ ] A push while the host is **stopped** still wakes it and builds (no regression).
- [ ] T-112's deploy chain works for a master push in both cases.
