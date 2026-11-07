---
id: T-410
title: "cv-public-react on react.erfeamor.com"
repo: cv-public-react
status: todo
owner: 
branch: feat/react-erfeamor-com
pr:
depends_on: [T-061]
risk: low
security_review: false
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

Serve the Next.js site at `react.erfeamor.com` through a Vercel custom domain. This was decided 2026-11-07 instead of `/react`, because Vercel discourages a proxy in front.

## Scope

- **Human:** add `react.erfeamor.com` in the Vercel dashboard and set `BFF_URL=https://erfeamor.com`, then **redeploy**: env changes apply only to a new deploy (`CLAUDE.md:119`).
- Add `metadataBase` to `app/layout.tsx`, which has none today. Update the `src/composition/container.test.ts:3` fixture and `CLAUDE.md:115`.

## Acceptance criteria

- [ ] `https://react.erfeamor.com` renders the CV over a valid certificate.
- [ ] `erfeamor.com/react` redirects there (via T-061).
