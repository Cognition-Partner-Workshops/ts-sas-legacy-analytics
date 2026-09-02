# P1 banking-core — wave 3 (end-to-end) independent reconciliation

**Mode: DEGRADED** — baseline is **reference-derived, not SAS-produced** (DEC-004 option b; no SAS runtime). Every verdict is a statement about the pinned seed snapshot `Data/csv` for business date 2024-01-31 / report_month 202401, never about production. Tolerances: v1 (`.migration/03_recon_tolerances.md`). Parity target: DEC-015 (a) literal Base SAS reading.

Reference manifest sha256 (`docs/migration/recon/reference/manifest.json`, `sha256sum` by this session): `aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7` — identical to `reference_manifest_sha256` in all five `recon.json` below and in `databricks/evidence/w3_b5/recon.json`.

Independence: this session migrated nothing and changed no converted code, reference output, tolerance, or `TableSpec`. Branch `migration/05-wave3-run-daily-banking` @ `7c40795`. Harness gate: `ruff check databricks` clean, `pytest -q databricks/tests` **77 passed**. No job was run or unpaused here; the state reconciled is the one left by the two full 5-task runs of `sas_legacy_run_daily_banking` (job 216001923865775, PAUSED): **736214486752362** and **568864968862809**, both `result_state: SUCCESS`, all 5 tasks SUCCESS (`databricks jobs get-run`, read-only, verified by this session).
## Live runs (one uncontended parent window, warehouse `565cd2fd713738c4`, 2026-09-02 UTC, each run exactly once, no retries)

| Unit | run_id | run_ts | overall | PASS | FAIL | N/A | INFO | DECL-UNEX | stmts | evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| U1 load_customer_accounts | `25d71806-5130-487d-b96a-a9f7e07d82bf` | 00:31:40Z | **PASS** | 52 | 0 | 2 | 2 | 1 | 6 | `docs/migration/recon/wave3/U1/` |
| U2 daily_transaction_processing | `b2108112-4f67-4bb2-9250-4dab0733e025` | 00:31:52Z | **PASS** | 64 | 0 | 4 | 4 | 1 | 12 | `wave3/U2/` |
| U3 credit_risk_scoring | `0628f483-870b-4deb-b73f-d5e961f06cc8` | 00:32:01Z | **PASS** | 96 | 0 | 5 | 5 | 0 | 9 | `wave3/U3/` |
| U5 run_daily_banking | `36d95ee5-250a-46e2-a497-153713a36623` | 00:32:05Z | **PASS** | 13 | 0 | 1 | 1 | 0 | 3 | `wave3/U5/` |
| U4 monthly_regulatory_reporting | `c86d0a51-f7ca-4511-9b2d-5bf3cf337cd9` | 00:32:16Z | **PASS** | 70 | 0 | 3 | 4 | 0 | 12 | `wave3/U4/` |

U4 was run with `--xlsx-path /Volumes/sas_legacy/sas_bronze/landing/reports/REG_REPORT_202401.xlsx`. The new T-12 Files-API fetch worked live: `recon.json` now records `xlsx.xlsx_source_path` (the Volume path), `xlsx_local_path`, and `xlsx_sha256 = 850d6d21a24f963fe65a1b88f8b5422fed9a7b55d5aa977aef12b5311e2d4e86`; T-12 on `monthly_rwa` PASS (existence + sheets). The wave-2 SKILL-FEEDBACK gap (spurious T-12 FAIL on Volume paths, no provenance) is closed. Note the sha differs from the wave-2 object (`5c9b14cf…`) because the workbook was rewritten by the two end-to-end runs; content check is out of T-12 scope by v1.
## Per-table verdicts (14 tables; ref rows = reference CSV; target rows = harness AND independent SQL)

| Unit | Table | Ref rows | Target rows | PASS | FAIL | N/A | DECL-UNEX | Verdict |
|---|---|---|---|---|---|---|---|---|
| U1 | sas_silver.cust_accounts_daily | 466 | 466 | 40 | 0 | 2 | 0 | PASS |
| U1 | sas_silver.acct_exceptions | 32 | 32 | 12 | 0 | 2 | 1 | PASS |
| U2 | sas_silver.daily_transactions | 18903 | 18903 | 15 | 0 | 2 | 0 | PASS |
| U2 | sas_silver.running_balances | 610 | 610 | 8 | 0 | 2 | 0 | PASS |
| U2 | sas_silver.txn_anomalies | 46 | 46 | 35 | 0 | 2 | 0 | PASS |
| U2 | sas_silver.txn_rejected | 12 | 12 | 6 | 0 | 2 | 1 | PASS |
| U3 | sas_silver.risk_scores | 236 | 236 | 65 | 0 | 4 | 0 | PASS |
| U3 | sas_silver.risk_migration | 195 | 195 | 15 | 0 | 4 | 0 | PASS |
| U3 | sas_gold.risk_summary | 12 | 12 | 16 | 0 | 2 | 0 | PASS |
| U4 | sas_gold.monthly_rwa | 59 | 59 | 16 | 0 | 1 | 0 | PASS |
| U4 | sas_gold.delinquency_aging | 70 | 70 | 14 | 0 | 2 | 0 | PASS |
| U4 | sas_gold.llp_coverage | 6 | 6 | 18 | 0 | 2 | 0 | PASS |
| U4 | sas_gold.capital_adequacy | 1 | 1 | 22 | 0 | 2 | 0 | PASS |
| U5 | sas_silver.archive_batch_history (latest batch `BANK_20240131_%`) | 4 | 4 | 13 | 0 | 2 | 0 | PASS |

Independent read-only Statement Execution checks (this session, warehouse `565cd2fd713738c4`): one `COUNT(*)` UNION over the 13 U1-U4 targets (statement `01f1a665-cb94-1257-b241-7ddcb2afa428`, SUCCEEDED) returned 466/32; 18903/610/46/12; 236/195/12; 59/70/6/1 — all 13 equal the reference manifest. `archive_batch_history`: **8 rows, 2 distinct batch_ids** (`01f1a665-ccb8-…`); per batch: `BANK_20240131_20260902T001758` PASS x4, `BANK_20240131_20260902T002106` PASS x4 (`01f1a665-cd35-…`) — 8 PASS, 0 FAIL. U5 spec reconciles the latest batch (4 steps) against the 4-row reference; the 8-row total is the append-per-run design (2 runs x 4 steps), not a duplication defect.
## N/A, INFO and DECLARED-UNEXERCISED rules (all cited)

- **T-9 `acct_exceptions` — DECLARED-UNEXERCISED**, DEC-015 (a) / AMB-01: literal output has no `EXCEPTION_TYPE`/`EXCEPTION_CODE`; keys = full row. Owner requester; close before STOP E (REQ-05 or production-schema export).
- **T-9 `txn_rejected` — DECLARED-UNEXERCISED**, DEC-015 (a) / AMB-02: no `REJECT_REASON` column; same owner/closure.
- **T-12 — N/A on the 13 non-workbook tables** ("no workbook"); PASS on `monthly_rwa` (tolerance v1: existence + sheet names only).
- **T-11 — INFO on all 14 tables**: rounding is a converted-code rule judged through T-4/T-5 row rules (all PASS).
- **ML-7 — INFO** on `risk_scores`/`risk_migration`: no account within 1e-9 of a rating edge on seed. **ML-8 `woe_*` — N/A**: runs only on an ML-1..ML-6 failure; none.
- Child-declared unexercised-by-seed (U4 AMB-07 missing-MTG-LTV / `Unknown` bucket; U5 `ABORT_ON_ERR=N` and the FAIL branch; `%sendmail` D4-003 DEFERRED; `restart_from` = Jobs repair run) remain unexercised after the end-to-end runs — every archived step is PASS, so the FAIL/abort path was never entered.
## Claims vs independent

| Source | Claim | Independent (this session) | Match |
|---|---|---|---|
| `databricks/evidence/w3_b5/recon.json` (`501ce058-…`, 00:26:31Z) | U5 PASS; 13/0/1/1/0; ref 4 / tgt 4 | U5 PASS; 13/0/1/1/0; 4/4 | yes |
| `w3_b5/idempotency.txt` | 8 rows / 2 batch_ids / 8 PASS; 13 U1-U4 counts unchanged | 8 / 2 / 8 PASS; 13 counts identical | yes |
| `w3_b5/job_runs.md` | runs 736214486752362, 568864968862809 SUCCESS, 5 tasks each | both SUCCESS, all 5 tasks SUCCESS via `jobs get-run` | yes |
| Wave-2 report (`..._P1_wave2_recon.md`) U2/U3/U4 | 64/0/4/1; 96/0/5/0; 70/0/3/0; per-table counts | identical per-unit and per-table PASS/FAIL/N-A/DECL-UNEX counts after two full end-to-end runs | yes |
| Wave-1 ledger (`05_progress.md`) U1 | 52 PASS / 0 FAIL / 2 N/A / 1 DECL-UNEX | identical | yes |

**U1-U4 results are unchanged after the end-to-end runs**: re-executing the whole pipeline twice through the orchestrator (upstream targets re-loaded by the job) reproduced every wave-1/2 verdict and row count exactly, so the per-unit idempotency claims hold under orchestration. No discrepancy found.
## DEC-017 observation (PROPOSED, not decided)

`SELECT DISTINCT model_id FROM sas_legacy.sas_silver.risk_scores` (statement `01f1a665-cdaf-…`) returns exactly one value: **`CRM-2023-Q4-v2`** (mixed case). The literal SAS reading via `%parmv` `_CASE=U` would write `CRM-2023-Q4-V2`. Reference and conversion still agree with each other, so T-3 is PASS and the deviation from legacy is invisible to the gate, as DEC-017 predicts. Neither reference nor conversion was changed here; option (a) still requires a decision and a re-run of U3 in a later window.

## Overall verdict

- **U1 PASS, U2 PASS, U3 PASS (ML-1..ML-6 green), U4 PASS (T-12 existence + sheets, now with Volume provenance), U5 PASS** — all DEGRADED.
- **Wave 3 / P1 end-to-end: RECON GREEN** on the seed snapshot. Not a statement about production volumes; a customer in-perimeter SAS recon remains the STOP E entry criterion. Open, non-blocking: DEC-016 (overwrite semantics, unexercised by single-date parity), DEC-017 (`MODEL_ID` case), T-9 DECLARED-UNEXERCISED x2.

## SKILL FEEDBACK
- `data-reconciliation`: an orchestrator-level unit whose target is an append-per-run history should state in its `recon.summary.md` both the filtered population (latest batch, 4) and the table total (8) — the summary alone reads as "4 = 4" and hides the accumulation that the idempotency evidence has to explain.
- `data-reconciliation`: T-12 `xlsx_sha256` changes on every pipeline run (workbook rewritten with identical gold content); the record should say whether a sha change between windows is expected, otherwise a reviewer reads it as drift.
