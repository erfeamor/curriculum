---
id: T-041
title: "The CI host's shutdown DNS sentinel is a race: two stops in four left ci.erfeamor.com pointing at a released public IP"
repo: cv-infra
status: in_review
owner: tech-product-owner
branch: fix/ci-dns-sentinel-ordering
pr: https://github.com/erfeamor/cv-infra/pull/29
depends_on: [T-034]
risk: normal
security_review: true   # the sentinel exists to stop a released IP (possibly reassigned to another AWS customer) from answering for ci.erfeamor.com — adapter §5 network exposure
checkpoint:
  stage: qa   # review round 1 clean; PR open; NEXT: live apply from the branch (host must be up, CIKeepAlive), systemctl show check, then 5 stop/start cycles — deferred: human /usage 40–75% at H1
  repo: cv-infra
  branch: fix/ci-dns-sentinel-ordering
  worktree: none   # main cv-infra checkout
  commit: f51c201
  pr: https://github.com/erfeamor/cv-infra/pull/29
  developer: infrastructure-engineer
  reviewers: [code-review, security-review]
  risk: normal
  security_review: true
  review_round: 1
  open_findings: 0
  qa_bounces: 0
  fix_attempts: 0
  env_slot: n/a   # live on the CI host
  updated: 2026-10-01T01:05:00+02:00
  budget:
    turns: 0
    total_tokens: 0
    subagent_tokens: 107346
    spawns: 1   # infrastructure-engineer (fresh)
    status: ok   # human-reported /usage 40–75%
    checked: 2026-10-01T01:05:00+02:00
---

## H1 — decided by the human, 2026-09-30

**Root cause, proven from the host's persistent journal** (boot `166c501e…`, the 22:32 stop): systemd began the sentinel's `ExecStop` at 22:32:25.18; `systemd-networkd` stopped at **22:32:26.08** ("ens5: DHCP lease lost"); the `timeout 10` expired at 22:32:35.19 ("failed or timed out"). The successful 22:02 stop wrote the sentinel at 22:02:46, before networkd went down, so it's a race. `systemctl show` on the live unit: `After=basic.target system.slice systemd-journald.socket sysinit.target`, `Wants=` empty. Its sibling `ci-dns-updater.service` already has `Wants=`/`After=network-online.target`. A fifth stop (22:46:29) happened to succeed: **3 of 5** so far. The reaper's Lambda path is independent of this unit.

1. **Fix: order the unit.** `Wants=network-online.target` + `After=network-online.target` on `ci-dns-sentinel.service` (reverse order at shutdown keeps networkd and resolved up until `ExecStop` returns). Log the AWS CLI's own error to the journal instead of `>/dev/null 2>&1`, still exit 0. Raise the `timeout` from 10s to 20s. **No AWS-side EventBridge backstop** (considered and declined for now).
2. **Offline:** a `check-static.sh` assertion on the unit's ordering lines; red-first.
3. **Runbooks:** after a manual stop, read the record; UPSERT `192.0.2.1` by hand if it didn't flip.
4. **Live proof: 5 consecutive operator stop/start cycles** after the apply, each leaving the record on `192.0.2.1` within a minute, with the host's own UPSERT in CloudTrail (**us-east-1**) and "UPSERTed" in the journal.
5. **Budget:** the human reported `/usage` at 40–75%, so implement and review this window, and **checkpoint before the live apply**.

## Implement + review — 2026-10-01 (f51c201, cv-infra#29)

- Developer (fresh infrastructure-engineer, 1 spawn, ~107k tokens): exactly the H1 scope. Check 17 red-first (FAIL with the unit change stashed, OK restored).
- Driver-verified: diff read, full offline gate re-run green (terraform test 14/14, check-static 17/17, harnesses 12/21/10, Lambda 75).
- **Review round 1 (driver, code + security lenses): clean.** Ordering holds on stop (networkd and resolved are both ordered before `network-online.target`); no boot cycle (docker already starts after network-online; the updater uses the same pair live); 20s is well inside systemd's 90s stop timeout; the logged CLI error carries no credentials. Non-blocking, pre-existing: `scripts/tests/run-ci-dns-sentinel-tests.sh` isn't in cv-infra CLAUDE.md's offline-gate list.

**Next (resume here):** start the host with `CIKeepAlive`, back up state, plan from the branch (expect the provisioning script's S3 object, SSM hash and `null_resource.jenkins_provision` only), apply, `systemctl show ci-dns-sentinel -p After -p Wants`, then 5 stop/start cycles with record + CloudTrail (us-east-1) + journal checks. Then H2.

## Why

Found 2026-09-30 while closing [T-034](T-034-release-ci-host-idle-eip.md) phase 2. Four operator stops (`aws ec2 stop-instances`) of the CI host that night:

| Stop | Sentinel UPSERT from the host (CloudTrail, us-east-1) |
|---|---|
| ~21:43Z | 21:43:04Z → `192.0.2.1` ✔ |
| ~22:02Z | 22:02:46Z → `192.0.2.1` ✔ |
| ~22:24Z | **none** — the record kept `15.236.95.37` until the driver UPSERTed the sentinel by hand at 22:27:38Z |
| 22:32:49Z | **none** — the record kept `15.224.212.147`; sentinel set by hand right after |

`ci-dns-sentinel.service` (written by `templates/jenkins-provision.sh`) is a `oneshot` + `RemainAfterExit` unit whose `ExecStop` runs `scripts/ci-dns-sentinel.sh`. Its only ordering is `Before=docker.service`; it has **no `After=`/`Wants=network-online.target`**. systemd stops units in reverse start order, so nothing guarantees the network (or IMDS credentials) is still up when `ExecStop` runs. The script wraps the call in `timeout 10` and **exits 0 unconditionally**, so a lost race is silent.

**Why it matters:** once stopped, the host's public IP goes back to AWS's pool. If it's reassigned, `ci.erfeamor.com` answers from someone else's machine. That machine could receive GitHub's webhook deliveries (the payloads, not the secret) and could even obtain a Let's Encrypt certificate for the name via HTTP-01. The window lasts until the next boot's updater run. The doorbell itself is safe: since T-034 phase 2's third commit it checks the authoritative record against the instance's own IP before probing.

Not yet known: whether the reaper's graceful path (it sets the sentinel itself before stopping) has the same gap. It doesn't depend on the unit, so it probably doesn't.

## Scope

- Order the unit so its `ExecStop` runs while the network is still up: `After=network-online.target` + `Wants=network-online.target` (and consider `After=` on anything else the AWS CLI needs at shutdown). Re-check the `timeout 10` against a cold `aws` CLI start plus IMDS credential fetch.
- Log a failed UPSERT loudly to the journal (keep the exit 0, so shutdown isn't blocked).
- Offline: a `check-static.sh` assertion on the unit's ordering lines.
- Live: re-provision (the script travels through S3 + the SSM hash), then **several** operator stops in a row, each followed by a record read. A single success proves nothing, since tonight's failure rate was two in four.
- Update `docs/runbooks/drone.md` / `ci-host-replace.md`: after a manual stop, read the record, and UPSERT the sentinel by hand if it didn't flip.

## Acceptance criteria

- [ ] The unit's ordering guarantees the network during `ExecStop`, asserted offline.
- [ ] At least 5 consecutive operator stops each leave the record on `192.0.2.1` within a minute (CloudTrail shows the host's UPSERT each time).
- [ ] The runbooks carry the manual check and fallback.
