# P1 banking-core — DEC-017 (a) reference correction and U3 re-reconciliation

**Mode: DEGRADED** — baseline is **reference-derived, not SAS-produced** (DEC-004 option b; no SAS runtime). Verdicts are statements about the pinned seed snapshot `Data/csv` for business date 2024-01-31, never about production. Tolerances: v1 (`.migration/03_recon_tolerances.md`), unchanged.

Independence: this session migrated nothing and did not touch `databricks/src/`, tolerances, or `TableSpec`s. The target state reconciled is the one left by PR #36's ad hoc U3 re-run (`databricks/evidence/dec017/`); no conversion was re-run here.

## Reference correction (DEC-017 (a))

`Programs/Banking/credit_risk_scoring.sas:21` calls `%parmv(model_id, _req=1)`; `Macro/parmv.sas:147` defaults `_CASE=U` and line 208 `%qupcase`s the value, so legacy writes `RISK_SCORES.MODEL_ID = 'CRM-2023-Q4-V2'`. The W0-R reference emitted the macro default literally (`CRM-2023-Q4-v2`).

Fix mirrors `%parmv` semantics at parameter entry rather than swapping the literal:

- `reference_impl/sas_semantics.py`: new `parmv(value, case="U")` (U upper / L lower / N none).
- `reference_impl/credit_risk_scoring.py`: `run(..., model_id=MODEL_ID_DEFAULT)` applies `S.parmv(model_id)` (SAS line 21) and threads the value into `scorecard()` (SAS line 192). The default literal `CRM-2023-Q4-v2` (SAS line 18) is retained unchanged.
- `reference_impl/tests/test_reference.py`: `model_id` assertion updated to `CRM-2023-Q4-V2`.
- `reference_impl/run_all.py`: manifest gains a `changelog` entry recording the decision, changed file, prior manifest SHA and reason.

Regenerated with `python -m reference_impl.run_all --business-date 2024-01-31 --report-month 202401`.

### Reference outputs before/after (sha256)

| file | before | after | changed |
|---|---|---|---|
| risk_scores.csv | `e112a246b4c01c2341e80109b8eece8b58a7da14962890c9d400f08bde5b31e8` | `9f8d21a7d00b21a58ba2b0a7b6cc41f345e17dd53b6a89c3d84e845296ace55b` | **yes** (236 rows, `model_id` column only) |
| cust_accounts_daily.csv | `089212a2…a12232` | identical | no |
| acct_exceptions.csv | `19fdf2d6…33e3d` | identical | no |
| daily_transactions.csv | `252fd814…c79d39` | identical | no |
| running_balances.csv | `ce43808d…24c36d` | identical | no |
| txn_anomalies.csv | `a72dfc09…f80c7` | identical | no |
| txn_rejected.csv | `4d395a57…d73a4` | identical | no |
| risk_migration.csv | `6b834b8f…249376` | identical | no |
| risk_summary.csv | `f5e53068…09c3f1` | identical | no |
| monthly_rwa.csv | `a42fc6e7…ba9b0b` | identical | no |
| delinquency_aging.csv | `b12070c4…db1be8` | identical | no |
| llp_coverage.csv | `579e28a0…29efb5` | identical | no |
| capital_adequacy.csv | `4c55af7c…479a94` | identical | no |
| archive_batch_history.csv | `f05c5ae5…625cc7` | identical | no |
| alternates/* (4 files) | see manifest | identical | no |

Verified by `sha256sum` of all 18 CSVs before and after regeneration: exactly one line differs (`risk_scores.csv`). Full hashes are in `docs/migration/recon/reference/manifest.json`.

**Reference manifest sha256:** old `aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7` → new `39cca40cb55d9c26a63e9c0da9fe934f7b22b3931f470a3342b7e95ae1e3c3ed`.

`databricks/tests/fixtures/reference/risk_scores.csv` (synthetic test fixture) carries no `model_id` column — unchanged.

## U3 live recon (run exactly once)

`run_recon.py --unit U3 --mode live --business-date 2024-01-31`, serverless SQL warehouse `565cd2fd713738c4`, read-only against `sas_legacy` (9 statements, 4.9 s), run_id `f5e605c5-1864-44f2-b6e3-f1fc1f1c8634`, 2026-09-02T01:03:47Z. `recon.json` records `reference_manifest_sha256 = 39cca40c…`.

| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | verdict |
|---|---|---|---|---|---|---|---|---|
| sas_silver.risk_scores | row_level | 236 | 236 | 65 | 0 | 4 | 0 | PASS |
| sas_silver.risk_migration | row_level | 195 | 195 | 15 | 0 | 4 | 0 | PASS |
| sas_gold.risk_summary | row_level | 12 | 12 | 16 | 0 | 2 | 0 | PASS |

**Overall U3: PASS** (96 PASS / 0 FAIL / 5 N/A / 5 INFO / 0 DECLARED-UNEXERCISED). `T-3 risk_scores.model_id`: PASS, `rows_compared=236 mismatches=0` — reference and target both now `CRM-2023-Q4-V2`, matching legacy `%parmv` output. Evidence: `databricks/evidence/dec017_recon/` (`recon.json`, `recon.summary.md`, `live_recon_stdout.txt`).

Local gate: `ruff check databricks` clean, `pytest -q databricks/tests` green.
