# P1 banking-core — wave 2 independent reconciliation

**Mode: DEGRADED** — baseline is **reference-derived, not SAS-produced** (DEC-004 option b; no SAS runtime). Every verdict below is a statement about the pinned seed snapshot `Data/csv` for business date 2024-01-31, never about production. Tolerances: v1 (`.migration/03_recon_tolerances.md`). Parity target: DEC-015 (a) literal Base SAS reading.

Reference manifest sha256 (`docs/migration/recon/reference/manifest.json`, `sha256sum` by this session): `aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7` — identical to `reference_manifest_sha256` in all three `recon.json` files below and in the children's three `recon.json` files. Same snapshot version on both sides.

Independence: this session migrated nothing in wave 2 and changed no converted code, reference output, tolerance, or `TableSpec`. Branch `migration/04-wave2-integration` @ `acc77db`. Harness gate: `ruff check databricks` clean, `pytest -q databricks/tests` 63 passed.

## Live runs (one uncontended parent window, warehouse `565cd2fd713738c4`, 2026-09-01 UTC)

| Unit | run_id | run_ts | overall | PASS | FAIL | N/A | INFO | DECL-UNEX | evidence |
|---|---|---|---|---|---|---|---|---|---|
| U2 daily_transaction_processing | `2a8d9a21-480e-4e61-a696-b4e887ce827b` | 23:57:40Z | **PASS** | 64 | 0 | 4 | 4 | 1 | `docs/migration/recon/wave2/U2/` |
| U3 credit_risk_scoring | `bc8b4c58-6246-42f3-b51e-9c0d215ef36b` | 23:57:52Z | **PASS** | 96 | 0 | 5 | 5 | 0 | `docs/migration/recon/wave2/U3/` |
| U4 monthly_regulatory_reporting | `7cdb6fb9-039f-4f37-abbe-83e3b83e7923` | 23:59:04Z | **PASS** | 70 | 0 | 3 | 4 | 0 | `docs/migration/recon/wave2/U4/` |

U4 first attempt (run_id `e913ceca-47f6-4a5b-a2ee-1956607c4738`, kept in `wave2/U4/attempt1_volumes_path/`) reported T-12 FAIL "workbook unreadable: No such file" because the harness opens `--xlsx-path` with local `openpyxl.load_workbook`, and `/Volumes/...` is not mounted on this machine. Table rules were all green on that attempt (69 PASS / 1 FAIL). Treated as a pure environment error; retried once with a read-only `databricks fs cp` of the same Volume object (11284 bytes, modified 2026-09-01T23:50:58Z, sha256 `5c9b14cf…4987db`; sheets `RWA`/`Delinquency`/`LLP_Coverage` = 59/70/6 data rows, matching the gold tables).

## Per-table verdicts (ref rows = reference CSV; target rows = harness AND independent SQL)

| Unit | Table | Ref rows | Target rows | PASS | FAIL | N/A | DECL-UNEX | Verdict |
|---|---|---|---|---|---|---|---|---|
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

Independent row counts: one read-only `SELECT COUNT(*)` UNION over the 11 tables via the Statement Execution API (statement `01f1a661-24c6-1561-94bb-ca8bb8e344d9`, SUCCEEDED) returned exactly the counts above; all 11 equal the reference manifest row counts.

## N/A and DECLARED-UNEXERCISED rules (all cited)

- **T-9 `txn_rejected` — DECLARED-UNEXERCISED**, DEC-015 (a) / AMB-02: the literal SAS output has no `REJECT_REASON` column (the `DROP` applies to every OUTPUT data set), so the per-reject-rule breakdown has no grouping column; keys are the full row (multiset compare). Owner: requester; close before STOP E via REQ-05 or a production-schema export.
- **T-12 — N/A on the 10 non-workbook tables** ("no workbook"; T-12 reconciles nothing beyond the feeding gold table). On `monthly_rwa` it is PASS (existence + 3 sheets).
- **ML-8 `woe_*` — N/A on `risk_scores`, `risk_migration`**: feature-parity probe runs only when an ML-1..ML-6 row fails; none did.
- Child-declared (U4, `05_progress.md` ledger row): AMB-07 missing-MTG-LTV (risk weight 1.00) and `Unknown` aging bucket unexercised by seed — confirmed in the reference CSVs: `monthly_rwa` MTG rows carry only 0.35/0.5, `delinquency_aging` has no `Unknown` bucket; the target agrees trivially there.

## Claims vs independent

| Unit | Child run_id (evidence dir) | Child claim | Independent | Match |
|---|---|---|---|---|
| U2 | `12462c12-…` (`databricks/evidence/w2_b2/`) | PASS; 64/0/4/1; 15-8-35-6 per table | PASS; 64/0/4/1; identical per-table counts | yes |
| U3 | `94664a10-…` (`w2_b3/`) | PASS; 96/0/5/0; 65-15-16 | PASS; 96/0/5/0; identical | yes |
| U4 | `2a8c6f9e-…` (`w2_b4/`) | PASS; 70/0/3/0; 16-14-18-22; T-12 sheets `[RWA, Delinquency, LLP_Coverage]` | PASS; 70/0/3/0; identical; same 3 sheets from the Volume object | yes |

Every per-table PASS/FAIL/N-A/DECL-UNEX count, both row counts, and the manifest sha in the children's `recon.json` are reproduced exactly. No discrepancy found. The child U4 T-12 PASS must also have used a locally readable copy (the harness cannot open Volumes paths); its summary does not record which path.

## Overall verdict
- **U2: PASS**, **U3: PASS** (ML-1..ML-6 green; ML-7 lists no band-edge accounts), **U4: PASS** (T-12 existence + sheets only, per v1) — all DEGRADED.
- **Wave 2: RECON GREEN** on the seed snapshot. Not a statement about production volumes (847k accounts / 2.3M txns); customer in-perimeter SAS recon remains the STOP E entry criterion. DEC-016 (overwrite semantics for `acct_exceptions`/`txn_rejected`) is still PROPOSED and is not exercised by single-date parity.

## SKILL FEEDBACK
- `databricks/recon/rules.py::t12` opens `--xlsx-path` with local `openpyxl.load_workbook`; a `/Volumes/...` path (the job's real output location) yields a spurious T-12 FAIL. Harness should fetch `dbfs:/Volumes/...` paths via the Files API (read-only) before loading, or document that `--xlsx-path` must be a local copy and record the source object + sha in `recon.json`. Not fixed here (independent session; no repo changes).
- `recon.summary.md` does not record the `--xlsx-path` actually used, so the T-12 provenance of a PASS is invisible to a reviewer.
