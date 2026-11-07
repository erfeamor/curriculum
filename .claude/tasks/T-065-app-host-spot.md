---
id: T-065
title: "App host on Spot (persistent, stop on interruption) with alerts"
repo: cv-infra
status: done
owner: claude
branch: feat/app-host-spot
pr: "-"
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

## DECIDED 2026-11-07 — not doing Spot; the app host stays on-demand

The human accepted Spot earlier the same day, before a throwaway proof (a scratch Terraform config with its own state, `t4g.nano` Spot in the default VPC, destroyed afterwards; nothing left in AWS) produced evidence that changed the premise.

**What worked.** A destroy-time `aws ec2 cancel-spot-instance-requests` on `self.spot_instance_request_id` leaves no ghost instance: after a `-replace` (via `user_data_replace_on_change`) there was one running instance, the old one terminated, its request `cancelled`; a plain `terraform destroy` left nothing. `aws_instance` with `instance_market_options { market_type = "spot"; spot_options { spot_instance_type = "persistent", instance_interruption_behavior = "stop" } }` plans and applies cleanly on provider 5.100.

**What decided it.**
- A *stopped* persistent Spot instance **could not be restarted**: `InsufficientInstanceCapacity` ("no available Spot capacity") on every retry for 90+ seconds. The host stops on every interruption and on every planned volume operation (`stop_instance_before_detaching`, T-066), and comes back only when capacity returns.
- `get-spot-placement-scores` (single AZ, target 1): **eu-west-3a scored 1/10 for `t4g.micro`, `t4g.small` and `t4g.nano`**; 3b scored 3 (`t4g.micro`) and 3c 3 (`t4g.small`). The MySQL data volume pins the host to 3a. Spot price: 3a $0.0015/h, 3c $0.0016, 3b $0.0028.
- Also seen: a manual stop of a persistent request goes `marked-for-stop` → `disabled`, and `start-instances` fails with `IncorrectSpotRequestState` until it reaches `disabled` (seconds).
- The account has no `AWSServiceRoleForEC2Spot` role until the first Spot request creates it (the scratch run created it; it is free and harmless).

**Decision.** The human chose to skip Spot over the alternatives (Spot in 3a with an on-demand fallback; move the volume to 3b first): no interruption risk, ~$5.8/month less saving. M3's end state becomes **~$8.4/month if T-067 says go, ~$12.0 if not** (was ~$2.6 / ~$6.2), plus the domain renewal. The credits ($104.05 on 2026-11-02) still cover ~$12.5/month until they expire on 2027-07-12, so the run-out date does not move earlier than expiry.

**Knock-on.** T-066 and T-068 no longer wait on this task. T-067's throwaway instance should be on-demand `t4g.nano` (cents), not Spot. T-069's budget retune uses the new rates. To revisit later: re-run `get-spot-placement-scores`, or move the data volume to another zone first.
