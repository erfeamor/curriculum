---
id: T-152
title: "Dev/CI parity: bump cv-database's local stack and migration gate to MySQL 8.4"
repo: cv-database
status: done
owner: backend-developer
branch: chore/mysql-84-parity-ci
pr: https://github.com/erfeamor/cv-database/pull/3
depends_on: []
risk: normal
security_review: true   # adapter §5 — the diff touches `Jenkinsfile`, which is CI config and an unconditional /security-review path. This is the flag that made the task un-mergeable into T-016 (security_review: false); see Provenance.
checkpoint:
  stage: done                  # H2 ratified 2026-08-22; merged as 5942881
  merged: 5942881
  worktree:                    # CLEARED at close-out -- T-028's generator exits 1 on a closed task that still declares a path. This is the convention T-028 made load-bearing.
  outstanding: "CI-console version proof (Flyway banner from Jenkins PR-3 build #2) was NEVER obtained -- the console is authenticated and the credential path was declined. Merged with the gap named in the PR at the human's H2 ruling, not ticked. Anyone with Jenkins access should still fetch it; the same fetch also settles T-026's unattributed PR-3/1 anomaly."
  pr: https://github.com/erfeamor/cv-database/pull/3
  commit: b0f346c
  worktree: /home/erfeamor/work/cvdl-worktrees/T-152   # CLEAR THIS AT CLOSE-OUT -- T-028's generator exits 1 on a closed task that still declares a path
  blocked_criterion: "CI-side version proof (Flyway banner from Jenkins build #2). Console is authenticated; fetching it needs the SSM jenkins-admin-password, which this machine's permission policy declined. Pipeline DEFINITION verified locally instead; pipeline RUN is not. Needs a human with Jenkins access, or an explicit permission grant."

  updated: 2026-08-22
  developer: backend-developer
  reviewers: ["/code-review", "infrastructure-engineer (CI-config lens, read-only)", "/security-review"]
  security_review: true        # adapter §5 — Jenkinsfile is an unconditional /security-review path
  qa_plan: recorded            # authored by quality-assurance at stage 0, appended to this file
  worktree: pending            # cv-database supports worktrees (T-002's note); created at stage 1 after H1
  branch: chore/mysql-84-parity-ci
  pr:
  h1_rulings:
    - "AC3 CORRECTED: the CI half proves 8.4 via Flyway's connection banner, not docker exec (the container is --rm'd). Applied to the acceptance criteria."
    - "AC grep scope CORRECTED to repo-wide, matching the criterion rather than the narrower --include form the verification block carried."
    - "SEQUENCED FIRST. T-016 now carries depends_on: [T-152], so host port 3306 is exclusive by construction rather than by scheduling discipline."
    - "WIPE PATH (down -v) is the documented, supported route."
    - "Jenkinsfile Deploy-stage defects (dead `branch 'main'` gate, stale RDS comment) FILED as T-153, depends_on: [T-152]. Do not fix them here -- board rule 3."

---

## Goal

`cv-database` pins **`mysql:8.0`** in two places while production applies migrations to **`mysql:8.4`**. Bring both to 8.4.

| Pin | File | What it is |
|---|---|---|
| `image: mysql:8.0` | `docker-compose.yml:3` | the repo's own local stack |
| `mysql:8.0` | `Jenkinsfile:18` | **the throwaway MySQL every migration is validated against before merge** |

Production is not in doubt: `cv-infra/templates/domain-service-user-data.sh:164` runs `docker run … mysql:8.4`, and its header comment says so at line 2.

## Why the Jenkinsfile is the half that matters

`cv-database`'s pipeline exists to answer one question — *will these migrations apply?* It answers it against **8.0** and merges on that answer, while the migrations then run against **8.4**. That is not a parity nicety; it is the CI gate testing a different engine than the one it gates.

The gap has no backstop anywhere else in the workspace:

- `cv-domain-service`'s tests run against in-memory **H2** (`src/test/resources/application.yml:4`), so they exercise neither version.
- The dev-loop's stage-4 QA stack derives from the meta repo's `docker-compose.dev.yml` (`scripts/qa-env-override.py:555`), which also pins **8.0** — that is [T-016](T-016-dev-prod-mysql-parity.md)'s half.

So today **no automated check anywhere in the workspace runs against MySQL 8.4.** Every "verified against MySQL 8.4" claim on this board traces back to one of these two pins.

> **Provenance note, recorded rather than assumed.** Four stage-4 QA checkpoints state they ran against *"live MySQL 8.4"* — [T-102](T-102-education-resource.md):17 and :137, [T-103](T-103-skills-catalog-and-assignments.md):97 and :260. The generator has no MySQL-image handling and its base compose pins 8.0, so those stacks were most likely **8.0 labelled 8.4**. The stacks are torn down and this is **not reconstructible** — the same evidence-evaporates-at-teardown problem [T-028](T-028-qa-env-generator-worktree-build-context.md) recorded for bind mounts. Do not re-litigate it here; the durable fix is that after this task and T-016 the label becomes true by construction. Read the version off the running container, never off the compose file.

## Scope

1. `docker-compose.yml` → `mysql:8.4`.
2. `Jenkinsfile` → `mysql:8.4` for the throwaway migration container.
3. Document the volume-upgrade gotcha wherever this repo's stack commands live (`CLAUDE.md:8` currently says "MySQL 8 on :3306").

**Out of scope — these belong to other tasks, do not touch them:**

- The meta repo's `docker-compose.dev.yml` pin and the QA generator → **[T-016](T-016-dev-prod-mysql-parity.md)**. Runs in parallel with this task; different repo, different branch, no shared file.
- `cv-database`'s prose that says "MySQL 8" where it means the *target engine* (`CLAUDE.md:3`, `README.md:9`) → **[T-017](T-017-docs-drift-rds-to-selfhosted.md)** already claims that bullet. This task touches `CLAUDE.md:8` only, and only for the volume gotcha. **T-017 and this task both land in `cv-database` — sequence them, do not run them concurrently.**
- Any schema change. `sql/migrations/**` must be untouched; Flyway checksums reject edited history.

## Watch-outs — verify, do not inherit

- **The existing local volume was created under 8.0.** **Ratified at H1 2026-08-22: document the wipe path (`docker compose down -v`) as the supported route** — dev seeds regenerate via the Flyway callback so it costs nothing.
  - ~~QA reproduces the dirty-volume case (L9) to prove 8.4 refuses an 8.0 datadir.~~ **WRONG, AND CORRECTED BY THE IMPLEMENTER 2026-08-22 — the asymmetry runs the other way.** Reproduced on a throwaway volume: **8.0 → 8.4 succeeds silently**, performing an in-place upgrade (`Data dictionary upgrading from version '80023' to '80300'`, `Server upgrade from '80046' to '80411' completed`), healthy, exit 0, zero restarts. The hard failure is the **downgrade**: after 8.4 has touched the volume, checking out any branch still pinned at 8.0 aborts with `[ERROR] [MY-014061] [InnoDB] Invalid MySQL server downgrade: Cannot downgrade from 80411 to 80046`, the container exits 1, and because it therefore never reports `healthy`, **`reset.sh:9`'s `until` poll loops forever instead of erroring**. That last clause is the operationally expensive part and nothing on this board predicted it.
  - **This is the fifth acceptance-criterion/spec error found by the person working against it** (T-103, T-104, T-028, this task's AC3, now this watch-out). The implementer caught it because their first draft of the doc repeated the claim and they checked it. The committed `CLAUDE.md` documents **both** directions with the real log lines and keeps the wipe as the supported route.
- **Flyway 10 bundles the MariaDB driver**, so every MySQL 8 JDBC URL needs `?allowPublicKeyRetrieval=true` or migrate **hangs retrying** rather than failing. Already present in `flyway.conf` and `Jenkinsfile:22` — confirm it survives the edit, because the failure mode is a silent hang, not a red build.
- **8.4 changes authentication defaults** (`mysql_native_password` is no longer enabled by default). The stack uses the `caching_sha2_password` default and should be unaffected — *check this by connecting, not by reasoning about it*. If Flyway cannot authenticate on 8.4, that is the first place to look.
- **This runs on the on-demand CI host.** The first build after an idle period fails spuriously — see **[T-026](T-026-first-build-after-cold-start-fails.md)**. A red first build here is likely T-026, not this change; confirm by re-running on the warm box before debugging the bump. Note T-026's caution: **`gh pr checks` reports `pass` while a failed build sits in the history**, so read the statuses API, not `pr checks`.

## Acceptance criteria

- [ ] `docker-compose.yml` and `Jenkinsfile` both run `mysql:8.4`; no `mysql:8.0` remains in the repo (`grep -rn "mysql:8" .`).
- [ ] Local stack comes up **from an empty volume**, `./scripts/migrate.sh` applies every migration clean, and `./scripts/reset.sh` lands identically.
- [ ] **Local stack:** the running container's own report is 8.4 — `docker exec <c> mysql --version` and `SELECT VERSION();` — captured verbatim in the PR. **Reading the tag out of the compose file does not satisfy this criterion**, which is the entire lesson of the provenance note above.
- [ ] **CI:** the Flyway connection banner in the build log reads `Database: jdbc:mysql://cv-mysql-ci-<N>:3306/cv?allowPublicKeyRetrieval=true (MySQL 8.4)`, pasted into the PR alongside the `Successfully applied 1 migration to schema \`cv\`` line.
  - **Corrected 2026-08-22:** the expected string originally omitted `?allowPublicKeyRetrieval=true`. Flyway echoes the **full** URL, so a literal grep for the shorter form would miss and read as "banner absent". Confirmed against a real run (below).
  - ~~`docker exec <c> mysql --version` for the CI container~~ — **struck at H1, 2026-08-22. It is not satisfiable and never was.** `Jenkinsfile:12` starts that MySQL with `--rm` and `post { always }` force-removes it, so there is no moment at which anything can exec into it. QA caught this authoring the test plan; the driver confirmed it in the file. The Flyway banner is the correct substitute because it is the *driver reporting what it detected from the live server*, not a tag being echoed back. **This is the fourth acceptance criterion on this board found wrong by the person working against it** (after T-103's `@Transactional` boundary, T-104's inherited "flag, don't block", T-028's AC1) — and the first whose author was the same session that filed the task, hours earlier.
- [ ] The Jenkins pipeline goes green on 8.4, with the Flyway stage's log showing every migration applied — not merely an exit 0.
- [ ] `git diff master...HEAD -- sql/` is empty.
- [ ] The volume-upgrade gotcha is documented where the stack commands live.

## Verification (developer before PR; QA repeats at stage 4)

```bash
docker compose down -v && docker compose up -d && sleep 10
docker exec cv-database mysql --version                             # expect 8.4.x   (corrected 2026-08-22: container_name is FIXED to `cv-database`, so the compose-generated `cv-database-mysql-1` this line used to name does not exist)
docker exec cv-database mysql -uroot -proot -e 'SELECT VERSION();'
./scripts/migrate.sh                                                 # every migration applies
./scripts/reset.sh                                                   # same result from a wiped volume
grep -rn "mysql:8" .                                                  # REPO-WIDE (corrected at H1): the --include form this line used to carry contradicted the acceptance criterion above and would miss a stray pin in a README, a shell script or a Dockerfile
git diff master...HEAD -- sql/                                       # empty
```

**What failure looks like:** not a red build. If `allowPublicKeyRetrieval` is lost, migrate **hangs** with an RSA-public-key warning and no error; if auth defaults bite, Flyway fails at connect rather than at a migration. Neither reads as "the version bump was wrong" unless you are looking for it.

## Definition of done

PR open against `master` from `chore/mysql-84-parity-ci`, version proven from the running container (not the tag), Jenkins green on 8.4, task updated to `in_review` with the PR URL.

## dev-loop notes

- **Developer:** `backend-developer` (adapter §2 — `cv-database` is its layer). **Reviewers:** `/code-review` + `infrastructure-engineer` (adapter §2: reviews all CI config).
- `security_review: true` is **not** a stage-0 guess — adapter §5 lists `Jenkinsfile` as an unconditional `/security-review` path. A1 would force it regardless.
- `risk: normal`, and it does **not** take the trivial fast-path: adapter §5's fast-path covers "isolated non-security config", and a CI gate is neither isolated nor non-security.
- Needs the stack genuinely run — the point is that 8.4 starts clean and Flyway reaches it, which no static read can establish.
- Parallel-safe with [T-016](T-016-dev-prod-mysql-parity.md): different repos, no shared file. Use a QA env slot per adapter §6 so the two stacks do not contend for host ports.

## Provenance

Filed 2026-08-22 from a board review. [T-016](T-016-dev-prod-mysql-parity.md) was written on 2026-08-13 as `repo: cv-project (meta)` and names only the meta repo's compose pin; the review found **three** `mysql:8.0` pins, two of them here. Filed as a separate task rather than widening T-016, per board rule 3 (acceptance criteria define scope) and because the two halves carry different `security_review` values — `Jenkinsfile` forces it, a local compose bump does not. The `T-15x` band is this repo's, so the work is discoverable by band instead of buried in a `T-0xx` meta task.

---

## QA test plan (authored at stage 0 by `quality-assurance`, 2026-08-22 — QA executes it verbatim at stage 4)

### 0 · Stage-4 environment — the slot decision, stated up front

**Run T-152's stack unshifted on `cv-database`'s natural host port 3306, and treat that port as time-exclusive. Do NOT run it through `scripts/qa-env-override.py`'s offset math.** The reason is load-bearing, and the driver **verified it independently** before accepting it:

- `flyway.conf:6` hardcodes `flyway.url=jdbc:mysql://localhost:3306/cv?...` and `scripts/migrate.sh` runs Flyway with `--network host`. Neither takes a port argument.
- `docker-compose.yml:5` sets `container_name: cv-database` — fixed, not `${COMPOSE_PROJECT_NAME}-mysql-1`. `reset.sh:9` polls that literal name. So `COMPOSE_PROJECT_NAME` does **not** namespace this stack the way it does the meta compose.

A `--slot N` override would move the *published* port to e.g. 3326 while `migrate.sh` still dialled `localhost:3306` — connection-refused at best, and at worst **silently validating against whatever else holds 3306**. Faking parallel-safety here is worse than not having it. The adapter §6 generator was built for `docker-compose.dev.yml` and does not extend to this repo's compose + scripts; QA is read-only and cannot patch `migrate.sh` to fix that.

> **The worst case is not a port error — it is a false pass.** Both this stack's database and the meta stack's are named `cv` with user `cv`/`cv`. If [T-016](T-016-dev-prod-mysql-parity.md)'s stack holds 3306 when `migrate.sh` runs, Flyway connects, migrates **the wrong server**, and reports success. Neither task would notice. Scheduling constraint, not a preference — see the H1 amendment.

CI verification (C-block) has no such constraint: Jenkins gives every build its own `cv-mysql-ci-$BUILD_NUMBER` container and network, so it is self-isolating regardless of wave shape.

### 1 · L — local stack, from an EMPTY volume

Run from the T-152 **worktree** on `chore/mysql-84-parity-ci` — never the meta repo's bundled copy, or the check proves `master`, not the branch ([T-028](T-028-qa-env-generator-worktree-build-context.md)).

| # | Check | How | Expected |
|---|---|---|---|
| L1 | Both pins bumped, none left | `grep -rn "mysql:8" .` — **repo-wide, no `--include` filter** | Every hit `mysql:8.4`; zero `mysql:8.0` anywhere |
| L2 | Empty-volume bring-up | `docker compose down -v; docker compose up -d`; poll `docker inspect -f '{{.State.Health.Status}}' cv-database` | `healthy` inside the 10×5s window, no restart loop |
| L3 | `migrate.sh` clean apply | `./scripts/migrate.sh` on the fresh volume | Exit 0; `Successfully applied 1 migration(s)` (one migration exists today) and the dev-seed callback running |
| L4 | `reset.sh` lands identically | `./scripts/reset.sh`; compare table set and `flyway_schema_history` before/after | Same tables, same V1 history row, same seed counts |
| L5 | Version provenance | `docker exec cv-database mysql --version` **and** `... -e 'SELECT VERSION();'` | Both `8.4.x`, and they agree |
| L6 | Schema untouched | `git diff master...HEAD -- sql/` after rebasing onto current `master` | Empty |
| L7 | Doc gotcha present | `grep -n "8.0\|8.4\|volume" CLAUDE.md` | Documents that the pre-existing volume was created under 8.0 and needs `down -v`, near the stack commands |
| L8 | `allowPublicKeyRetrieval` survived | `grep -n allowPublicKeyRetrieval flyway.conf Jenkinsfile` | Both still carry it — a one-line tag bump makes it easy to disturb the URL line in the same edit |
| L9 | **Dirty-volume scenario — CORRECTED 2026-08-22, the expectation was inverted** | (a) 8.0 volume → start 8.4 against it; (b) then re-pin to 8.0 against that same, now-8.4 volume | (a) **succeeds** — silent in-place upgrade, healthy, `Server upgrade from '80046' to '80411' completed`. (b) **fails hard** — `MY-014061 Invalid MySQL server downgrade`, container exits 1, and `reset.sh`'s health poll **hangs forever** rather than erroring. ~~8.4 refuses the 8.0 datadir~~ was wrong; verify both directions and check the hang specifically |

### 2 · Version provenance — falsifiability

- Required evidence is **L5's verbatim output** pasted into the PR — not a paraphrase, not "confirmed 8.4".
- Run L5 on the container QA brought up *in this session*. A log from an earlier torn-down run is not acceptable: the premise of this task is that four such claims on this board are unverifiable precisely because the stack is gone.
- `mysql --version` reports the **client binary**; `SELECT VERSION()` the **server**. On the official image they agree — if they don't, that is itself a finding, not something to average away.

### 3 · C — CI: proving the migrations ran on 8.4, not merely that the build was green

The throwaway container is `--rm`'d and `docker rm -f`'d in `post { always }`, so there is **no `docker exec` opportunity after the fact**. Evidence must come from what Flyway logs while connected.

| # | Check | How | Expected |
|---|---|---|---|
| C1 | Right commit, right build | `gh api repos/erfeamor/cv-database/commits/<sha>/statuses` — **not** `gh pr checks` (§4) | A `success` entry for the Jenkins context on the PR's actual HEAD sha |
| C2 | Full console log captured | Jenkins console log for that build, saved as PR evidence | Covers `Validate migrations` end to end |
| C3 | **Running-server version evidence** | grep the log for Flyway's connection banner: `Database: jdbc:mysql://cv-mysql-ci-<N>:3306/cv (MySQL 8.4)` | Reads `8.4`, not `8.0` — the driver reporting what it detected from the live server; the CI-side equivalent of L5 |
| C4 | Migrations actually applied | grep for `Migrating schema \`cv\` to version "1 - init schema"` and `Successfully applied 1 migration(s)` | Present — not just `BUILD SUCCESS` at the tail |
| C5 | The image that ran is 8.4 | grep for the `docker run … mysql:8.4` line, and any `Pulling from library/mysql … 8.4` | Confirms the **branch's** Jenkinsfile ran, not a stale checkout |
| C6 | CI URL keeps `allowPublicKeyRetrieval` | grep the `FLYWAY_URL=` line | Still carries `?allowPublicKeyRetrieval=true` |

**Required PR artifact: the C3 and C4 excerpts pasted, not summarized.** "Jenkins went green" does not satisfy this task's own framing — that is the gap it exists to close.

### 4 · [T-026](T-026-first-build-after-cold-start-fails.md) interference — expect it, do not be fooled by it

1. **Never trust `gh pr checks`** here: it shows only the latest status per context and reads `pass` while a failed build sits earlier in the history. Use `gh api repos/erfeamor/cv-database/commits/<sha>/statuses` and read every transition.
2. **T-026's signature is a stage that produced no output at all** (`No build record … could be located`, empty stage). A genuine 8.4 failure has real output — the `docker network create`/`docker run` lines, then a pull error, a connect error, or Flyway's migration-failure text.
3. **If build #1 is empty-output-red:** re-run on the warm box before concluding anything about the bump.
4. **If it persists on a warm box, or shows real stage output**, it is not T-026 — debug it as genuine, most likely one of §6's two shapes.
5. Record which occurred in the PR. A red first build with no explanation has already been mis-filed once on this board (it briefly looked like T-106 had broken CI).

### 5 · Coverage risks — including where this task's own AC is wrong

- **The AC's CI provenance requirement is not satisfiable as written.** It says *"the running container's own report — `docker exec <c> mysql --version`"*, but the Jenkins MySQL container is `--rm`'d and force-removed in `post { always }`; there is never a moment to exec into it. This plan substitutes Flyway's own `Database: … (MySQL 8.4)` banner (C3), which is the driver reporting the live server rather than a tag being echoed. **Flagged as borderline-unfalsifiable as written**: an implementer reading it literally could ship the CI half with nothing stronger than a green tick — reproducing exactly the class of unverifiable claim this task was filed to stop. Fix the AC; do not let a reviewer accept "Jenkins is green".
- **A fresh isolated volume never exercises the dirty-8.0-volume path** the L7 doc entry warns about — L2's `down -v` guarantees a clean start, so "clean bring-up from an empty volume" is trivially true whether or not the warning is even accurate. L9 exists to force the scenario rather than let the plan pass around it.
- **The task's AC and its own Verification block disagree on grep scope**: the AC says `grep -rn "mysql:8" .` (repo-wide), the verification block narrows to `--include=Jenkinsfile --include=*.yml`, which would miss a stray pin in a README, a shell script, or a Dockerfile. Use the wide form (L1).
- **CI proves exactly one migration (V1) today.** A limit of the repo's state, not the task — but it means 8.4 is validated against the simplest possible DDL surface. A future migration using something 8.0/8.4-divergent gets its first real test the day it is written. Put a line in the PR so "CI now validates against 8.4" is not over-read.
- **No `timeout {}` wrapper in the Jenkinsfile.** If the edit drops `allowPublicKeyRetrieval` (L8/C6 catch it), the failure is a silent hang — and with `FLYWAY_CONNECT_RETRIES=60` and no pipeline timeout, the build and the shared on-demand CI host hang rather than failing fast. Not this task's scope to add one; flagged as an amplifier if L8/C6 are skipped.
- **`container_name: cv-database` defeats `COMPOSE_PROJECT_NAME` isolation.** A stale container from any previous run produces `Conflict. The container name "/cv-database" is already in use` regardless of project name. Confirm `docker ps -a --filter name=cv-database` is empty before L2.

### 6 · Silent failure signatures — one non-error surface, two causes

| Symptom | Cause | Telling them apart |
|---|---|---|
| Flyway appears **stuck** — no error, no exit; RSA-public-key WARN repeating; Jenkins sits `IN_PROGRESS` well past its normal ~90s | `?allowPublicKeyRetrieval=true` lost from `flyway.conf` or `FLYWAY_URL` (L8/C6) | **Hangs, does not error.** No forward progress; WARN text naming public-key retrieval. Check the URL line first |
| Flyway **fails immediately** at connect with an explicit auth/access error, no retry loop | MySQL 8.4's `mysql_native_password`-disabled-by-default change hitting a path that assumed it | **Fast and loud**, one clear error line, not a retry pattern. Confirm by connecting manually (`mysql -h127.0.0.1 -ucv -pcv cv`) — the watch-out says check by connecting, not by reasoning. Not expected: the stack never opts into `mysql_native_password` |

Neither reads, on its face, as "the version bump broke something" — they read as a stuck build or an unrelated auth bug.

---

## Stage 1 + A1 — implemented, and what the run established (2026-08-22)

**PR [cv-database#3](https://github.com/erfeamor/cv-database/pull/3)**, branch `chore/mysql-84-parity-ci`, commit `b0f346c`. Three files, +30/-2: `docker-compose.yml:3`, `Jenkinsfile:18`, `CLAUDE.md` (gotcha block). `sql/` untouched, `Deploy` stage untouched (T-153's).

**A1 — deterministic gate.** `cv-database`'s gate is `flyway migrate` against a throwaway MySQL 8.4 (adapter §3); there is no lint/typecheck/unit suite in this repo. Passed. **Risk re-check against the real diff:** 32 lines / 3 files, so no `trivial` revocation applies (the task was never flagged trivial); the diff touches `Jenkinsfile`, which **confirms** the stage-0 `security_review: true` rather than merely inheriting it.

### Local version proof (verbatim, container brought up this session on an empty volume)

```
$ docker exec cv-database mysql --version
mysql  Ver 8.4.11 for Linux on x86_64 (MySQL Community Server - GPL)
$ docker exec cv-database mysql -uroot -proot -e 'SELECT VERSION();'
VERSION()
8.4.11
```

Auth checked **by connecting, not by reasoning**, as the watch-out demanded: `cv`, `root@%` and `root@localhost` all report `caching_sha2_password`, so 8.4's `mysql_native_password` change does not bite. Image pulled explicitly by digest to rule out a stale cache serving 8.0 layers under the new tag.

`migrate.sh` on the fresh volume and `reset.sh` after it both land `Successfully applied 1 migration to schema \`cv\`, now at version v1` plus `Executing SQL callback: afterMigrate - seed dev`; the before/after capture (tables, `flyway_schema_history` incl. checksum `-1643462046`, seed counts person 1 / skill 5 / person_skill 5) diffs empty. `grep -rn "mysql:8" .` returns only 8.4. `allowPublicKeyRetrieval` intact at `flyway.conf:6` and `Jenkinsfile:22`.

### The CI half — what is proven, and what is NOT

**Proven by the driver, 2026-08-22:** the branch's Jenkinsfile stage was re-run locally with its exact commands (own docker network, `mysql:8.4`, the same networked `FLYWAY_URL`, `FLYWAY_LOCATIONS`, `FLYWAY_CONNECT_RETRIES=60`):

```
Database: jdbc:mysql://cv-mysql-ci-<N>:3306/cv?allowPublicKeyRetrieval=true (MySQL 8.4)
Migrating schema `cv` to version "1 - init schema"
Successfully applied 1 migration to schema `cv`, now at version v1 (execution time 00:00.193s)
  [server reports] VERSION() = 8.4.11
```

**NOT proven: that Jenkins build #2 executed those commands.** The console is authenticated (`consoleText` → 403) and fetching it needs the SSM admin credential, which this machine's permission policy declined — deliberately not worked around. So the pipeline *definition* is verified on 8.4; the *pipeline run* is evidenced only by a green status. **Do not conflate the two** — a local reproduction and a CI execution are different claims, and collapsing them is precisely the move this task exists to stop. The AC stays **unticked** until someone with Jenkins access pastes build #2's banner and applied-migrations lines.

### Findings that outlive this PR

1. **Flyway 10 does not officially support MySQL 8.4.** Every run now warns: `Flyway upgrade recommended: MySQL 8.4 is newer than this version of Flyway and support has not been tested. The latest supported version of MySQL is 8.1.` Warning only; migrations apply and the build stays green. **Crucially this is not a regression introduced here:** `cv-infra/templates/domain-service-user-data.sh:181` already runs `flyway/flyway:10` against the production `mysql:8.4`, on every instance replacement. So the unsupported pairing has been in **production** all along and this PR is the first thing to make it *visible*. That is an argument for the change, not against it — CI now reproduces production exactly, warning included. **A Flyway major bump is a genuine follow-up and belongs in its own task** (board rule 3); do not fold it in here.
2. **[T-026](T-026-first-build-after-cold-start-fails.md) recurred with a NEW status signature — fifth occurrence.** Previous four were a plain red first build. Here `PR-3/1` posted **`success` at 07:48:06 and then `error` at 07:48:07 — one second apart, on the same build** — before `PR-3/2` went green at 07:48:31 on the warm box. Nobody retriggered; push-then-PR fired two deliveries as T-026 already documents. The success-then-error inversion is new and is recorded there.
3. **The dirty-volume asymmetry** (see the corrected watch-out above): the upgrade is silent, the downgrade is fatal, and the downgrade's real cost is that `reset.sh`'s health poll hangs rather than failing.

### Stage 2 — specialist + security review (infrastructure-engineer, read-only, 2026-08-22)

**No blocking findings. No non-blocking findings against the PR's own content.** Both lenses run: CI-config specialist (adapter §2) and `/security-review` (adapter §5, unconditional on a `Jenkinsfile` diff — run, not waived for being a one-line change).

**On the Flyway-10-vs-8.4 question, the reviewer inverted the framing and the argument is worth keeping.** Blocking this PR over the support warning would privilege the *more* dangerous status quo: before it, CI validated against 8.0 while production applied migrations on 8.4, so a green gate said nothing about the engine that actually receives them. The pairing was already load-bearing in production (`user-data.sh:181`) and untested everywhere. This PR is the **fix** for that gap, not its source.

Security surface, itemised — every item pre-existing and unaffected by the tag change:

- No `--privileged`, no `--cap-add`, no `--network host`; the pipeline builds its own per-build bridge network `cv-db-ci-$BUILD_NUMBER`.
- Hardcoded `MYSQL_ROOT_PASSWORD=root` / `cv`/`cv` are **acceptable** here: the container publishes no host port, is uniquely named per `$BUILD_NUMBER`, is `--rm` plus force-removed in `post { always }`, and backs a database that never outlives the stage. Not a secrets finding.
- `-v "$WORKSPACE/sql:/flyway/sql"` mounts the repo's own migrations; not a new surface.
- **NOTE:** `post { always }` swallows cleanup failures (`|| true`). On a shared, cost-metered on-demand host that can leak containers/networks over time. Pre-existing; not for this PR.
- **NOTE:** images are pulled by mutable tag, before and after — applies equally to `flyway/flyway:10`.

`CLAUDE.md` block confirmed accurate against the empirical log lines and correctly placed (immediately after the commands block, ahead of the `CI: Jenkinsfile` line). `grep -rn "mysql:8" .` repo-wide returns only the three intended 8.4 hits. Nothing the diff should have touched was missed.

**Two follow-ups the reviewer asked to be filed, neither blocking and neither depending on this task:**

1. **Bump Flyway** to a version that claims MySQL 8.4 support. Orthogonal — T-152 is the fix for the parity gap, not its cause.
2. **Add `timeout {}` to the Jenkinsfile.** Flagged *moderately urgent* for a cost reason rather than a correctness one: if `allowPublicKeyRetrieval` were ever lost, Flyway hangs rather than failing (`FLYWAY_CONNECT_RETRIES=60`), and a hung build ties up the **only** CI host — which the cost model ([T-020](T-020-cost-model-correction.md)) prices at ~$17.24/month if it is left running. Latent, not live: `allowPublicKeyRetrieval` is verified intact at `flyway.conf:6` and `Jenkinsfile:22` after this edit.

### Stage 2, second lens — `/code-review` did NOT run, and that is recorded rather than papered over

The adapter's reviewer set for `normal` risk is `/code-review` **plus** one specialist lens. The specialist lens ran (above). `/code-review` was invoked **twice** against this worktree and both times returned an empty result after ~5 seconds and a single tool call — it does not appear to review a target outside the session's own repository. That is not a clean review; it is a pass that did not happen, and reporting "no findings" from it would be exactly the green-signal-that-measured-nothing failure this board has catalogued three times ([T-107](T-107-post-id-cross-person-write.md)'s mock-measuring test, [T-028](T-028-qa-env-generator-worktree-build-context.md)'s master-building QA stack, [T-026](T-026-first-build-after-cold-start-fails.md)'s `gh pr checks`).

**The driver did the general correctness pass inline instead, and it is a pass over facts rather than an opinion.** Every factual claim the diff makes was checked against the repo:

| Claim in the diff | Checked against | Result |
|---|---|---|
| the leftover volume is `cv-mysql-data` | `docker-compose.yml:13` (mount) and `:21` (declaration) | correct |
| "`reset.sh` already does all three steps" | `scripts/reset.sh:6,7,9,12` — `down -v`, `up -d`, health poll, `migrate.sh` | correct |
| the doc sits where the stack commands live | `CLAUDE.md` — immediately after the commands fence, before the `CI:` line | correct |
| no 8.0-era assumption survives | `grep -rniE "mysql 8\.0\|native_password"` repo-wide | only the deliberately historical mention inside the new block |

`CLAUDE.md:8` still reads *"MySQL 8 on :3306"* — accurate (8.4 *is* MySQL 8) and it is [T-017](T-017-docs-drift-rds-to-selfhosted.md)'s prose to sharpen, correctly left alone here.

**Open action for the workspace, not for this PR:** the adapter mandates a reviewer this pipeline could not actually run on an out-of-repo worktree. Every future `T-1xx`/`T-15x`/`T-2xx` task has the same shape, so this will recur on the next task and the one after. Worth a task of its own.

### Stage 4 — exploratory QA (read-only, 2026-08-22)

**Local half: CLEAN. L1–L9 all pass**, run against the branch in the worktree (worktree root confirmed to be the checkout, port 3306 confirmed free before and after). Highlights that are not just green ticks:

- **L9 was re-verified independently rather than trusted** from either the task file's prose or the developer's run — and it confirms the corrected, inverted expectation. 8.0→8.4: silent in-place upgrade to `healthy` (`Data dictionary upgrading from version '80023' to '80300'`, `Server upgrade from '80046' to '80411' completed`). 8.4→8.0: `ExitCode: 1` with `[MY-014061] Invalid MySQL server downgrade: Cannot downgrade from 80411 to 80046`.
- **The hang was proven, not inferred.** QA ran `reset.sh`'s literal `until [ health = healthy ]; sleep 2` loop against the exited container under a bounded 30s `timeout`: it never broke out (exit 124). So the documented claim that the poll *loops forever instead of erroring* is measured behaviour.
- L5 `8.4.11` from both client and server, read off the running container. L4's before/after diff empty (7 tables, history checksum `-1643462046`, seed counts). L6 `sql/` untouched. L8 `allowPublicKeyRetrieval` intact.
- Auth-plugin watch-out discharged **by connecting**, as instructed — clean connections as both `root` and `cv` against a fresh 8.4 instance.

**CI half: BLOCKED on verification access, not on a code defect.** QA hit the same 403 and declined, as instructed, to sign off C1–C6 on the strength of the driver's local reproduction of the pipeline stage. Correctly so: that proves the pipeline *definition*, not that Jenkins executed it. The acceptance criterion stays **unticked**.

**To close it, one fetch covers two open items** — the console for `http://13.39.59.12/jenkins/job/cv-database/job/PR-3/`, builds **#2** (this task's criterion: the `docker run … mysql:8.4` line, Flyway's banner, `Successfully applied 1 migration`, and `FLYWAY_URL` still carrying `?allowPublicKeyRetrieval=true`) and **#1** ([T-026](T-026-first-build-after-cold-start-fails.md)'s unattributed anomaly).

**QA also overturned a driver claim, and it stands corrected.** The driver had written the PR-3/1 `success`-then-`error` sequence into T-026 as its "fifth occurrence". QA pointed out T-026's filed signature is `No build record … could be located` **with an empty stage**, and that evidence was never obtained here — so the attribution was unearned. T-026 is retitled to an *unattributed anomaly* pending that console log. **A reviewer's job includes checking the driver**, and this is the second time in this task that the specification-side, not the implementation-side, was the weak link.

**Stack torn down**, no `cv-database` container or volume remains, 3306 free — [T-016](T-016-dev-prod-mysql-parity.md) can unpark.
