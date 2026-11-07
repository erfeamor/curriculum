---
id: T-065
title: "App host on Spot (persistent, stop on interruption) with alerts"
repo: cv-infra
status: todo
owner: 
branch: feat/app-host-spot
pr:
depends_on: [T-061]
risk: high
security_review: true
---

## Why

Part of **M3 — cost first, on erfeamor.com** (planned 2026-11-07; the plan is summarized in [TASKS.md](TASKS.md) § M3).

Spot `t4g.micro` in eu-west-3a cost $0.0015/h against $0.0094/h on demand (measured 2026-11-06), about $5.8/month saved. The human accepted the interruption risk on 2026-11-07.

## Scope

- `instance_market_options { market_type = "spot"; spot_options { spot_instance_type = "persistent", instance_interruption_behavior = "stop" } }`. It must be persistent, because `stop_instance_before_detaching` (`storage.tf:229`) stops the instance. Check `valid_until`, so the request never expires.
- **No ghost instance:** a destroy-time `local-exec` runs `aws ec2 cancel-spot-instance-requests` on `self.spot_instance_request_id`. Without it, every later `-replace` or user_data change re-launches the old host. That copy bills, and the `count > 1` guard (`cv-domain-service deploy.yml:250-253`) would then break deploys. **Prove it on a throwaway instance first.**
- **Alerts:** an EventBridge rule on Spot interruption warnings and stop/start state changes publishes to the budget SNS topic. Its policy needs an `events.amazonaws.com` statement scoped by `aws:SourceArn` (`budgets.tf:84-115`).
- A `var.app_host_spot` toggle falls back to on-demand. `plan.tftest.hcl` asserts the market options. Run `plan` twice after apply, to catch a permanent diff.

## Acceptance criteria

- [ ] `InstanceLifecycle=spot`; a deliberate `-replace` leaves no extra instance and a cancelled request.
- [ ] A stop and start comes back healthy, and the alert email arrives.
