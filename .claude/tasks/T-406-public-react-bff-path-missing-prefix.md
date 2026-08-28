---
id: T-406
title: "cv-public-react calls the BFF at a path the BFF does not serve — `/api/v1/...` instead of `/bff/api/v1/...` — and its test asserts the wrong URL, so the suite is green"
repo: cv-public-react
status: todo
owner:
branch: fix/bff-public-edge-path
depends_on: []
risk: normal
security_review: false   # no auth or exposure change; a wrong path returns 404, it does not widen access
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
