---
id: T-407
title: "cv-public-react's domain types now assert `null`-not-absent, but `toCv` never establishes it — the adapter defends the arrays and leaves every scalar undefended"
repo: cv-public-react
status: todo
owner:
branch: fix/tocv-null-invariant
depends_on: [T-405]   # T-405 declares the invariant; this makes it true at runtime
risk: normal
security_review: false
---

## The gap

[T-405](T-405-public-react-null-optionals.md) retyped all ten contract-optional fields to `string | null`, asserting **the key is always present**. Nothing establishes that at runtime:

```ts
return toCv((await response.json()) as CvDto);   // unchecked cast, no validation
```

and `toCv` copies the scalars straight through:

```ts
headline: dto.headline,        // no `?? null`
location: dto.location,
summary:  dto.summary,
experiences: dto.experiences ?? [],   // arrays ARE defended
```

**The adapter already defends the four section arrays with `?? []` and leaves every scalar undefended.** That asymmetry is the whole finding: the same author, in the same function, guarded one kind of absence and not the other.

Worse for the sections — `toCv` copies `dto.experiences ?? []` **verbatim**, never touching the objects inside, so `location`, `description`, `fieldOfStudy`, `category`, `repoUrl` and `startDate` get no normalization at all.

## Why it matters, concretely

If the producer ever omits a key, `cv.headline` is `undefined` while typed `string | null`. A consumer written **to the ratified contract** then takes the wrong branch:

- `person.headline === null` → `false` for `undefined`, so an absent value is treated as present.
- `project.startDate === null` → `false`, and the *"undated projects last"* rule (contract § Ordering) silently misclassifies the row.

Those are the exact comparisons contract rule 7 invites a consumer to write — the rule says *"a consumer may assume the key exists and must handle `null`"*.

## The distinction that makes this correct here and WRONG in the BFF

[T-210](T-210-bff-domain-types-null-not-absent.md) explicitly **forbade** `?? null` in `cv-bff-node`, and that ruling stands. The two are not in tension:

| | cv-bff-node | cv-public-react |
|---|---|---|
| role | **pass-through**: rebuilds the public payload from the upstream | **anti-corruption layer**: maps a wire format into a domain model |
| effect of `?? null` | **fabricates data on the wire** — invents a `null` the producer never sent, changing what every downstream consumer receives | **normalizes into this app's own domain invariant** — nothing leaves the process |
| what the contract says | rule 7 is *"inherited from the producer, not enforced by the BFF"* | a consumer *"may assume the key exists"* — this adapter is where that assumption is made safe |

`BffCvRepository`'s own doc comment already claims this role: *"this adapter still owns the mapping so the domain never depends on the wire format, and it defends against missing section arrays."* It should defend against missing scalars for the same reason and in the same place.

## Scope

- `toCv`: `?? null` on the three head scalars.
- **Per-section mapping** for the nested optionals — `location`, `description`, `fieldOfStudy`, `category`, `repoUrl`, `startDate`. This is the part that is not a one-liner: `toCv` currently does not map inside the arrays at all, so this adds four small element mappers.
- A test driving a payload with keys genuinely **omitted** (not null) and asserting the domain `Cv` comes back with `null` — the mirror of T-405's all-null fixture. It must fail before the change.

**Out of scope:** adding a validation library (zod &c.) — this is normalization, not schema validation, and a dependency is a separate decision with its own bundle cost. Also out of scope: any change to `cv-bff-node`, whose behaviour is correct and deliberate.

## Acceptance criteria

- [ ] Every field the domain types declare `string | null` is `null`, never `undefined`, after `toCv` — for all ten, including the six nested in sections.
- [ ] A test feeds a payload with those keys **absent** and asserts `null` on each; it fails against `master`.
- [ ] The four `?? []` array defenses still work, and T-405's all-null fixture test passes unchanged.
- [ ] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass.

## Watch-outs

- **`?? null`, not `|| null`.** `||` would collapse a legitimate empty string to `null`, erasing a real value — the same mistake [T-210](T-210-bff-domain-types-null-not-absent.md)'s head-route test was written to catch.
- Do not "fix" this by loosening the domain types back to `string | null | undefined`. That would restore the imprecision the whole T-209/T-210/T-405 line removed, and would push the null-check onto every future component instead of the one adapter.

## Consider doing this together with [T-406](T-406-public-react-bff-path-missing-prefix.md)

Both live in `src/infrastructure/BffCvRepository.ts`, both need the same live-stack verification, and T-406 is what makes this reachable in practice — while the fetch path is wrong the page never renders anything but its error state, so neither defect is observable end-to-end. Separate task files because they are separate defects (routing vs. mapping invariant), but one PR is defensible and cheaper.

## dev-loop notes

- **Developer:** `fullstack-developer`. **Reviewer:** `frontend-architect` (adapter §2). Authoritative CI: **Vercel**.
- `risk: normal`.

## Provenance

Raised by `/code-review` (effort `medium`) during [T-405](T-405-public-react-null-optionals.md)'s review round 1, 2026-08-28, as a **MEDIUM** finding. Filed rather than absorbed per board rule 3: T-405's scope says in as many words that *"any change to `toCv`'s mapping"* is out of scope. Direct precedent — [T-207](T-207-public-types-derived-from-domain-interfaces.md) was filed out of [T-205](T-205-bff-allowlist-section-normalizers.md) for exactly this reason, and revisiting the earlier task's scope note was the whole point of it.

The finding is nonetheless a real instance of the board's recurring shape, one level up from where T-405 found it: **T-405 made a type stronger without making it true.**
