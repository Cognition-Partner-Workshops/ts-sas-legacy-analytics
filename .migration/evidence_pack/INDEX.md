# STOP E evidence pack — P1 banking-core (cutover-signoff gate)

Prepared 2026-09-02 by the `!dbx_cutover_signoff` preparation session (branch `migration/08-signoff-prep`). This session migrated nothing, changed no code under `databricks/src` or `databricks/recon`, ran no job, and touched no Databricks state; every Databricks fact below comes from read-only `databricks jobs get`, `notification-destinations list`, and `SHOW GRANTS` / `DESCRIBE CATALOG` on warehouse `565cd2fd713738c4` (evidence scrubbed under `databricks/evidence/signoff/`).

Sources: `.migration/05_progress.md`, `04_dependency_register.md`, `06_decisions.md`, `09_parallel_run_ledger.md`, `evidence_pack/wave{0,1,2,3}_close_brief.md`, `docs/migration/ts-sas-legacy-analytics_P1_{wave2,wave3,dec017}_recon.md`, `docs/migration/ts-sas-legacy-analytics_P1_banking_core_plan.md` §5-6, `docs/migration/ts-sas-legacy-analytics_target_state.md`, `databricks/resources/jobs.yml`.

Mode caveat that applies to every recon fact in this pack: **DEGRADED — reference-derived, not SAS-produced** (DEC-004 option b). Every verdict is a statement about the 31JAN2024 seed snapshot, not about production.

Companion documents: `stop_e_brief.md` (one-page decision) and `docs/migration/ts-sas-legacy-analytics_P1_cutover_runbook.md` (rehearsal + rollback).

---

## (i) All waves merged and green

Integration branch: `migration/02-analysis-plan` (all P1 wave PRs merged there). **Nothing from the migration chain has merged into `main`**: PRs #24 (`migration/00-setup` → `main`, draft), #25 (`01-inventory` → `00-setup`), #26 (`02-analysis-plan` → `01-inventory`) are still OPEN — see new GAP G-1 in §(iii).

| Wave | Content | PRs (state) | Recon report | Verdict | PASS / FAIL / N-A / DECL-UNEX | Row counts (target = reference) |
|---|---|---|---|---|---|---|
| pre-wave | setup, inventory, analysis + plan (STOP A/B/C) | #24 OPEN draft, #25 OPEN, #26 OPEN (stacked chain into `main`) | n/a (docs) | n/a | n/a | n/a |
| 0 | W0-R independent Python reference (14 tables); W0-A catalog `sas_legacy`, bronze, formats, `sas_macros`, bundle, harness, CI | #27 MERGED, #28 MERGED | `databricks/evidence/w0a_bronze_load.txt`, `w0a_formats.txt`, `w0a_recon_selftest.txt`; reference self-checks 28 pytest | GREEN (bronze 9/9 = manifest; formats 9/9; harness fixture self-test PASS) | n/a (no live recon in wave 0) | bronze 487/250/500/248/114/248/455/622/18293 |
| 1 (pilot) | U1 `load_customer_accounts` | #29 MERGED | `databricks/evidence/w1_b1/recon.{json,summary.md}` | PASS (live 2024-01-31) | 52 / 0 / 2 / 1 (T-9 `acct_exceptions`) | `cust_accounts_daily` 466, `acct_exceptions` 32 |
| 2 | U2 `daily_transaction_processing`, U3 `credit_risk_scoring`, U4 `monthly_regulatory_reporting` | #31, #30, #32 MERGED (via `migration/04-wave2-integration`); independent recon #33 MERGED | `docs/migration/ts-sas-legacy-analytics_P1_wave2_recon.md`; child evidence `databricks/evidence/w2_b2/`, `w2_b3/`, `w2_b4/` | PASS x3 (independent) | U2 64/0/8/1 (T-9 `txn_rejected`); U3 96/0/10/0 (ML-1..6 green, ML-7 INFO, ML-8 N/A); U4 70/0/7/0 | U2 18903/610/46/12; U3 236/195/12; U4 59/70/6/1 + `REG_REPORT_202401.xlsx` 3 sheets |
| 3 | U5 `run_daily_banking` (`batch_summary` task) + end-to-end | #34 MERGED; independent end-to-end recon #35 MERGED | `docs/migration/ts-sas-legacy-analytics_P1_wave3_recon.md`; `docs/migration/recon/wave3/U1..U5/`; `databricks/evidence/w3_b5/` | GREEN — U1 52/0, U2 64/0, U3 96/0, U4 70/0, U5 13/0 | U5 13 / 0 / 1 / 0 (+1 INFO) | all 14 tables = reference; `archive_batch_history` 4 latest-batch of 8 total (2 full runs) |
| DEC-017 (a) | `MODEL_ID` upper-case: conversion side + reference side | #36 MERGED (conversion), #37 MERGED (reference + U3 live recon) | `docs/migration/ts-sas-legacy-analytics_P1_dec017_recon.md`; `databricks/evidence/dec017/`, `dec017_recon/` | U3 PASS | 96 / 0 (T-3 `model_id` 0 mismatches) | 236/195/12 unchanged; manifest `aea7c04a…` → `39cca40c…` (only `risk_scores.csv` changed) |
| coexistence | `sas_legacy_recon` scheduled job, staged red, ledger; cycle 4 redeploy with corrected reference | #38 MERGED, #39 MERGED | `.migration/09_parallel_run_ledger.md`; `databricks/evidence/coexistence/` | cycle 4 GREEN 5/5 | see §(ii) | — |

Local gates at wave 3 close / coexistence: `ruff` clean, `pytest` 77 → 83 passed, `bundle validate` pass. GitHub Actions produced **no check runs** on any PR (repo Actions disabled/restricted) — all gates were verified locally and by the independent recon sessions (recorded in every wave brief).

## (ii) Parallel-run ledger status

Source: `.migration/09_parallel_run_ledger.md`.

| Field | Status |
|---|---|
| Window | OPEN since 2026-09-02T01:04Z; tier `snapshot`; mode DEGRADED |
| Recon job | `sas_legacy_recon` id `1058116656072070`, 5 independent tasks, `0 15 6 * * ?` UTC, UNPAUSED, `max_concurrent_runs` 1; writes only `sas_recon.run_log` |
| Cycles | 4 total: 1 RED 4/5 (U3 `T-3:model_id`, DEC-017 baseline drift — triaged as (a)), 1 STAGED RED 3/5 (`business_date=2024-02-29` override; U5 T-1/T-2/T-8 + U3), 1 RED 4/5 (recovery from staged red confirmed), 1 GREEN 5/5 (run `371352986351516`, manifest `39cca40c…`) |
| GREEN clock | **1 of 5** consecutive GREEN cycles (started 2026-09-02T01:12:17Z). Exit criterion per ledger: 5 consecutive GREEN **and** REQ-05 SAS-produced recon, or requester acceptance at STOP E. |
| Staged red | PROVEN: fail path and task independence demonstrated (a red task never hides another); note it reds U5 only, not the whole job |
| Alerting | **WEBHOOK: NOT WIRED** — `notification-destinations list` returned `[]` again on 2026-09-02 (`databricks/evidence/signoff/notification_destinations.json`); both jobs have empty `webhook_notifications` and no `on_failure` email. Remediation carried by the daily Devin automation "sas_legacy P1 coexistence: recon ledger + remediation" (D5-004; automation id still TBD in the register — GAP G-2) |
| Cost per cycle | ~5.3–6.1 serverless task-minutes + 42 (45 on retry) warehouse statements |

## (iii) Dependency register — every D-row

Source: `.migration/04_dependency_register.md` + plan §1 (STOP C, DEC-013 turned every P1 PROPOSED-* into DECIDED / DEFERRED / ACCEPTED).

**Assertion: no P1-touching row is UNDECIDED.** The register's `Status` column still shows `UNDECIDED` literally on six INV rows (D2-INV-001, D3-INV-001, D6-INV-001, D9-INV-001, D7-INV-001, D10-INV-001); all six were decided at STOP C (plan §1: D2-INV-001 DECIDED, D3-INV-001 DECIDED, D9-INV-001 DECIDED, D7-INV-001 / D10-INV-001 ACCEPTED, D6-INV-001 OUT OF P1 SCOPE). The literal column is stale, not an open decision — corrected in this PR (see §(iii) note below and `04_dependency_register.md`).

| ID | Item | Status at STOP E | Owner | Severity | Gate |
|---|---|---|---|---|---|
| D1-001 | table→table lineage | CLOSED by inventory + analysis §5 (all P1 edges) | Devin | — | — |
| D2-001 / D2-002 / D2-003 / D2-INV-001 | macro closure, formats, autoexec | CLOSED wave 0 (12-file closure ported; 9 formats → `sas_ref`; libref map + job params) | Devin | — | — |
| D3-001..006, 008, 009 | Oracle / RAW_BANK inputs | RESOLVED (seeded, bronze snapshot); **live ingestion DEFERRED-with-condition** | Customer (REQ-01) | high for production, none for demo | REQ-01 delivery + one bronze refresh reconciled; **not a STOP E blocker under the DEGRADED caveat, but a production precondition** |
| D3-007, D10-004 | `ORA_DW.COST_OF_FUNDS` | OPEN — out of P1 scope (P2) | Customer | low (P1) | P2 plan |
| D3-010..015, D10-003 | insurance inputs / seeds | OPEN — out of P1 scope (P3) | Customer | low (P1) | P3 plan |
| D3-INV-001 | header-only inputs | DECIDED (not lineage) | Requester | — | — |
| D4-001 | `REPORTS.*` consumers | **OPEN / DEFERRED** — gold Delta is the contract; downstream readers unknown (REQ-02 unanswered) | Customer | **high** | STOP E: consumers must be identified before the flip (runbook §2) |
| D4-002 | xlsx recipients / delivery path | **OPEN / DEFERRED** — workbook built on volume `landing/reports/`; recipients + delivery unknown (REQ-02) | Customer | **high** | STOP E |
| D4-003 | `%sendmail` → notifications | **OPEN / DEFERRED** — no destination (REQ-02); no SMTP | Customer | medium | STOP E (and D5-004 webhook) |
| D5-001, D5-002, D10-005 | Control-M definitions / order | **OPEN / DEFERRED** — order 1→4 implemented as task chain; Control-M export never received (REQ-03); timezone of 05:45 schedule unknown (UTC placeholder) | Customer | **high** | STOP E: REQ-03 or explicit "Workflows schedule is sole trigger" |
| D5-003 | insurance order | OPEN — out of P1 scope | Customer | low | P3 |
| D5-004 | coexistence recon schedule + alerting | **OPEN (webhook GAP)** | Devin (job) / Customer (destination, workspace-admin) | medium | STOP E |
| D6-001, D7-001, D8-001 | BI / APIs / views | ACCEPTED (N/A) | Customer | — | — |
| D6-INV-001 | `customer_profitability` trigger | OUT OF P1 SCOPE | Customer | low | P2 |
| D9-001 | `customer_profitability` reads `CURATED.RISK_SCORES` | OPEN — P2; `sas_silver.risk_scores` published as a stable contract | P2 plan | low (P1) | P2 |
| D9-002 | intra-P1 risk-rating consumers | CLOSED by wave order | Devin | — | — |
| D9-INV-001 | `ARCHIVE.BATCH_HISTORY` shared target | DECIDED — P1 owns `sas_silver.archive_batch_history` (registered, loaded) | Devin | — | — |
| D7-INV-001, D10-INV-001 | last-run evidence gap; estate completeness UNVERIFIABLE | ACCEPTED as scope constraints (REQ-04 unanswered) | Customer | medium | recorded; not a gate |
| D10-001, D10-007 | no SAS runtime / no legacy baseline | ACCEPTED (DEC-004 b) — **STOP E entry requires REQ-05** | Requester | **blocking** | STOP E — see §(vii) |
| D10-002 | no Oracle/Teradata connectivity | DEFERRED-with-condition (REQ-01) | Customer | high (production) | as D3 |
| D10-006 | catalog `sas_legacy` | CLOSED (created 2026-09-01) | Devin | — | — |

New GAPs found by this session (not previously in the register; added there as G-rows):

| ID | GAP | Owner | Severity | Gate |
|---|---|---|---|---|
| G-1 | Migration chain never merged to `main`: PRs #24/#25/#26 OPEN; all wave PRs merged only into `migration/02-analysis-plan`. Cutover from a non-default branch has no protected-branch guarantee. | Requester (repo owner) | medium | STOP E (merge chain or record `migration/02-analysis-plan` as the release branch) |
| G-2 | D5-004 remediation automation id recorded as "TBD" — the alerting fallback cannot be audited from the register. | Devin (parent) | low | fill before STOP E |
| G-3 | Governance parity: `sas_legacy` is owner-only (zero explicit grants); no consumer or read-only principal exists; both jobs `run_as` the migration owner identity (a workspace admin). No legacy access model was ever exported (REQ-02/03 unanswered), so parity cannot be asserted. | Customer (grants) / Devin (proposal) | **high** | STOP E — see §(vi) |
| G-4 | Neither job has an `on_failure` email or webhook notification (`email_notifications: {}` on `sas_legacy_run_daily_banking`). A failed production run after the flip would be silent except through the Jobs UI / the Devin automation. | Customer (destination) | medium | STOP E (overlaps D4-003 / D5-004) |

## (iv) Unverified / declared-unexercised paths

| Path | Where declared | Why unexercised | Owner | Severity | Gate |
|---|---|---|---|---|---|
| T-9 per-type breakdown on `acct_exceptions` | DEC-015 (a) / AMB-01; wave 1 brief; wave 3 recon | literal schema has no `EXCEPTION_CODE` column | Requester | medium | STOP E (REQ-05 or production `STG_BANK.ACCT_EXCEPTIONS` schema export) |
| T-9 per-type breakdown on `txn_rejected` | DEC-015 (a) / AMB-02; wave 2 brief | no `REJECT_REASON` column | Requester | medium | STOP E (same) |
| AMB-06 missing-value comparison (`. < 0` TRUE in SAS) → `anomaly_type` for orphan accounts | `reference_impl/AMBIGUITIES.md`; audit F-5 | conversion implements literal reading (`daily_transaction_processing.py:241`); no orphan in seed | Requester | medium | STOP E (REQ-05 / production data) |
| AMB-08 `N=N_ACCOUNTS` vs `_FREQ_` when PD missing | `reference_impl/AMBIGUITIES.md`; audit F-5 | no missing PD in seed | Requester | low | STOP E (REQ-05) |
| `ABORT_ON_ERR=N` branch and the FAIL/abort branch of `run_daily_banking` | wave 3 brief; wave 3 recon | every archived step PASSed in both full runs; unit-tested only | Devin (tests) / Requester (accept) | medium | STOP E — accept as unit-tested, or request a deliberate failed-task run before cutover |
| `restart_from` repair-run row selection | wave 3 brief | mapped to Jobs repair run; never exercised live | Devin / Requester | low | STOP E accept |
| `%sendmail` (4 call sites: U1, both orchestrators, claims) | D4-003 DEFERRED | no notification destination (REQ-02), no SMTP | Customer | medium | STOP E — destination or explicit "no email" |
| Capital constants 50M / 65M / 80M (`monthly_regulatory_reporting`) | wave 2 brief | reproduced verbatim as PLACEHOLDERS, not corrected | Requester | **high** (regulatory output) | STOP E — confirm they are the production values or supply the real ones (a code change → re-recon U4) |
| Seed-unexercised U4/U3 branches: missing FICO, missing secured LTV, missing MTG LTV `else 1.00`, `Unknown` delinquency bucket, missing PROC MEANS class values | wave 2 brief | not present in the 31JAN2024 seed | Requester | medium | REQ-05 / production recon |
| Insurance units (`claims_processing`, `policy_valuation`) and `customer_profitability` | DEC-008, DEC-012 | out of P1 scope; no seed (D10-003/004) | Customer | n/a for P1 | P2/P3 plans |
| Multi-day exception accumulation (`acct_exceptions`, `txn_rejected` overwrite) | DEC-016 PROPOSED | single-date parity only | Requester | medium | STOP E (DEC-016 decision) |
| Control-M schedule timezone (05:45 `BANK_MASTER`) | plan §1 D5 row | UTC placeholder; no export (REQ-03) | Customer | medium | STOP E |

## (v) Deployables

Verified 2026-09-02 with read-only `databricks jobs get`; scrubbed JSON in `databricks/evidence/signoff/job_<id>.json` (owner e-mail replaced by `<requester>`). Bundle: `databricks/databricks.yml` + `databricks/resources/jobs.yml`, target `dev`, serverless only, `environments[].spec.dependencies = openpyxl==3.1.5, databricks-sdk==0.63.0`.

| Job | Job id | Schedule | Pause status | Tasks | `max_concurrent_runs` | Notifications |
|---|---|---|---|---|---|---|
| `sas_legacy_run_daily_banking` | `216001923865775` | `0 45 5 * * ?` UTC | **PAUSED** (as required until STOP E) | `load_customer_accounts` → `daily_transaction_processing` → `credit_risk_scoring` → `monthly_regulatory_reporting` → `batch_summary` (`run_if: ALL_DONE`) | 1 | none (`email_notifications: {}`, `webhook_notifications: {}`) — G-4 |
| `sas_legacy_recon` | `1058116656072070` | `0 15 6 * * ?` UTC | **UNPAUSED** | `recon_U1`..`recon_U5` (independent) | 1 | `no_alert_for_skipped_runs` only; no webhook — D5-004 |

Both jobs `run_as` the migration owner identity (workspace admin). Cutover-principal rule: the unpause and the Control-M repoint are performed only by the customer-held cutover principal, never by Devin (plan §6; `AGENTS.md` guardrail).

## (vi) Governance / access parity

Evidence: `databricks/evidence/signoff/uc_grants_sas_legacy.md` (read-only `SHOW GRANTS` on the catalog and on `sas_bronze`/`sas_silver`/`sas_gold`, `DESCRIBE CATALOG EXTENDED`).

| Legacy control (target-state / plan §6) | Legacy model | Current `sas_legacy` state | Parity |
|---|---|---|---|
| Libref-level access: `ORA_DW`/`RAW_BANK` read-only; `STG_BANK`/`CURATED`/`REPORTS` writable by the batch id | separate read-only sources vs. batch-writable staging/curated/report libraries | **0 explicit grants** at catalog or schema level; owner-only (migration identity, `admins` group); jobs run as owner | **GAP (G-3)** — no batch principal, no read-only consumer principal, no separation of write vs read |
| `%lock` dataset locks | serialised writers | Delta ACID / MERGE; `max_concurrent_runs: 1` | parity by design |
| `ARCHIVE.BATCH_HISTORY` audit trail | append-per-run | `sas_silver.archive_batch_history` (8 rows / 2 batches) + Jobs run history | parity (closed wave 3) |
| Email alerts `EMAIL_ONCALL` / `EMAIL_DL` | SMTP | none wired | **GAP** — REQ-02 / D4-003 / G-4 |
| Regulator xlsx delivery | `&REPORT_PATH` on the SAS server | UC volume `sas_bronze.landing/reports/` | **GAP** — REQ-02 (delivery + recipients) |
| PII columns (`PRIMARY_EMAIL`, `PHONE_NUMBER`, `CUSTOMER_NAME`) | no masking in legacy | no masking; reproduced as-is | parity (recorded; column masks are a customer decision) |
| Scheduler authority | Control-M | Workflows schedule PAUSED | GAP by design until STOP E (REQ-03) |
| Cutover principal | customer-held | never held by Devin | n/a |

Verdict: **governance parity NOT ESTABLISHED**. The legacy access model was never exported (no Control-M export, no consumer list), and the target has no grants at all beyond ownership. Minimum before any consumer flip: a read-only group with `USE CATALOG` / `USE SCHEMA` / `SELECT` on `sas_gold` (and `sas_silver` for `CURATED.*` readers), and a dedicated job run-as principal — proposals only; grants are the customer's to issue.

## (vii) DEGRADED-mode requirement — customer-executed production-data recon

| Item | Status |
|---|---|
| REQ-05 (in-perimeter SAS run of the 31JAN2024 bootstrap + `run_daily_banking`, outputs as CSV under `Data/expected/`) | **NOT AVAILABLE** — fired 2026-09-01, no response recorded |
| Consequence | Every recon verdict in this pack compares Databricks output to an independent Python re-expression of the SAS source (DEC-004 b). A shared misreading of SAS by reference and conversion is invisible to the gate (DEC-017 was exactly such a case, caught by code review, not by recon). |
| Gate | **BLOCKING for cutover** (`03_recon_tolerances.md` R-0; plan §1 D10-001 "STOP E entry still requires the customer's in-perimeter recon"; ledger exit criterion). Can only be waived by the requester explicitly accepting the DEGRADED caveat at STOP E. |

## (viii) End-to-end, production-schedule-shaped verification

| Run | What | Result |
|---|---|---|
| `736214486752362` (2026-09-02, 175 s) | full 5-task `sas_legacy_run_daily_banking`, ad hoc trigger (job PAUSED), serverless | all 5 tasks SUCCESS, no retries; U1-U4 targets re-loaded, counts unchanged |
| `568864968862809` (2026-09-02, 203 s) | second full 5-task run (idempotency under orchestration) | all 5 tasks SUCCESS; `archive_batch_history` 8 rows / 2 batch_ids; independent recon U1..U5 GREEN afterwards (wave 3 recon) |
| `371352986351516` (2026-09-02T01:12Z, cycle 4) | scheduled-shape `sas_legacy_recon` (5 tasks, bundle-deployed with corrected reference) | GREEN 5/5, 0 FAIL, manifest `39cca40c…` in every task output |

Not exercised: a run fired by the actual schedule (`0 45 5 * * ?`) — the job has never run UNPAUSED; a run triggered by Control-M (no Control-M here); a run on a business date other than 2024-01-31 with data.

## (ix) Decisions DEC-001..017

| ID | Subject | Status |
|---|---|---|
| DEC-001 | catalog `sas_legacy` + 5 schemas + libref map | APPROVED (STOP A) |
| DEC-002 | serverless only; Jobs not DLT | APPROVED |
| DEC-003 | tolerances v1; no exact PD match | APPROVED |
| DEC-004 | recon mode DEGRADED; R-0 option (b) independent reference | ACCEPTED |
| DEC-005 | `credit_risk_scoring` only model code; no re-modelling | APPROVED |
| DEC-006 | exclusions (`uc-data-migration-sas-to-databricks`, prior branches) | FACT |
| DEC-007 | notification contract (DM, STOPs/halts/wave closes only) | FACT |
| DEC-008 | insurance + cost-of-funds convertible, not reconcilable | APPROVED |
| DEC-009 | no `ow_tp` prefix; `sas_legacy_*` | ACCEPTED |
| DEC-010 | STOP A approved; scorer tolerance requester-owned | APPROVED |
| DEC-011 | STOP A re-confirmed | APPROVED |
| DEC-012 | STOP B: P1 banking-core | APPROVED |
| DEC-013 | STOP C: P1 dependency decisions, REQ-01..05 fired | APPROVED |
| DEC-014 | P1 schedule / widths / caps | APPROVED |
| DEC-015 | (a) literal Base SAS reading is the parity target | APPROVED (wave-0 STOP D) |
| DEC-016 | exception-history semantics (append vs overwrite vs partition column) | **PROPOSED — pending requester; must be decided at or before STOP E** |
| DEC-017 | `MODEL_ID` upper-case (a) | APPROVED + EXECUTED (PRs #36, #37; U3 live PASS) |

## (x) Cost roll-up

ACUs are Devin session cost as recorded in the wave briefs; Databricks usage is serverless only (no clusters anywhere).

| Wave / activity | Devin ACU (recorded) | Databricks usage |
|---|---|---|
| Wave 0 | W0-A 10.1; W0-R 13.9; orchestrator ≈ 2 | ~30 warehouse statements; 2 bundle deploys; 0 job runs |
| Wave 1 | B1 15.8; orchestrator ≈ 1.5 | ~20 statements; 3 ad hoc job runs (1 SUCCESS, 1 FAILED-on-exit-code + retry, 1 failed pre-write); 3 live recon runs |
| Wave 2 | B4 9.1; B2/B3 "same order" (9–16 each, exact figures in session ledgers, not in the repo); independent recon 3.8 | ~105 + ~40 statements; job runs B3 1, B4 2 (1 FAILED FUSE save), B2 0; 4 live recon runs |
| Wave 3 | B5 7.4; independent recon 3.8 | ~18 statements + 42 for recon; 2 full 5-task job runs (175 s, 203 s); 1 bundle deploy |
| DEC-017 (a) + coexistence (PRs #36-#39) | not recorded in repo artifacts | 4 `sas_legacy_recon` runs (~5.3–6.1 task-min + 42–45 statements each); 1 U3 ad hoc warehouse run; 2 bundle deploys |
| Signoff prep (this session) | reported in the session close message | read-only: 2 `jobs get`, 1 `notification-destinations list`, 5 warehouse statements |
| **Total recorded** | **≈ 67.4 ACU** (10.1+13.9+2+15.8+1.5+9.1+3.8+7.4+3.8) **plus** B2/B3 (≈ 18–32) and the DEC-017/coexistence sessions (unrecorded) → realistic order **≈ 90–110 ACU** | serverless only; well under the demo warehouse's idle cost |

---

## Gate summary

| Required item | State |
|---|---|
| (i) waves merged and green | MET on `migration/02-analysis-plan` (not on `main`, G-1) |
| (ii) parallel-run ledger | PARTIAL — GREEN clock 1/5; webhook GAP |
| (iii) register: no UNDECIDED | MET (literal statuses corrected this PR); OPEN/deferred rows listed with gates |
| (iv) unexercised paths | LISTED, all owned; capital constants and T-9 x2 need requester action |
| (v) deployables | MET — both jobs verified, `run_daily_banking` PAUSED |
| (vi) governance parity | **GAP** (G-3) |
| (vii) production-data recon | **NOT AVAILABLE — BLOCKING** (REQ-05) |
| (viii) end-to-end verification | MET on seed (2 full runs + cycle 4); never run from the schedule |
| (ix) decisions | DEC-016 approved (a) 2026-09-02 |
| (x) cost | rolled up; two sessions unrecorded |
