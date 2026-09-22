---
id: T-408
title: "cv-public-vanilla calls the BFF at `/api/v1/…`, a path the BFF no longer serves — the landing page is broken today, and `main.js` has no test at all"
repo: cv-public-vanilla
status: todo
owner:
branch: fix/bff-public-edge-path
depends_on: []
risk: normal
security_review: false   # no auth or exposure change; a wrong path returns 404, it does not widen access
---

## The defect

`src/main.js:10` builds:

```js
const response = await fetch(`${BFF_URL}/api/v1/people/${PERSON_ID}`);
```

with `BFF_URL` defaulting to the bare origin `http://localhost:3000` (`src/main.js:3`, and `.env.example:1` sets `VITE_BFF_URL=http://localhost:3000`).

**cv-bff-node does not serve that path.** `src/middleware/auth.ts:20` sets `API_BASE_PATH = '/bff/api/v1'` and `src/app.ts:31-32` mounts both routers there and nowhere else. [T-202](T-202-bff-public-routing-and-auth.md) removed the old `/api/v1` base deliberately — it belongs to cv-domain-service at the edge.

So against a running stack the fetch 404s, `main()` takes its `catch`, and the page renders `<p role="alert">Could not load résumé: BFF responded with 404</p>`. **The landing page is the error path, today.**

## This is not news to the contract — it is news to the board

`docs/api-contract.md:189` states it outright:

> only its **path** moves, from `/api/v1/people/:id` to `/bff/api/v1/people/:id` … **this is a breaking change for `cv-public-vanilla`, which calls the old path today.**

The contract named the consumer that would break, T-202 shipped the break, and **no task was ever filed to fix the consumer.** That is the gap this task closes.

## Why nothing caught it

**`main.js` has no test.** The repo's only spec is `src/cvCard.test.js`, which covers the pure renderer. The fetch, the URL it builds, and the error branch are untested — so unlike its React sibling ([T-406](T-406-public-react-bff-path-missing-prefix.md)), where a test asserts the *wrong* URL and is green, here there is simply **no check to be wrong**. Same invisible defect, opposite mechanism, and worth recording as such: the board's recurring *"green check that measures nothing"* has a quieter cousin — **no check at all**.

## Why no existing task owns this

Checked before filing, because three tasks come close:

| Task | Touches the URL? | Why it does not own this |
|---|---|---|
| [T-401](T-401-public-cv-sections.md) | Yes — it fetches `/bff/api/v1/people/:id/cv` (path corrected in-file 2026-08-17) | Its scope is **rendering sections**; it would fix this only as a side effect of replacing the fetch. It also `depends_on: [T-201]`-era aggregate work and has never started, so the live defect would sit until then. |
| [T-403](T-403-public-vanilla-deploy.md) | Yes — bakes `VITE_BFF_URL` at build time | `depends_on: [T-014]`, which is unstarted and the expensive one. Its defect is the **localhost fallback in a deployed bundle**, not the path. |
| [T-404](T-404-public-react-point-at-deployed-bff.md) | — | Different repo (cv-public-react), and config-only. |

None of them makes the page work on `master` in the near term. This one does, and it is cheap.

## The ruling this inherits (settled in T-406, do not re-litigate)

**`BFF_URL` is a bare host origin; the code builds `/bff/api/v1/…`.** The alternative — folding the prefix into the env var — was rejected. Evidence:

- The contract (§ *Public edge path*) states the prefix is **not stripped at the edge**, so a given endpoint has one URL and it is the same string in local dev and in AWS.
- Both public sites' `.env.example` hold a bare origin, and a variable named `BFF_URL` reads as a host.
- Folding the prefix into the variable adds a deploy-side half (the baked `VITE_BFF_URL` in T-403, Vercel's project env in T-404) that a green local build would not cover.

**Match cv-public-react.** Two public sites disagreeing about the BFF's public path is a worse outcome than either choice, which is the same reasoning T-406 applied in the other direction.

## Scope

- `src/main.js:10` builds `/bff/api/v1/people/:id`.
- **Add the missing test for `main.js`** — this task must not land the fix with the same blind spot that hid it. Cover the URL that is built and the error branch, with `fetch` stubbed.
- Check `.env.example`, `README`/`CLAUDE.md` and any workflow for stale `/api/v1` references and make all sources agree with the contract.

**Out of scope:** rendering the CV sections ([T-401](T-401-public-cv-sections.md)), deploying this site or baking the deployed BFF URL ([T-403](T-403-public-vanilla-deploy.md)), and any change to cv-bff-node's routing — the BFF is right and the contract agrees with it.

## Acceptance criteria

- [ ] `main.js` requests a path cv-bff-node actually serves, verified against `API_BASE_PATH` in cv-bff-node's source rather than against this repo's docs.
- [ ] A test covers the URL `main.js` builds, and **is proven to fail against the old path** — restore the bug, watch it go red, restore the fix. A new test that cannot fail repeats the defect.
- [ ] The error branch keeps working: a genuine failure still renders the `role="alert"` state.
- [ ] `.env.example` and the repo's docs agree with the code.
- [ ] **Verified against a running stack, not only against a stub** — bring the dev stack up and confirm the page renders the person card instead of its alert state.
- [ ] `npm run lint`, `npm test`, `npm run build` pass.

## Watch-outs

- **Do not widen this into T-401.** The temptation is to switch the fetch to the `/cv` aggregate while here. That is T-401's scope and its renderers are its acceptance criteria; this task fixes the path on the request the site makes **today**.
- `VITE_`-prefixed env vars are inlined at **build** time by Vite — a runtime-only check will not catch a bad bake (that trap is T-403's, recorded there with the Drone empty-string precedent).

## dev-loop notes

- **Developer:** `fullstack-developer`. **Reviewer:** `frontend-architect` (adapter §2 — `cv-public-vanilla` is its review surface). Authoritative CI: **GitHub Actions**.
- `risk: normal`. Small diff, but stage-4 QA against a live stack is **required**, not optional — the runtime behaviour is the entire defect, exactly as in [T-406](T-406-public-react-bff-path-missing-prefix.md).

## Provenance

Found by the driver during [T-406](T-406-public-react-bff-path-missing-prefix.md)'s refinement, 2026-09-22. T-406's scope line instructs the implementer to *"check `cv-public-vanilla` for the same defect and file separately if present — do **not** widen this task into it"* (board rule 3). The check was run at refinement rather than deferred to the developer, because the answer also settled T-406's own open (a)/(b) ruling: the sibling's `.env.example` is a bare origin, which is evidence about what `BFF_URL` means in this workspace.

**Verified by reading both sources**, not inferred: `cv-public-vanilla/src/main.js:10` against `cv-bff-node/src/middleware/auth.ts:20`. Not yet verified against a running stack.
