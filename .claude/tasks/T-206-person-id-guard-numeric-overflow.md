---
id: T-206
title: "The shared person-id guard accepts digit runs that overflow Java Long — 5 upstream calls and a 502 where a 400 belongs"
repo: cv-bff-node
status: todo
owner:
branch: fix/person-id-guard-length-bound
pr:
depends_on: [T-201]   # T-201 ships the guard this changes. Also read T-204, which ADOPTS the same guard — see "Who this affects".
risk: normal
security_review: true   # same reasoning as T-201's ruling 2: the route is anonymous by contract, and this is the guard standing in front of a five-way upstream fan-out
---

## Goal

`src/middleware/validate-person-id.ts` tests `/^[0-9]+$/`. A 300-digit string **is** a run of digits, so it passes — then overflows Java's `Long` upstream. Found by exploratory QA during [T-201](T-201-bff-cv-aggregate.md), 2026-08-27, against the live stack.

Observed end to end, not reasoned about:

```
GET /bff/api/v1/people/999…9/cv   (20 or 300 nines)
  -> guard PASSES
  -> five real upstream calls made
  -> cv-domain-service 400s (Long parse failure)
  -> the BFF's get() maps any non-404 upstream failure to 502
  -> client receives 502
```

Two things are wrong with that, and they are separable:

1. **A client error is reported as a server error.** The caller sent a malformed id; 502 says the BFF's upstream is broken. The contract does not cover this case, so nothing is technically violated — but 502 is the wrong answer to give a public site, and it is the answer that gets paged on.
2. **The guard's whole purpose is not to make the call.** Its own doc comment says an invalid id *"must never reach an upstream URL"*, and here five of them do.

## The part that makes this worth a task

**The guard's comment promises something the code does not deliver**, and that is the specific defect class this board keeps cataloguing — most recently [T-026](T-026-first-build-after-cold-start-fails.md)'s attempt 1, a guard whose failure was indistinguishable from its success. Here the comment reads as an absolute guarantee (*"anything that is not a run of digits is not an id, and must never reach an upstream URL"*) and its own framing is what lets the overflow through: an oversized digit run **is** a run of digits, so the code is faithful to the letter of the comment while defeating its point.

**Fix both halves or neither.** A length bound with the comment left overstating is the same trap one size smaller.

## Who this affects — this is not confined to `/cv`

[T-204](T-204-bff-validate-person-id-param.md) `depends_on` T-201 specifically so it **adopts this shared guard** rather than writing a second implementation. So whatever this task decides propagates to `GET /people/:id` automatically. **Sequencing matters:** if T-204 lands before this, it inherits the weaker guard and nobody re-checks it. Prefer landing this first, or note the interaction in T-204's PR.

## Scope

- Add an upper bound to the guard. **Justify the number rather than picking one** — Java `Long.MAX_VALUE` is 19 digits, so 19 is the natural ceiling and anything above it cannot be a valid id in this system. Decide whether to reject `>19` digits outright or to range-check the parsed value; the second also catches a 19-digit number above `Long.MAX_VALUE`.
- **Rewrite the doc comment so it states what the guard actually guarantees.** No absolute claim the code does not keep.
- Return **400**, consistent with the guard's existing behaviour for other malformed input.

**Out of scope:** the `get()` helper's non-404 → 502 mapping, which is [T-201](T-201-bff-cv-aggregate.md) ruling 4 and correct for genuine upstream failures. This task stops malformed input from reaching it; it does not change what happens when it does.

## Acceptance criteria

- [ ] An over-long digit run returns **400** and makes **no upstream call** — asserted the way T-201's guard tests already are, by confirming `fetch` was never called.
- [ ] The test is **confirmed red before the fix**, per this board's standing practice. The reproduction is trivial: 20 nines.
- [ ] Valid ids at the boundary still work — a 19-digit id at or below `Long.MAX_VALUE` must not be rejected if the chosen approach is a range check, and the choice is recorded either way.
- [ ] **The doc comment no longer makes a guarantee the code does not keep.** This is a real criterion, not a tidy-up: the comment is why the gap survived review, `/security-review` and a falsifiability check.
- [ ] `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` pass.

## Watch-outs

- **Do not "fix" this by widening the regex or parsing with `Number()`.** `Number('1e3')` is 1000 and `parseInt('12abc')` is 12 — both would loosen a guard whose value is that it is strict. The current regex is correct as far as it goes; it needs a bound, not a replacement.
- QA verified the guard's other properties hold (`1abc`, `1;DROP`, `..%2F..%2Fadmin`, `1%20` all 400 with **no upstream request**, confirmed against the domain service's own logs). Do not regress those while adding the bound.

## Definition of done

PR open against `master` from `fix/person-id-guard-length-bound`, GitHub Actions green, task updated.

## dev-loop notes

- **Developer:** `fullstack-developer` (adapter §2 — `cv-bff-node`). **Reviewers:** `/code-review` + `fullstack-developer` + `/security-review`.
- Gates (adapter §3): the `cv-bff-node` row — lint, typecheck, test, build. Authoritative CI: **GitHub Actions**.
- **Small diff, but do not take the trivial fast-path**: it is the guard in front of an anonymous five-way fan-out.

## Provenance

Found by exploratory QA at T-201's stage-4, 2026-08-27, against the live isolated stack — a black-box probe of the guard with an oversized input, which no unit test in T-201 had tried. Filed rather than fixed inside T-201 per board rule 3: T-201's acceptance criteria are its scope and none of them cover numeric overflow. QA classified it low-severity and explicitly **not** a T-201 defect, which is the right call — the contract makes no promise here and the 502 is technically compliant. It is filed because the comment overstates, not because the status code is illegal.
