---
id: T-403
title: "Public site (vanilla): deploy to S3/CloudFront and point it at the deployed BFF"
repo: cv-public-vanilla
status: todo
owner:
branch: chore/deploy-and-bff-url
pr:
depends_on: [T-014]
risk: normal
security_review: true
---

## Why this exists

**Found while filing T-013/T-014, and worth stating plainly: `cv-public-vanilla` is not deployed either.** Verified on the live account — `aws s3 ls s3://cv-project-frontend-dev/` returns exactly one prefix, `admin/`. The public site has never been published.

Its CI ends the same way the BFF's does:

```yaml
# Placeholder until cv-infra outputs the bucket/distribution IDs:
# deploy job syncs dist/ to S3 and invalidates CloudFront on main.
```

Those outputs have existed for a while — `cv-admin-react/.drone.yml` hardcodes both (`cv-project-frontend-dev`, distribution `E2AV0INGJW1UO2`) and deploys successfully today. The blocker named in that comment is stale.

Second defect, independent of deployment: `src/main.js:3` reads

```js
const BFF_URL = import.meta.env.VITE_BFF_URL || 'http://localhost:3000';
```

With no `VITE_BFF_URL` baked at build time, a deployed bundle fetches from **the visitor's own machine**. `cv-admin-react/.drone.yml` carries a comment about precisely this trap — Drone silently drops empty-string env values, which *"let the localhost fallback into a deployed bundle once."* The same footgun, unfixed here, in a repo that has never deployed so has never been caught by it.

Together these are why the public path shows nothing in AWS even once T-014 lands: no BFF **and** no site.

## Scope

- Replace the placeholder with a real deploy job: build, `aws s3 sync dist/` to the site's own prefix of the shared bucket, invalidate that prefix. Follow `cv-admin-react/.drone.yml`'s deploy step as the working reference — same bucket, same distribution, different prefix.
- The prefix must agree with `cv-infra/functions/spa-router.js`, which routes extension-less URIs per owning app. Read that function; do not guess the prefix.
- Bake `VITE_BFF_URL` at build time, pointing at the public edge path T-013 ratified and T-014 deployed. Same-origin (a relative path) is preferable to an absolute URL if the contract's edge layout allows it — it removes the CORS dependency entirely.
- Remove or guard the `localhost:3000` fallback so a missing env var **fails the build** rather than shipping a bundle that fetches from the visitor's laptop.

## Acceptance criteria

- [ ] A `master` push publishes the built site and invalidates its prefix; PR builds do not deploy.
- [ ] The deployed bundle contains **no** `localhost:3000` — grep the built output in CI and fail on a hit. This is the whole point of the task; a convention is not enough.
- [ ] Loading the site through the CloudFront domain renders person data fetched from the deployed BFF (end-to-end, real request).
- [ ] The admin at `/admin/` still works — the two apps share a bucket and a distribution.
- [ ] `npm run lint`, `npm test`, `npm run build` pass.

## Definition of done

PR open against `master` from `chore/deploy-and-bff-url`, GitHub Actions green including the deploy stage on the merge commit, merged. With T-014, this makes the public path real end-to-end for the first time.

## dev-loop notes

- **Developer:** `fullstack-developer` (adapter §2 — `cv-public-vanilla` is Vanilla JS + Vite). The workflow edit is CI config, nominally `infrastructure-engineer` territory; it is kept in one task because the deploy stage and the `VITE_BFF_URL` bake are the same defect seen from two sides, and splitting them across personas would ship a deploy that publishes the broken bundle. **Reviewers:** `/code-review` + `frontend-architect` (adapter §2 primary FE reviewer) + `infrastructure-engineer` on the workflow/credentials.
- **`security_review: true`:** `.github/workflows/**` plus AWS deploy credentials — a named §5 CI path. Read T-005 (CI secret blast radius) before reusing the `cv-project-drone-deploy` key.
- **Filed as an addition, not part of the original ask.** It surfaced while verifying the BFF gap. If it is judged out of scope, T-501 cannot pass end-to-end without it — say so there rather than silently dropping it.
- Gates (adapter §3): `npm run lint` · `npm test` (vitest run) · `npm run build`. No typecheck in this repo. Authoritative CI: **GitHub Actions**.
- **`cv-public-react` (Vercel) is deliberately not in scope.** It consumes the same BFF aggregate via `BFF_URL` (`src/composition/container.ts:23`) and will need that env var pointed at the deployed BFF — but that is a Vercel project setting, not a repo change, and it has no `depends_on` relationship with this task. Handle it at T-501, or file it separately if it turns out to need code.
