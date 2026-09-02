# STOP E brief — P1 banking-core cutover signoff (2026-09-02)

Evidence: `.migration/evidence_pack/INDEX.md`. Runbook: `docs/migration/ts-sas-legacy-analytics_P1_cutover_runbook.md`.

## Recommendation: DEFER

Recommend **"STOP E deferred — continue coexistence until REQ-05 SAS-produced recon is PASS and the GREEN clock reaches 5/5"**.

Why: the conversion is complete and every gate this engagement *can* run is green, but the one gate that says anything about production — a customer-executed, SAS-produced recon (REQ-05) — does not exist. Every PASS in the pack compares Databricks output to an independent Python re-reading of the SAS source; the reading can be wrong in the same way twice (DEC-017 was exactly that, caught by review not by recon). Approving now means accepting that the target reproduces *our reading of* the legacy, not the legacy. That is a legitimate choice, but only the requester can make it, and it must be made explicitly — say so plainly: **if the requester approves today, they are accepting the DEGRADED caveat as the basis for a regulatory reporting pipeline.**

## Blocking gaps (any one is enough to defer)

| # | Gap | Owner | Closes when |
|---|---|---|---|
| 1 | **Production-data recon NOT AVAILABLE** (REQ-05, fired 2026-09-01, no response). Blocking-for-cutover per tolerances R-0 / plan §1 D10-001. | Requester | `Data/expected/` delivered and recon re-run PASS (snapshot tier → SAS-produced) |
| 2 | **Alerting not wired**: no notification destination (`notification-destinations list` = `[]`, needs workspace-admin); neither job has `on_failure`. A failed run post-flip is silent. | Customer workspace-admin | destination created; bundle adds `on_failure`; `jobs get` shows it |
| 3 | **DEC-016 pending** (append vs overwrite for `acct_exceptions` / `txn_rejected`). Multi-day accumulation semantics unknown; single-date parity only. | Requester | decision recorded in `06_decisions.md` |
| 4 | **GREEN clock 1/5** (cycle 4, 2026-09-02T01:12Z). Exit criterion is 5 consecutive GREEN. | time (4 more daily cycles at 06:15 UTC, earliest 2026-09-06) or requester waiver | ledger shows 5/5 |
| 5 | **Governance parity GAP (G-3)**: `sas_legacy` has zero grants; no consumer or batch principal; jobs run as a workspace-admin owner. Legacy access model never exported. | Customer | read-only consumer group + job run-as principal granted |
| 6 | **Consumers unnamed** (REQ-02): `REPORTS.*` readers, xlsx recipients, e-mail destination; **Control-M export absent** (REQ-03), schedule timezone unknown. The runbook flip cannot be rehearsed beyond desk-check. | Requester | REQ-02/03 answered |
| 7 | **Capital constants 50M/65M/80M** reproduced as placeholders in regulatory output (U4). | Requester | confirmed as production values, or corrected + U4 re-recon |

Also open, not individually blocking: T-9 x2 DECLARED-UNEXERCISED; `ABORT_ON_ERR=N`/FAIL branch and repair-run unit-tested only; `%sendmail` deferred; migration chain never merged to `main` (G-1; PRs #24-#26 open); D5-004 automation id TBD (G-2).

## What is proven

- All 5 P1 units converted, merged into `migration/02-analysis-plan` (PRs #27-#39), legacy source untouched, serverless only, everything inside catalog `sas_legacy`.
- Independent recon GREEN for every unit and end-to-end: 14/14 tables row-count-equal to the reference (466/32; 18903/610/46/12; 236/195/12; 59/70/6/1; 4), 0 FAIL across 52+64+96+70+13 rule checks, scorer ML-1..ML-6 green, DEC-017 corrected and re-proven (T-3 `model_id` 0 mismatches).
- Idempotency under orchestration: two full 5-task job runs (`736214486752362`, `568864968862809`) reproduce every wave-1/2 verdict; `archive_batch_history` accumulates by design.
- Coexistence machinery works: scheduled 5-task recon, staged red proves the fail path and task independence, recovery confirmed, cycle 4 GREEN 5/5 on the corrected reference.
- Deployables verified read-only today: `sas_legacy_run_daily_banking` `216001923865775` **PAUSED**; `sas_legacy_recon` `1058116656072070` UNPAUSED 06:15 UTC.
- Rollback is instant by construction (legacy never modified; re-pause + Control-M repoint back).

## Decision sentences (reply with one, verbatim)

- Approve: **"STOP E approved — cutover authorized"** — this also means: "I accept the DEGRADED caveat (reference-derived, not SAS-produced) and the open gaps 2-7 as post-cutover items"; the runbook's flip steps then belong to the customer-held cutover principal, never Devin.
- Defer (recommended): **"STOP E deferred — continue coexistence until <condition>"** — suggested condition: *"REQ-05 SAS-produced recon PASS and GREEN clock 5/5"*; minimum acceptable condition if REQ-05 cannot be produced: *"GREEN clock 5/5, alerting wired, DEC-016 decided, consumer grants in place"*.

Either way, DEC-016 needs an answer in the same reply.
