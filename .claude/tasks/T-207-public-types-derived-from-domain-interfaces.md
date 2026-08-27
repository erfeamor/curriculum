---
id: T-207
title: "BFF: the aggregate's Public* types are derived from the Domain* interfaces they exist to distrust — the allowlist's compile-time guarantee fails in both directions"
repo: cv-bff-node
status: todo
owner:
branch: fix/public-types-from-contract
pr:
depends_on: [T-205]   # T-205 writes the allowlists this bounds. The finding is about the types those rebuilds are checked against.
risk: normal
security_review: true   # same reasoning as T-205: the route is ANONYMOUS by contract (T-013), and the leak direction below lands on it
---

## Goal

`src/routes/cv.ts:66-69` defines the four public types by subtracting from the domain ones:

```ts
type PublicExperience = Omit<DomainExperience, 'id'>;
type PublicEducation  = Omit<DomainEducation, 'id'>;
type PublicSkill      = Omit<DomainSkillAssignment, 'skillId'>;
type PublicProject    = Omit<DomainProject, 'id'>;
```

So `tsc` checks T-205's field-by-field rebuilds against the **domain** shape — the very shape this code exists to stop trusting. Spell the four `Public*` types as standalone interfaces transcribed from `docs/api-contract.md` instead, so the compiler checks the public payload against the contract rather than against the upstream.

## Why this is worth a task

**T-205 made the runtime an allowlist. The types are still a denylist**, and its comment overstates what the compiler enforces: *"the cost is that a new CONTRACT field needs an edit in this file"*. Neither direction actually holds. Both were confirmed empirically against `b6fd1f6` during T-205's review round 1, by the reviewer and again by the driver:

- **Leak direction.** Adding a required `personId: number` to `DomainSkillAssignment` makes `PublicSkill` *require* it too, and the build fails:
  `src/routes/cv.ts(115,64): error TS2741: Property 'personId' is missing in type '{ name: string; category: string | undefined; proficiency: string; }' but required in type 'PublicSkill'.`
  The error points at `stripSkill`, and the path of least resistance under compiler pressure is to add `personId: s.personId` — **reintroducing exactly the disclosure T-205 removed, on the anonymous route, with a green build.** T-205's own premise is that someone will eventually update the domain interfaces to match what cv-domain-service really sends, so this is a *scheduled* event, not a hypothetical.
- **Drop direction.** Adding an *optional* `techStack?: string` to `DomainProject` typechecks **clean** with `stripProject` unchanged — the newly contracted field is silently absent from the public payload, with no compile error and no failing test. Every optional field in these sections (`location`, `description`, `fieldOfStudy`, `category`, `repoUrl`, project `startDate`) sits in that same blind spot.

This is the board's recurring **"green check that measures nothing"** shape once more — the compiler looks like it is guarding the public payload and is in fact guarding conformance to the upstream. Related: [T-205](T-205-bff-allowlist-section-normalizers.md) (the runtime half, merged), [T-107](T-107-post-id-cross-person-write.md), [T-109](T-109-ordering-tiebreak-unevidenced-siblings.md), [T-028](T-028-qa-env-generator-worktree-build-context.md).

## Scope

- Replace the four `Omit<Domain*, …>` aliases with standalone `interface` declarations whose fields are transcribed from `docs/api-contract.md` §§ Experience, Education, Projects, Skills — **not** from the `Domain*` interfaces above them.
- Correct the comment T-205 added so it describes the guarantee the code actually keeps.
- **Add a type-level regression guard** so the leak direction cannot come back silently: a test (or a `tsd`-style compile assertion, or a deliberate `// @ts-expect-error`) proving that an undeclared field added to a `Domain*` interface does **not** propagate into the corresponding `Public*` type.

**Out of scope:** the runtime normalizers themselves — T-205 already made them allowlists and this task must not change their behavior. The four leak tests and the sparse test it added must pass unchanged.

## Acceptance criteria

- [ ] The four `Public*` types are standalone interfaces spelled from the contract; no `Omit<Domain*, …>` remains in `src/routes/cv.ts`.
- [ ] Adding a required field to any `Domain*` interface produces **no** error in the corresponding `strip*` function (proving the public type no longer tracks the domain one). Demonstrate this in the PR the way T-205 demonstrated its red-before-green.
- [ ] A newly added optional **contract** field is a compile error until the matching `strip*` copies it — the drop direction is closed.
- [ ] The public payload is byte-identical: T-205's four leak tests, its sparse test, and T-201's contract-shape and no-leak tests all pass **unchanged**.
- [ ] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass.

## Watch-outs

- The `Domain*` interfaces stay as they are — they describe the upstream and that is their job. Only the `Public*` side is transcribed from the contract.
- Do not weaken T-201's contract-shape test to make the new types fit; if they disagree, the contract wins and the types are wrong.

## dev-loop notes

- **Developer:** `fullstack-developer` (adapter §2 — `cv-bff-node`). Gates: the `cv-bff-node` row of adapter §3. Authoritative CI: **GitHub Actions**.
- `risk: normal`. Small diff, but it is the compile-time guard on an anonymous public payload.

## Provenance

Raised by `/code-review` (effort `high`) during [T-205](T-205-bff-allowlist-section-normalizers.md)'s review round 1, 2026-08-27, as a **LOW, explicitly non-blocking** finding. Both directions were then re-verified independently by the driver before filing. Filed rather than absorbed into T-205 per board rule 3: T-205's scope note says *"Keep the public types as they are — they already describe the intended shape correctly"*, and its acceptance criteria are its scope. That scope note is precisely what this task revisits — the types describe the intended shape, but they are **derived** in a way that does not hold it.
