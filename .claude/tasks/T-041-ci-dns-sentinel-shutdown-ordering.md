---
id: T-041
title: "The CI host's shutdown DNS sentinel is a race: two stops in four left ci.erfeamor.com pointing at a released public IP"
repo: cv-infra
status: todo
owner:
branch: fix/ci-dns-sentinel-ordering
pr:
depends_on: [T-034]
risk: normal
security_review: true   # the sentinel exists to stop a released IP (possibly reassigned to another AWS customer) from answering for ci.erfeamor.com — adapter §5 network exposure
---

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
