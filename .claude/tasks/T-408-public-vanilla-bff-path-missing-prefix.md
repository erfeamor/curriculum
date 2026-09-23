---
id: T-408
title: "cv-public-vanilla calls the BFF at `/api/v1/…`, a path the BFF no longer serves — the landing page is broken today, and `main.js` has no test at all"
repo: cv-public-vanilla
status: done
owner: fullstack-developer
branch: fix/bff-public-edge-path
pr: https://github.com/erfeamor/cv-public-vanilla/pull/3
depends_on: []
risk: normal
security_review: false   # no auth or exposure change; a wrong path returns 404, it does not widen access
checkpoint:
  stage: done   # merged 0acd7fc (squash of cv-public-vanilla#3), 2026-09-24 — H2 accepted by the human
  repo: cv-public-vanilla
  branch: fix/bff-public-edge-path
  worktree: none   # removed after merge
  developer: fullstack-developer
  reviewers: [code-review, frontend-architect]
  risk: normal
  security_review: false
  commit: 0acd7fc   # squash merge on master (branch commit was 6621ded)
  pr: https://github.com/erfeamor/cv-public-vanilla/pull/3
  qa: pass   # stage 4, cvdl_t-408, headless Chromium
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: 0
  wave: [T-023, T-408, T-208]   # 2026-09-24 wave, human-requested
  updated: 2026-09-24T11:40:00+02:00
  budget:
    turns: 445
    total_tokens: 125733638
    subagent_tokens: 204000
    spawns: 3
    status: soft   # 83.8% of ceiling_total_tokens — ask before starting merge
    checked: 2026-09-24T11:40:00+02:00
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

## Test plan (QA)

Authored by `quality-assurance` at refinement, 2026-09-24 — the plan it executes at stage 4. Facts re-verified by QA against `origin/master`, and the load-bearing ones re-checked by the driver the same day (CORS default and compose value, generator slug lowercasing, `cv-bff-node` checkout on `master`, `:4173` free).

> **Driver amendments before filing (2026-09-24) — they override the plan text where the two disagree.**
> 1. **Nothing in this plan writes to the reviewed tree.** QA drafted the falsification as `git stash` inside the repo and the live build as `.env` + `npm run build` in the main checkout. Both would mutate code under review (QA is read-only; the developer is the only writer) and the second targets the main checkout, not the task's worktree. **Both now run in a disposable clone** of the worktree branch in the QA scratchpad: `git clone --local --branch fix/bff-public-edge-path /home/erfeamor/work/cvdl-worktrees/t-408 <scratch>/t-408-qa`.
> 2. **Falsification** = in a second disposable clone at `origin/master`, copy the new `src/main.test.js` from the branch in (`git show fix/bff-public-edge-path:src/main.test.js`), run it, and watch it fail **on the URL assertion line**. Never by reverting the fix in place.

### 0. Fixed facts

| Fact | Source |
|---|---|
| Defect: `main.js:10` builds `${BFF_URL}/api/v1/people/${PERSON_ID}`; `BFF_URL` a bare origin defaulting to `http://localhost:3000` | `src/main.js:3,10` |
| BFF mounts only `/bff/api/v1` | `cv-bff-node/src/middleware/auth.ts:20`, `src/app.ts` |
| BFF passes the upstream status through on `/people/:id`, so an unknown id genuinely 404s | `cv-bff-node/src/routes/people.ts:71` |
| Error render: `<p role="alert">Could not load résumé: ${err.message}</p>` | `src/main.js:17` |
| `git ls-files \| xargs grep -ln "api/v1"` — no extension filter — hits **only** `src/main.js`; `.env.example` is already a bare origin per the ruling | live |
| No headless-browser tooling in the repo; Playwright's Chromium installs and launches here | `package.json`; live check |
| **CORS allowlist is the fixed string `http://localhost:4173`** — `cv-bff-node/src/app.ts:14` default and `docker-compose.dev.yml:69`; the generator shifts host ports only, never service env | driver-verified |
| Seed person 1 = Jane Doe / Full-Stack Engineer / Remote | `cv-database/sql/dev-seeds/afterMigrate__seed_dev.sql:6` |
| Slot 0 → BFF `:3010`, domain `:8090`, MySQL `:3316` | `scripts/qa-env-override.py` |

**This site is client-rendered** (`index.html` ships a bare `#app`; `main.js` fetches in the browser), so — unlike T-406 — a `curl` of `/` returns the same static shell whether or not the fix landed. AC5 needs a real JS runtime: headless Chromium. **The frontend must be served from origin `http://localhost:4173`** or CORS fails for reasons unrelated to this fix. `:4173` is also the human's own public-site dev port — confirm it is free (`ss -ltn | grep ':4173 '`), keep the window short, and if it is occupied, **stop and report** rather than move ports.

### 1. Unit level — `src/main.test.js`, `fetch` stubbed

- **Exact URL:** `fetch` called with `http://localhost:3000/bff/api/v1/people/1` (or the test-env `VITE_*` values). This is the assertion falsification must hit.
- **Happy path:** `{ok:true, json}` → `#app` contains the name; no `role="alert"`.
- **Non-2xx:** `{ok:false, status:404}` → `role="alert"` with `Could not load résumé: BFF responded with 404`.
- **Network throw:** `fetch` rejects → `role="alert"` still renders.
- **Falsification (AC2):** per amendment 2. **PASS only if it fails on the URL assertion** — a red from a missing `#app` or an import error does not count.

### 2. Live stack (slot 0) — AC5

```bash
cd /home/erfeamor/work/curriculum
python3 scripts/qa-env-override.py --task t-408 --slot 0 --smoke bff:/bff/api/v1/people/1   # then its printed `up`
curl -i http://localhost:3010/bff/api/v1/people/1        # expect 200, "name":"Jane Doe"
```
In the disposable clone (amendment 1): `VITE_BFF_URL=http://localhost:3010` in `.env`, `npm ci && npm run build`, then `grep -o 'localhost:3010[^"'"'"']*' dist/assets/*.js` to prove the bake (Vite inlines `VITE_*` at build time). `npm run preview -- --port 4173 --strictPort &`, then a throwaway Playwright script (in the scratchpad) that loads `http://localhost:4173/`, waits for the fetch to settle, and prints the `[role="alert"]` count and `#app` HTML.

**PASS:** alert count `0`, and `#app` contains `Jane Doe`, `Full-Stack Engineer`, `Remote`. **FAIL:** an alert, or an empty `#app` — the current-`master` behaviour.

### 3. Negative probes — AC3

- **Unknown id:** `curl -i :3010/bff/api/v1/people/999999` → `404`; rebuild the disposable clone with `VITE_PERSON_ID=999999`, reload → alert count `1`, no card. Rules out "renders *something* regardless".
- **No dual mount:** `curl -i :3010/api/v1/people/1` → `404`.
- Bonus: `curl -i :3010/bff/api/v1/people/not-a-number` → `400`.

### 4. Consistency sweep — AC4

`git ls-files | xargs grep -n "api/v1"` in the worktree → PASS when the only hit is `src/main.js` reading `/bff/api/v1/…`. Expected to need **no doc edit** (`.env.example` already a bare origin) — record the zero-diff outcome explicitly so it does not read as unchecked. Anything new beyond `main.js` is drift to flag, not silent scope.

### 5. Gates — AC6

In the worktree: `npm run lint && npm test && npm run build`. GitHub Actions green — statuses API, not `gh pr checks`.

Teardown: stop the preview, the printed `down -v`, delete the scratch clones. Slot 1 (T-208) untouched.

## QA record — stage 4, 2026-09-24 (PASS)

Executed by the `quality-assurance` instance that authored the plan, with the driver amendments (two `--local` disposable clones, no `git stash`), against `cvdl_t-408` (slot 0, BFF `:3010`; BFF and domain built from `master` — correct, this task touches no BFF code). Driver spot-checked teardown, `:4173` release and PR head afterwards.

| AC | Result | Evidence |
|---|---|---|
| 1 path | PASS | `main.js:10` → `/bff/api/v1/people/:id`; live `GET :3010/bff/api/v1/people/1` → 200 Jane Doe |
| 2 falsification | PASS | origin/master clone + the branch's `main.test.js`: **exactly 1 of 4 fails, at `main.test.js:36`** (`…/api/v1/people/1` vs `…/bff/api/v1/people/1`); the 3 rendering tests pass on both, as expected |
| 3 error branch | PASS | live id `999999` → BFF 404 → alert count 1, `#app` = the alert text only, no card |
| 4 consistency | PASS | `git ls-files \| xargs grep -n "api/v1"` → 3 hits, all `/bff/api/v1` (`main.js:10`, `main.test.js:30`, `:36`); docs/`.env.example`/CI zero-diff, as predicted |
| 5 live render | PASS | bake confirmed in `dist/`; `vite preview --port 4173 --strictPort`; headless Chromium: **id 1 → alert count 0, full card (Jane Doe / Full-Stack Engineer / Remote)**, no page errors; CORS origin matched |
| negative probes | PASS | old `/api/v1/people/1` → 404 (no dual mount); `/bff/api/v1/people/not-a-number` → 400 |
| 6 gates | PASS | lint, 7/7, build; GitHub Actions `test` success on `6621ded` |
| teardown | PASS | no `cvdl_t-408` containers, override removed, scratch clones deleted, `:4173` released |

No defect bounced. `qa_bounces: 0`.

**Carried forward from review (non-blocking, not this task's scope):** a trailing slash in `VITE_BFF_URL` would produce `//bff/…` — T-403 sets that value at deploy time and should carry the same AC T-404 carries for the React site. Both reviewers also noted `main.js:17` interpolates `err.message` into `innerHTML` unescaped — pre-existing, not user-controlled today.

## Watch-outs

- **Do not widen this into T-401.** The temptation is to switch the fetch to the `/cv` aggregate while here. That is T-401's scope and its renderers are its acceptance criteria; this task fixes the path on the request the site makes **today**.
- `VITE_`-prefixed env vars are inlined at **build** time by Vite — a runtime-only check will not catch a bad bake (that trap is T-403's, recorded there with the Drone empty-string precedent).

## dev-loop notes
- **Blocks [T-401](T-401-public-cv-sections.md) and [T-403](T-403-public-vanilla-deploy.md)** (edges added 2026-09-23, board review): both edit `src/main.js`, and T-401 extends the test this task adds. Through T-401 it also gates [T-501](T-501-e2e-cv-milestone.md). Still do not widen into either.

- **Developer:** `fullstack-developer`. **Reviewer:** `frontend-architect` (adapter §2 — `cv-public-vanilla` is its review surface). Authoritative CI: **GitHub Actions**.
- `risk: normal`. Small diff, but stage-4 QA against a live stack is **required**, not optional — the runtime behaviour is the entire defect, exactly as in [T-406](T-406-public-react-bff-path-missing-prefix.md).

## Provenance

Found by the driver during [T-406](T-406-public-react-bff-path-missing-prefix.md)'s refinement, 2026-09-22. T-406's scope line instructs the implementer to *"check `cv-public-vanilla` for the same defect and file separately if present — do **not** widen this task into it"* (board rule 3). The check was run at refinement rather than deferred to the developer, because the answer also settled T-406's own open (a)/(b) ruling: the sibling's `.env.example` is a bare origin, which is evidence about what `BFF_URL` means in this workspace.

**Verified by reading both sources**, not inferred: `cv-public-vanilla/src/main.js:10` against `cv-bff-node/src/middleware/auth.ts:20`. Not yet verified against a running stack.
