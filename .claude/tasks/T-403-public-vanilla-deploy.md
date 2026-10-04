---
id: T-403
title: "Public site (vanilla): deploy to S3/CloudFront and point it at the deployed BFF"
repo: cv-public-vanilla
status: todo
owner:
branch: chore/deploy-and-bff-url
pr:
depends_on: [T-014, T-408, T-043, T-045]   # T-043 added 2026-10-01: the BFF's public routes 401/502 until it has a service token. T-408 added 2026-09-23 — FILE-LEVEL: this task edits `src/main.js:3` (the localhost fallback) and T-408 fixes `main.js:10`; and a deploy of the pre-T-408 bundle would publish a page whose only request 404s.
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

## H1 — decided by the human, 2026-10-04

1. **Credential: GitHub OIDC**, split out as [T-045](T-045-github-oidc-deploy-role-public-vanilla.md) (cv-infra), which goes first. The workflow assumes the role (ARN from a repo variable) via `aws-actions/configure-aws-credentials` with `permissions: id-token: write`, on `master` pushes only.
2. **Same-origin, relative BFF calls:** production builds call `/bff/api/v1/…` on the page's own origin; local dev keeps `http://localhost:3000`. That needs a small `src/main.js` change (an unset `VITE_BFF_URL` in a production build → `''`, not localhost). A CI grep fails the build if `localhost:3000` is in `dist/`.
3. **The site deploys to the bucket ROOT** (the edge sends every non-admin path to `/index.html`, and `default_root_object = index.html`). **`aws s3 sync … --delete` must carry `--exclude "admin/*"`**, so the live admin is never deleted. T-045's role also denies writes under `admin/`, as a second guard.
4. **Budget:** `/usage` 40–75%: T-045 first to merge, then checkpoint; this task starts in a later window.

## Board review 2026-10-04 — an unowned cv-infra dependency: the deploy credential

The deploy job runs in **GitHub Actions** and needs AWS credentials (S3 sync to the site's prefix plus a CloudFront invalidation). cv-infra has **no GitHub OIDC provider**; the only deploy credential is the `drone_deploy` IAM user's static key (T-008), which [T-005](T-005-ci-secret-blast-radius.md) warns against reusing. **Decide the GitHub → AWS credential model at this task's H1**, not later at T-112/T-203's: the recommended shape is an `aws_iam_openid_connect_provider` for `token.actions.githubusercontent.com` plus a role per repo, trusted only for that repo's `master`, allowed only its own bucket prefix and the invalidation. That's a cv-infra piece, so **split it at stage 0** (adapter §2): a cv-infra task first, then this one. [T-203](T-203-bff-ci-deploy-stage.md) (also GitHub Actions) reuses the same provider.

## Scope

- Replace the placeholder with a real deploy job: build, `aws s3 sync dist/` to the site's own prefix of the shared bucket, invalidate that prefix. Follow `cv-admin-react/.drone.yml`'s deploy step as the working reference — same bucket, same distribution, different prefix.
- The prefix must agree with `cv-infra/functions/spa-router.js`, which routes extension-less URIs per owning app. Read that function; do not guess the prefix.
- Bake `VITE_BFF_URL` at build time, pointing at the public edge path T-013 ratified and T-014 deployed. Same-origin (a relative path) is preferable to an absolute URL if the contract's edge layout allows it — it removes the CORS dependency entirely.
- Remove or guard the `localhost:3000` fallback so a missing env var **fails the build** rather than shipping a bundle that fetches from the visitor's laptop.

## Acceptance criteria
- [ ] **(from T-014's H1 refresh, 2026-10-01)** Once this task publishes a root `index.html`, `/metrics` and `/health` through the CloudFront domain still do **not** return the SPA shell (T-014 excluded them from `spa-router.js` while the defect was dormant). Verify by request.

- [ ] A `master` push publishes the built site and invalidates its prefix; PR builds do not deploy.
- [ ] The deployed bundle contains **no** `localhost:3000` — grep the built output in CI and fail on a hit. This is the whole point of the task; a convention is not enough.
- [ ] Loading the site through the CloudFront domain renders person data fetched from the deployed BFF (end-to-end, real request).
- [ ] The admin at `/admin/` still works — the two apps share a bucket and a distribution. **(H1 2026-10-04)** The deploy's `sync --delete` excludes `admin/*`, verified by listing `admin/` before and after the first deploy (same object count and ETags).
- [ ] **A trailing slash on `VITE_BFF_URL` must not produce `//bff/api/v1/…`.** `src/main.js` concatenates `${BFF_URL}/bff/api/v1/…` without normalising (since T-408), and this task is the one that sets the value — a hand-typed deploy variable is exactly where a trailing slash appears. Trim it in `main.js` or fail the build on it. Mirrors the AC [T-404](T-404-public-react-point-at-deployed-bff.md) carries for the React site; raised by `frontend-architect` in T-408's review, 2026-09-24.
- [ ] `npm run lint`, `npm test`, `npm run build` pass.

## Definition of done

PR open against `master` from `chore/deploy-and-bff-url`, GitHub Actions green including the deploy stage on the merge commit, merged. With T-014, this makes the public path real end-to-end for the first time.

## dev-loop notes

- **Developer:** `fullstack-developer` (adapter §2 — `cv-public-vanilla` is Vanilla JS + Vite). The workflow edit is CI config, nominally `infrastructure-engineer` territory; it is kept in one task because the deploy stage and the `VITE_BFF_URL` bake are the same defect seen from two sides, and splitting them across personas would ship a deploy that publishes the broken bundle. **Reviewers:** `/code-review` + `frontend-architect` (adapter §2 primary FE reviewer) + `infrastructure-engineer` on the workflow/credentials.
- **`security_review: true`:** `.github/workflows/**` plus AWS deploy credentials — a named §5 CI path. Read T-005 (CI secret blast radius) before reusing the `cv-project-drone-deploy` key.
- **Filed as an addition, not part of the original ask.** It surfaced while verifying the BFF gap. If it is judged out of scope, T-501 cannot pass end-to-end without it — say so there rather than silently dropping it.
- Gates (adapter §3): `npm run lint` · `npm test` (vitest run) · `npm run build`. No typecheck in this repo. Authoritative CI: **GitHub Actions**.
- **`cv-public-react` (Vercel) is deliberately not in scope.** It consumes the same BFF aggregate via `BFF_URL` (`src/composition/container.ts:23`) and will need that env var pointed at the deployed BFF — but that is a Vercel project setting, not a repo change, and it has no `depends_on` relationship with this task. ~~Handle it at T-501, or file it separately if it turns out to need code.~~ **Filed separately 2026-08-17 as [T-404](T-404-public-react-point-at-deployed-bff.md)** — T-501 never picked it up, so it sat unowned between three task files. Still not this task's problem; it now has its own.
