# Spike T-506: serverless, priced against the trimmed host

Decided 2026-11-21. Prices are from the AWS Price List API for **eu-west-3 (Paris)**, pulled 2026-11-21. Rates marked *derived* or *assumed* are not from that pull.

## Recommendation

1. **Do not migrate the CV to serverless.** It would save at most about $7.60/month, and only after the credits expire on 2027-07-12. Before then the saving is zero, because ~$39 of credits expire unused anyway. The cost is a rewrite of the data layer. No follow-up task.
2. **Build budgetPlanner serverless, outside the app host.** Estimated +$1.30/month. The host has no room for a second app, and growing it to `t4g.small` adds $6.86/month on its own.
3. **The CV and budgetPlanner stay independent.** The Lambda and DynamoDB pieces for budgetPlanner are cheap to prove, and if serverless later proves good there, the CV question can be reopened with real experience.
4. **Reopen the CV question in May 2027** (credits end 2027-07-12), with budgetPlanner's measured usage and its Aurora DSQL experience as the input. If DSQL went smoothly the CV move gets cheaper; if not, keep the host.

## Facts that drive the numbers

| Fact | Value | Source |
|---|---|---|
| Measured run rate | $0.239 to $0.263/day over the last 5 full days (use **$0.25**, ~$7.60/month) | Cost Explorer, 2026-11-16..20 |
| Credits | $97.73 left, 233 days to 2027-07-12 | `aws freetier get-account-plan-state` |
| App host memory | 911 MB total, 629 used, **493 MB of swap in use**, domain service alone 405 MB | SSM `free -m`, `docker stats` |
| CV traffic | ~15,000 CloudFront requests in 14 days (~1,100/day), mostly static from S3 | CloudWatch |
| CV schema | 70 lines of SQL, 5 foreign keys, 1 `ENUM`, `AUTO_INCREMENT` ids | `cv-database/sql/migrations` |

## Prices (Paris)

| Item | Price |
|---|---|
| Lambda requests | $0.20 per million |
| Lambda compute | x86 $0.0000166667 per GB-s; arm64 about $0.0000133334 (*derived*, 20% less) |
| Lambda free tier | 1M requests and 400,000 GB-s a month, permanent (*not in the price list; from AWS docs, confirm*) |
| SnapStart (Java) | no extra charge, per the AWS docs |
| Aurora DSQL | $0.0000095 per DPU, $0.45 per GB-month; first 100,000 DPU and 1 GB free each month |
| DynamoDB on demand | $0.7423 per million writes, $0.1487 per million reads, first 25 GB free |
| Textract AnalyzeExpense | $0.01 per page |
| Textract text detection | $0.0015 per page |
| EC2 `t4g.small` | $0.0188/h = $13.72/month (`t4g.micro` is $6.86) |

Aurora DSQL answers in eu-west-3 (`aws dsql list-clusters` works) and is priced there. AWS's older write-ups disagree on whether Paris is multi-Region capable. Only single-Region clusters matter here.

## Part 1: the CV

| Option | Monthly cost | Saving vs $7.60 | What it takes |
|---|---|---|---|
| Today (host + MySQL) | $7.60 | | nothing |
| BFF on Lambda only | still $7.60 | $0 | the host stays for the domain service and MySQL; the BFF is already 39 MB, nothing to free |
| BFF + domain service on Lambda + MySQL kept | still ~$7.60 | $0 | MySQL still needs a host or RDS (RDS is dearer) |
| **All on Lambda + DSQL** | ~$0.70 (Route 53 zone, S3, Cognito) | **~$6.90** | below |
| All on Lambda + DynamoDB | ~$0.70 | ~$6.90 | rewrite of the whole domain service |

Compute is free at this scale: 10,000 invocations a month at 1 GB for 1.5 s is 15,000 GB-s, against 400,000 free. DSQL is free at this size (a few hundred KB, a few thousand DPU). Only the full move saves anything, and the saving is the host plus its disks.

**The real price of the full move:**

- **JPA on DSQL.** DSQL speaks PostgreSQL, so the Hibernate dialect changes, `AUTO_INCREMENT` becomes identity or UUID keys, and `ENUM` becomes a text column with a check. DSQL has **no foreign keys**, and the five `ON DELETE CASCADE` constraints would have to move into the service code, with tests. The app, its 6 entities and the contract tests all change.
- **Flyway.** The two migrations are MySQL and must be rewritten. Flyway's DSQL support is unverified; DSQL authenticates with short-lived IAM tokens, not a password.
- **Cold starts on the public CV.** The JVM takes 30 to 40 s today. SnapStart typically brings restore to a few seconds, still slow for a first visitor. The CV avoids this only because the BFF is cached by CloudFront and the Next.js site by ISR.
- **Auth, metrics, dev stack.** The domain service validates Cognito JWTs itself and sits behind CloudFront with VPC origins today (T-068); Lambda needs Function URLs with OAC instead. Prometheus and Grafana scrape the host, so `cv-observability` would shrink to CloudWatch. `docker-compose.dev.yml` would need DSQL or a Postgres stand-in, so dev and prod would differ.
- **Size of the work:** about 8 to 12 tasks across five repos, several of them `high` risk with an apply.

**Verdict:** no-go. Payback is $6.90 a month for a multi-week rewrite, with no benefit before 2027-07-12.

Cheaper levers on the CV, **not priced here** (a separate task if wanted): a one-year Compute Savings Plan on the host, taken near the credit expiry.

## Part 2: re-estimating the account with budgetPlanner

From `/home/erfeamor/work/budgetPlanner/SPECIFICATION.md`: a PWA, Google Sheets as the system of record, CSV bank imports (PSD2 later), receipt and price-label OCR, a school-menu photo, and AI use only where no rule applies. Two users, small volume. The figures below are **assumptions**, to be replaced by measurement once the app exists.

| Component | Assumption | $/month |
|---|---|---|
| PWA hosting | S3 + the existing CloudFront (new path or subdomain; a subdomain means a certificate with one more name) | 0.00 |
| Auth | existing Cognito pool, a new app client, 2 users | 0.00 |
| Compute | arm64 Lambda, ~10,000 calls a month, within the free tier | 0.00 |
| App state (rules, price history index, tokens) | DynamoDB on demand, well inside 25 GB | 0.00 |
| Receipt OCR | 40 receipts × 1.5 pages × $0.01 | 0.60 |
| Price-label OCR | 120 photos × $0.0015 | 0.18 |
| AI classification and menu planning | a few calls a month (*assumed*) | 0.30 |
| Photo storage in S3 | ~400 MB a month, with a lifecycle rule (*assumed*) | 0.10 to 0.20 |
| **Total, serverless** | | **about $1.30** |

**Not in the estimate:** PSD2 aggregator fees (undecided), a customer-managed KMS key for bank credentials ($1/month, so v2 should use SSM SecureString instead), and the Google APIs (free at this volume).

### Effect on the account

| Scenario | $/day | $/month | Credits | After credits |
|---|---|---|---|---|
| CV only (today) | 0.250 | 7.60 | $58 spent by 2027-07-12, **$39 expire unused** | $7.60 |
| CV + budgetPlanner on Lambda | 0.293 | 8.90 | $68 spent, **$30 expire unused** | $8.90 |
| CV + budgetPlanner on the app host, upsized to `t4g.small` | 0.518 | 15.80 | **exhausted 2027-05-28**, 6 weeks early | $15.80 |

- **The Lambda path costs $1.30 a month** and keeps every dollar of credit working until July.
- **Putting it on the host doubles the bill** and runs the credits out in May.
- **Budget alarms.** `gross_usage` is $17: the Lambda path stays well under it. The upsized host (~$15.80) sits just under it, which is too tight to warn before the credits are gone.

### What I'd carry into budgetPlanner's own tasks

1. Serverless from day one; no new EC2.
2. Cost guard in the first infra task: a budget alarm at 2× the estimate, and a Textract page cap, since OCR is the only usage-driven line.
3. Use text detection ($0.0015) for price labels, not expense analysis ($0.01).
4. Keep Google as the system of record; the database stays a cache of rules.
