# Wave 3 close brief — P1 banking-core, B5 `run_daily_banking` (U5) + end-to-end recon

Repo `Cognition-Partner-Workshops/ts-sas-legacy-analytics`, branch `migration/02-analysis-plan` (all P1 waves merged). Width 1. Date 2026-09-02.

## What landed
- PR #34 (merged): `databricks/src/jobs/run_daily_banking.py` as 5th job task `batch_summary` (`run_if: ALL_DONE` after steps 1-4 = D5-001 dependency chain). Reads the run via Jobs API and appends one row per step to `sas_silver.archive_batch_history` (literal `PROC APPEND ARCHIVE.BATCH_HISTORY`; append-per-run BY DESIGN). Job `sas_legacy_run_daily_banking` stays PAUSED, serverless, `max_concurrent_runs: 1`.
- Harness (same PR): `T-3:pattern=` rule + latest-partition target filter for run-time-keyed tables; T-12 fetches `/Volumes/` workbooks via Files API and records `xlsx_source_path`/`xlsx_sha256` (closes the wave-2 harness gap). 14 new tests; 77 total green.
- PR #35 (merged): independent end-to-end recon `docs/migration/ts-sas-legacy-analytics_P1_wave3_recon.md` + `docs/migration/recon/wave3/U1..U5/`.

## Decided and why
- U5 recon spec shape: key `(batch_id, step_num)` with `batch_id` as pattern key `^BANK_20240131_\d{8}T\d{6}$`, target filtered to latest batch; times T-7. Reason: `batch_id` embeds a run-time datetime (T-7 class) and cannot equal the reference placeholder. No tolerance value changed (analysis §6 row already stated the rule).
- `restart_from` -> Jobs repair run (no code). `%sendmail` -> D4-003 DEFERRED (no destination, REQ-02). `ABORT_ON_ERR=Y` = dependency chain.

## Independent recon (one uncontended window, after two full orchestrated runs)
GREEN. U1 52/0, U2 64/0, U3 96/0, U4 70/0, U5 13/0 PASS/FAIL; all 14 tables row counts = reference (466/32; 18903/610/46/12; 236/195/12; 59/70/6/1; 4 latest-batch of 8 total). U1-U4 verdicts identical to waves 1-2 after re-execution through the orchestrator, so idempotency holds under orchestration. Mode DEGRADED — reference-derived, not SAS-produced. Manifest sha `aea7c04a…25cc7`.

## What broke / implications
- Nothing failed in review. Deployer email leaks into CLI/bundle outputs; evidence had to be scrubbed (`<requester>`) — playbook step added to skill feedback.
- `databricks-sdk` had to be added to job environment dependencies (not stdlib).

## Unproven
- FAIL/abort branch, `ABORT_ON_ERR=N`, repair-run row selection: unit-tested only (every archived step PASSed).
- T-9 on `acct_exceptions`/`txn_rejected` DECLARED-UNEXERCISED (DEC-015 (a)); closure needs REQ-05 or production schema.
- DEC-016 (append vs overwrite for `acct_exceptions`) and DEC-017 (`MODEL_ID` case; target holds `CRM-2023-Q4-v2`) remain PROPOSED. Capital constants 50M/65M/80M are reproduced placeholders — STOP E item.
- Everything is a statement about the 31JAN2024 seed snapshot, not production.

## Cost line
- W3 B5 child: 7.4 ACUs; 2 full 5-task serverless job runs (175 s, 203 s), 1 bundle deploy, ~18 short warehouse statements, live recon 1 of cap 3.
- W3 independent recon: 3.8 ACUs; 5 live recon runs (42 warehouse statements total) + 4 read-only SQL checks; no job runs.
- Parent: gather/review only. No clusters anywhere.
