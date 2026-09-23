---
id: T-406
title: "cv-public-react calls the BFF at a path the BFF does not serve — `/api/v1/...` instead of `/bff/api/v1/...` — and its test asserts the wrong URL, so the suite is green"
repo: cv-public-react
status: done
owner: fullstack-developer
branch: fix/bff-public-edge-path
pr: https://github.com/erfeamor/cv-public-react/pull/5
depends_on: []
risk: normal
security_review: false   # no auth or exposure change; a wrong path returns 404, it does not widen access
checkpoint:
  stage: done   # merged 357d830 (squash of #5), 2026-09-22
  pr: https://github.com/erfeamor/cv-public-react/pull/5
  qa: pass   # stage 4 executed 2026-09-22 against cvdl_t-406, driver-verified
  repo: cv-public-react
  branch: fix/bff-public-edge-path
  developer: fullstack-developer
  commit: 357d830   # squash merge on master (branch commit was 15239f9)
  reviewers: [code-review, frontend-architect]
  risk: normal
  security_review: false
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  ruling: "(a) BFF_URL is a bare origin; the repository builds /bff/api/v1/... — settled at refinement, evidence in the task body"
  filed_from_refinement: [T-408]
---

## The defect

`src/infrastructure/BffCvRepository.ts:64` builds:

```ts
const url = `${this.baseUrl}/api/v1/people/${personId}/cv`;
```

With `BFF_URL=http://localhost:3000` (the `.env.example` value and the code's own default) that resolves to `http://localhost:3000/api/v1/people/1/cv`.

**cv-bff-node does not serve that path.** `src/middleware/auth.ts:20` sets `API_BASE_PATH = '/bff/api/v1'`, and `src/app.ts:31-32` mounts **both** routers there and nowhere else. [T-202](T-202-bff-public-routing-and-auth.md) removed the old `/api/v1` base deliberately — cv-bff-node's own `CLAUDE.md` records it: *"The old `/api/v1` base is removed, not dual-mounted — it belongs to cv-domain-service at the edge."*

So against a locally-running stack this site gets a **404**, `BffCvRepository` throws `CvFetchError`, and `app/page.tsx` renders its `role="alert"` failure state. The whole page is the error path.

## Why nothing caught it

**The test asserts the wrong URL.** `src/infrastructure/BffCvRepository.test.ts:61`:

```ts
expect(url).toBe('http://bff.test/api/v1/people/1/cv');
```

It pins the buggy path as if it were correct, so the suite is green and stays green. `global.fetch` is mocked, so no real request is ever made and the mismatch cannot surface. This is the board's recurring **green check that measures nothing** — compare [T-405](T-405-public-react-null-optionals.md), [T-207](T-207-public-types-derived-from-domain-interfaces.md), [T-205](T-205-bff-allowlist-section-normalizers.md), [T-028](T-028-qa-env-generator-worktree-build-context.md).

**And the repo's own docs encode the error too**, so a reader checking the code against the docs finds agreement: `cv-public-react/CLAUDE.md` describes the fetch as `${BFF_URL}/api/v1/people/:id/cv` in two places.

## The one thing to settle first

**Is `BFF_URL` meant to carry the `/bff` prefix?** Both readings are defensible and they lead to different fixes:

- **(a) The path is wrong** — `BFF_URL` is a host origin (which is what `http://localhost:3000` and the name suggest), and the repository should build `/bff/api/v1/...`. Fix the code, the test, and `CLAUDE.md`.
- **(b) The base URL is wrong** — `BFF_URL` is meant to include the edge prefix, and `.env.example` should read `http://localhost:3000/bff`. Fix the config and the docs.

**Recommendation: (a).** `cv-public-vanilla` is the sibling consumer of the same endpoint — check what it does and match it, because two public sites disagreeing about the BFF's public path is a worse outcome than either choice. The contract (§ BFF) spells the public edge as `/bff/api/v1`, and a variable named `BFF_URL` defaulting to a bare origin reads as a host.

Whichever is chosen, **`.env.example`, `CLAUDE.md` and the test must end up agreeing with the code** — three of the four currently agree with each other and are wrong.

## Scope

- Settle (a) vs (b), then make the URL correct end-to-end.
- **Correct the test so it asserts the real path.** Changing the assertion to match the code is not a fix — this task exists because that is exactly what the test does today.
- Update `cv-public-react/CLAUDE.md`'s two `${BFF_URL}/api/v1/...` mentions and `.env.example` if (b).
- Check `cv-public-vanilla` for the same defect and file separately if present — do **not** widen this task into it.

**Out of scope:** deploying or pointing at a deployed BFF ([T-404](T-404-public-react-point-at-deployed-bff.md)), and any change to cv-bff-node's routing — the BFF is right and the contract agrees with it.

## Acceptance criteria

- [ ] `BffCvRepository` requests a path cv-bff-node actually serves, verified against `API_BASE_PATH` in cv-bff-node rather than against this repo's docs.
- [ ] The URL assertion in `BffCvRepository.test.ts` matches the corrected path.
- [ ] `.env.example` and `CLAUDE.md` agree with the code.
- [ ] **Verified against a running stack, not only against a mock** — `docker compose -f docker-compose.dev.yml up` in the meta repo, then confirm this site renders the person head instead of its `role="alert"` failure state. A mocked-fetch test cannot prove this defect is fixed, because a mocked-fetch test is what hid it.
- [ ] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass.

## Watch-outs

- **Do not "fix" this by relaxing the test.** The failure mode here *is* a test written to agree with the code instead of with the contract.
- If (b) is chosen, remember Vercel's Project Environment Variables hold `BFF_URL` in production — a config-only fix has a deploy-side half that a green local build will not cover ([T-404](T-404-public-react-point-at-deployed-bff.md) owns that wiring).

## dev-loop notes

- **Developer:** `fullstack-developer`. **Reviewer:** `frontend-architect` (adapter §2 — `cv-public-react` is its review surface). Authoritative CI: **Vercel**.
- `risk: normal`. Small diff, but stage-4 QA against a live stack is **required** here rather than optional — see AC4. This is the opposite of [T-405](T-405-public-react-null-optionals.md)'s stage 4, where a live stack was skipped with evidence because the change had no runtime delta; here the runtime behaviour is the entire defect.

## Provenance

Found by the driver during [T-405](T-405-public-react-null-optionals.md), 2026-08-28, while correcting the stale `/api/v1/people/:id/cv` path in `src/domain/cv.ts`'s header comment. Correcting the *comment* prompted checking whether the *code* had the same error; it does. Filed rather than folded into T-405 per board rule 3 — T-405's acceptance criteria are types and null coverage, and this is a routing defect that needs live verification T-405 explicitly argued it did not need.

**Not yet verified against a running stack** — the mismatch is read off `API_BASE_PATH` in cv-bff-node's source and the URL cv-public-react constructs. The (a)/(b) question above is exactly the uncertainty that reading cannot settle.

---

## Test plan (QA)

Authored by `quality-assurance` at refinement, 2026-09-22 — the plan it executes at stage 4. Facts below were **re-verified by the driver** against the files named, because a test plan that is wrong about the fixture is a plan that passes for the wrong reason.

### 0. Fixed facts this plan rests on (all verified)

| Fact | Source | Verified |
|---|---|---|
| Corrected path `GET {BFF_URL}/bff/api/v1/people/:id/cv`, `BFF_URL` a bare origin | contract § *Public edge path*; ruling (a) below | ✔ |
| BFF runs with no JWT locally | `docker-compose.dev.yml:58,70` — `AUTH_ENABLED: "false"` | ✔ |
| Seed person 1 = `Jane Doe` / `Full-Stack Engineer` / `Remote` | `cv-database/sql/dev-seeds/afterMigrate__seed_dev.sql:5-6` | ✔ |
| Failure state is `<p role="alert" className="load-error">` | `cv-public-react/app/page.tsx:24` | ✔ |
| `npm start` **already** binds 4300 (`next start -p 4300`) | `cv-public-react/package.json` | ✔ — do **not** pass `-- -p 4300` again |
| Isolated stack slot 0 → BFF **3010**, domain **8090**, MySQL **3316** | `scripts/qa-env-override.py` | ✔ |

**AC4 substitution, recorded not silently taken.** AC4 names the base `docker compose -f docker-compose.dev.yml up`. QA substitutes the isolated per-task stack (`qa-env-override.py`, slot 0) so a parallel run cannot collide on ports or volumes. Same endpoint, port-shifted — equivalent-or-stronger evidence for the same criterion. Noted here so a later reader does not find the criterion quietly reinterpreted.

### 1. Unit level — including the falsification step

```bash
cd /home/erfeamor/work/curriculum/cv-public-react
npm test -- BffCvRepository
```

Expect green, with the assertion reading `expect(url).toBe('http://bff.test/bff/api/v1/people/1/cv')`.

**Falsification is mandatory — it is the whole point of this task.**

```bash
cd /home/erfeamor/work/curriculum/cv-public-react
git diff HEAD -- src/infrastructure/BffCvRepository.ts   # confirm the fix is the one line touched
git stash push -- src/infrastructure/BffCvRepository.ts  # revert SOURCE only, keep the corrected test
npm test -- BffCvRepository                              # EXPECT RED, on the URL assertion specifically
git stash pop
npm test -- BffCvRepository                              # EXPECT GREEN again
```

**PASS criterion:** the stashed run fails *on the `expect(url).toBe(...)` line*, not on an unrelated error. If it stays green with the old path restored, the test is still measuring nothing and the task is **not done** regardless of what the assertion string says. (Board lineage: T-405, T-207, T-205, T-028 — and T-201, where the first falsification attempt itself passed.)

### 2. Live stack — AC4, mandatory here

```bash
cd /home/erfeamor/work/curriculum
python3 scripts/qa-env-override.py --task T-406 --slot 0 --json   # confirm endpoints.bff == localhost:3010
COMPOSE_PROJECT_NAME=cvdl_t-406 docker compose \
  -f docker-compose.dev.yml -f docker-compose.override.cvdl_t-406.yml up --build -d
curl -i http://localhost:3010/bff/api/v1/people/1/cv
```

Expect `HTTP/1.1 200` and `"name":"Jane Doe"`. **This step is deliberately separate**: it isolates *"does the BFF serve this path at all"* from *"does the frontend build the right URL"*, so a failure here cannot be misread as a frontend bug.

```bash
cd /home/erfeamor/work/curriculum/cv-public-react
cp .env.example .env
sed -i 's#^BFF_URL=.*#BFF_URL=http://localhost:3010#' .env
npm run build
npm start &                       # already binds 4300 — do NOT add -- -p 4300
curl -s http://localhost:4300/ | grep -c 'role="alert"'      # EXPECT: 0
curl -s http://localhost:4300/ | grep -o '<h1>[^<]*</h1>'    # EXPECT: <h1>Jane Doe</h1>
```

**Evidence to capture:** the full `curl -i` of the BFF call and the rendered HTML showing `Jane Doe` / `Full-Stack Engineer` / `Remote`. Attach both to the QA record. This is the PASS state, contrasted against the documented current FAIL (the whole page being the `role="alert"` branch).

Teardown:

```bash
pkill -f "next start" 2>/dev/null
cd /home/erfeamor/work/curriculum
COMPOSE_PROJECT_NAME=cvdl_t-406 docker compose \
  -f docker-compose.dev.yml -f docker-compose.override.cvdl_t-406.yml down -v
```

### 3. Negative / edge probes

- **A genuine 404 must still render the alert.** `curl -i http://localhost:3010/bff/api/v1/people/999999/cv` → expect `404` (contract design rule 4). Then set `PERSON_ID=999999` in `.env`, restart, reload — `role="alert"` **must** appear. The error path is a feature; this task must not collapse it into always-green.
- **Dual-mount guard.** `curl -i http://localhost:3010/api/v1/people/1/cv` (the *old* path) → expect `404`, confirming `/bff` is genuinely required and the old base was removed, not dual-mounted.
- **No stale reference survives.** `grep -rn "api/v1/people" cv-public-react --include='*.ts' --include='*.tsx' --include='*.md' | grep -v node_modules` → every hit reads `/bff/api/v1/people/...`.

### 4. Consistency across the four named sources

`BffCvRepository.ts` · `BffCvRepository.test.ts` · `.env.example` · `CLAUDE.md` (**lines 4 and 43**). PASS when all agree with the contract and none still reads the bare `/api/v1/...`. Note `.env.example` needs **no change** under ruling (a) — it is already a bare origin, and that is evidence *for* the ruling.

### 5. Full local gate (AC5)

```bash
cd /home/erfeamor/work/curriculum/cv-public-react
npm run lint && npm run typecheck && npm test && npm run build
```

### QA's notes on the criteria as written

- **AC1** is an inspection instruction, not an assertion. Made concrete: grep the literal `API_BASE_PATH` value in `cv-bff-node/src/middleware/auth.ts`, diff it against the string built in `BffCvRepository.ts`, then subsume it under the live `200`.
- **AC4** — see the substitution recorded in §0.
- Everything else is directly executable as written.

---

## QA record — stage 4, 2026-09-22 (PASS)

Executed by the `quality-assurance` instance that authored the plan above, against the isolated stack `cvdl_t-406` (slot 0, BFF `:3010`). **Run ahead of stage 3** — the PR could not be opened because the local SSH agent refused to sign (`agent refused operation`), and the live-stack criterion does not depend on the PR. The reordering is recorded rather than quietly taken.

Key results, each **re-verified by the driver** rather than accepted on report:

| Check | Result |
|---|---|
| `GET :3010/bff/api/v1/people/1/cv` | **200**, `{"name":"Jane Doe",…}` |
| `GET :3010/api/v1/people/1/cv` (old path) | **404** — prefix required, not dual-mounted |
| `GET :3010/bff/api/v1/people/999999/cv` | **404** |
| Site renders (`PERSON_ID=1`) | `<h1>Jane Doe</h1>` + headline/location/summary; **no `role="alert"`** |
| Site renders (`PERSON_ID=999999`) | `role="alert"` present, **no `<h1>` at all** |
| Repo-wide `api/v1/people` grep | 5 hits, all `/bff/api/v1/…` |

**The AC4 criterion is met by the second and fifth rows together, not by the second alone.** A fix that made the page render could also have been a fix that made it *always* render; the unknown-id probe is what rules that out. `npm run build` prerendered the page against the live BFF, so the fetch is proven to resolve during ISR generation, not only at request time.

**Five sources, not four.** The plan's §4 consistency check named four; `README.md:61` carried the same stale path and was found by the developer unprompted. All five now agree with the contract. Recorded because the task body, the test plan and the original finding all under-counted the doc drift by one — the defect was one file wider than any of the three sources that described it.

No defects; no bounce-back. Working tree clean throughout (`.env` is gitignored and was the only file QA wrote).
