# P1 banking-core — Migration Plan (for STOP C)

Inputs verified current: analysis `ts-sas-legacy-analytics_P1_banking_core_analysis.md` (same commit), target-state profiles for CORE/SQL/PIPELINE/ORCHESTRATION/CONSUMER/ML-SCORING/DATA (all workload types in P1 covered), tolerances v1 approved (DEC-005), notification contract DEC-007. Nothing here launches; every wave below waits for STOP C.

---

## 1. Dependency decision table (decide mode — no UNDECIDED left)

| ID | Class | Decision | Routing point | Cutover condition | Decommission condition | Owner | Request |
|---|---|---|---|---|---|---|---|
| D2-001, D2-INV-001 | D2 | **Port the 12-file closure only**, as behaviour not text: `parmv`→parameter validation helper, `nobs`→`COUNT(*)`, `lock`→no-op (Delta ACID; recorded), `sendmail`→job-notification stub, `export_xlsx`→openpyxl task, `export_dbms`→not ported (`export_xlsx` is a wrapper over it, `Macro/export_xlsx.sas:3`; the openpyxl task replaces the whole behaviour); transitive helpers (`handle get_data_attr loop seplist useridToEmail queryActiveDirectory`) not ported. 80 files stay PROPOSED-unused, untouched. | wave 0 `databricks/src/sas_macros/` | n/a | never deleted by this migration | Devin | — |
| D2-002 | D2 | 9 banking formats → `sas_ref.fmt_<name>` lookup tables (+ `fmt_registry`); insurance 5 deferred with P3 | wave 0 | n/a | n/a | Devin | — |
| D2-003 | D2 | autoexec → libref→schema map (`01_conventions.md`) + job parameters `business_date` (default `2024-01-31` for recon), `report_month` (`202401`), `region` (`ALL`), `abort_on_err` (`Y`) | wave 0 bundle `variables` | n/a | n/a | Devin | — |
| D3-001..006, 008, 009 | D3 | Recon and coexistence run from **bronze snapshot** loaded from `Data/csv` (materialize, tier S: full copy, verify by row count + sha256 manifest). Live ingestion from Oracle/raw is **DEFERRED-with-condition**. | wave 0 bronze load | closes when REQ-01 delivers an extract feed or federation path, and one bronze refresh reconciles to it | legacy feed retired after 2 clean cutover cycles | Customer (REQ-01) / Devin (loader) | **REQ-01** |
| D3-INV-001 | D3 | **Header-only declarations are documentation, not lineage.** Edges `daily_transactions→U4`, `collateral→U4` dropped. Enables wave-2 width 3. (P2's `COST_OF_FUNDS` handled in P2 plan.) | analysis §5 | n/a | n/a | Requester (approves via STOP C) | — |
| D4-001 | D4 | Gold Delta tables **are** the report contract; unknown downstream readers re-point at cutover | wave 2 B3/B4 | consumers identified (REQ-02 answer) and re-pointed | n/a | Customer | REQ-02 |
| D4-002 | D4 | `REG_REPORT_<yyyymm>.xlsx` rebuilt by an openpyxl job task writing to `sas_bronze.landing/reports/` volume; file existence + 4 sheets asserted; content not reconciled (T-12) | wave 2 B4 | regulator recipients confirm the file path/delivery (REQ-02) | legacy `&REPORT_PATH` writer stopped | Customer | REQ-02 |
| D4-003 | D4 | `%sendmail` → Databricks Jobs email/webhook notifications on task failure + run success; no SMTP in demo → **DEFERRED-with-condition** | wave 3 B5 | notification destination provided (REQ-02) | n/a | Customer | REQ-02 |
| D5-001/002, D10-005 | D5 | Order 1→4 becomes Workflow task dependencies; `restart_from` becomes "repair run" from failed task. Job ships **PAUSED** (schedule 05:45 daily per `run_daily_banking.sas:6` `Control-M BANK_MASTER`; timezone unknown → `UTC` placeholder, flagged). Trigger authority remains Control-M until STOP E; **DEFERRED-with-condition** | wave 3 B5 | REQ-03 export received *or* requester confirms Workflows schedule as sole trigger at STOP E | Control-M job disabled after 2 clean cycles | Customer | **REQ-03** |
| D9-002 | D9 | Intra-P1; `RISK_RATING` originates in demographics (bronze), so U2/U3 depend only on U1. Handled by wave order. | wave order | n/a | n/a | Devin | — |
| D9-INV-001 | D6 | **P1 owns `sas_silver.archive_batch_history`** (append-only, key `batch_id, step_num`). Insurance orchestrator appends to the same table when P3 migrates; until then no second writer exists on the target. Registered as a P1 write target. | wave 3 B5 | n/a | n/a | Devin (P1) | — |
| D9-001, D6-INV-001 | D9/D6 | Not touched by P1. `sas_silver.risk_scores`/`cust_accounts_daily`/`daily_transactions` are published as stable contracts for P2. Decision deferred to the P2 plan, explicitly. | — | — | — | P2 plan | — |
| D7-INV-001, D10-INV-001 | D7/D10 | **Accepted as scope constraints** (no last-run evidence for 5 units; completeness UNVERIFIABLE). REQ-04 asks for a `sasautos`/metadata listing to close D10-INV-001. | — | — | — | Customer | REQ-04 |
| D10-001 | D10 | **Accepted as scope constraint**: recon is reference-derived (DEC-004). STOP E entry still requires the customer's in-perimeter recon on production volumes (03_recon_tolerances.md). | W0-R | REQ-05 result present at STOP E | — | Requester | **REQ-05** |
| D10-002 | D10 | as D3 row: DEFERRED-with-condition (REQ-01) | — | REQ-01 | — | Customer | REQ-01 |
| D10-006 | D10 | **Devin creates `sas_legacy`** and the 5 schemas as the first wave-0 action (STOP A granted; DEC-002) | wave 0 W0-A | n/a | n/a | Devin | — |
| D10-007 | D10 | option (b): independent recon session builds the Python reference from SAS source (W0-R) | wave 0 W0-R | n/a | n/a | Devin (non-migrating session) | — |
| D10-003, D10-004 | D10 | Not touched by P1; remain OPEN for P3/P2 | — | — | — | — | — |

## 2. Fired lead-time requests

All requests are addressed to the requester (sole customer contact per DEC-007) and fired in the STOP C Slack DM; none blocks conversion, REQ-01/03/05 gate STOP E.

| Req | Ask | Recipient | Expected lead time | Status |
|---|---|---|---|---|
| REQ-01 | Oracle DW (`CUST_ACCOUNTS`, `CUST_DEMOGRAPHICS`, `BUREAU_SCORES`, `PAYMENT_HISTORY`, `COLLATERAL`, `LOAN_DETAILS`) and `RAW_BANK` txn-feed delivery path for the target: extract drop to a UC volume, or Lakehouse Federation credentials (secret names only) | requester → source-DBA | unknown; assume ≥ 1 week | FIRED 2026-09-01 |
| REQ-02 | Names of downstream consumers of `REPORTS.*`, delivery path for `REG_REPORT_*.xlsx`, and notification destination replacing `EMAIL_DL`/`EMAIL_ONCALL` | requester | days | FIRED 2026-09-01 |
| REQ-03 | Control-M job/condition export for `run_daily_banking` | requester → scheduler team | days | FIRED 2026-09-01 |
| REQ-04 | `sasautos` directory listing / SAS metadata export to close completeness `UNVERIFIABLE` | requester | days | FIRED 2026-09-01 |
| REQ-05 | One in-perimeter SAS run of `Data/README.md` bootstrap + `run_daily_banking` on the 31JAN2024 seeds, outputs delivered as CSV (`Data/expected/`) — upgrades recon from reference-derived to SAS-produced | requester | unknown | FIRED 2026-09-01 |

## 3. Wave 0 — scaffolding delta (what does not exist yet)

Repo today has no `databricks/` tree, no bundle, no CI. Wave 0 creates, serially, in one migrating session (W0-A) plus one independent session (W0-R):

W0-A (branch `migration/02-wave0-scaffolding`, PR to `migration/01-inventory` chain — PRs stack on the previous migration branch until `main` merge is authorised):
1. `CREATE CATALOG sas_legacy`; schemas `sas_bronze sas_silver sas_gold sas_ref sas_recon`; volume `sas_bronze.landing`. Register in `05_progress.md` first.
2. Bronze materialization (size tier S, < 20k rows/table): upload 9 CSVs to the volume, `COPY INTO` typed bronze tables (`ddMONyyyy` dates, `DECIMAL(18,2)` money, `STRING` ids); verify row counts against the manifest in `05_progress.md`; write `sas_bronze._manifest` (file, rows, sha256, business_date).
3. `sas_ref.fmt_*` (9) + `fmt_registry` from `Formats/banking_formats.sas`; assert value counts against `Formats/banking_formats.sas`.
4. `databricks/src/sas_macros/` Python package (D2 decision), `databricks/tests/` pytest skeleton, `ruff` config.
5. Bundle `databricks/databricks.yml`: targets `dev` (default), variables from D2-003, job shells `sas_legacy_run_daily_banking` (4 tasks, `serverless`, schedule PAUSED), `sas_legacy_recon` (harness), warehouse id `565cd2fd713738c4`.
6. Recon harness `databricks/recon/`: `run_recon.py --unit <U> --mode fixture|live --business-date` comparing target tables to reference CSVs by the T-/ML- rules, emitting `recon.json` + `recon.summary.md`; `sas_recon.run_log` table.
7. CI (`.github/workflows/dbx-migration.yml`): `ruff check`, `pytest databricks/tests`, `databricks bundle validate -t dev` (needs secrets by name only).

W0-R (independent `!dbx_data_reconciliation` session, reference-build mode; branch `migration/02-wave0-reference`): plain-Python implementation of U1-U5 from the SAS source only, run on `Data/csv` → `docs/migration/recon/reference/<table>.csv` + `manifest.json` (sha256, source commit, "reference-derived, not SAS-produced"). It never sees converted code; migrating children never edit `recon/reference/`.

Environment ownership: `sas_legacy` is owned by the migration identity (DEC-002); child sessions write only to their registered targets; the recon session has read-only intent on silver/gold and writes only `sas_recon.*`.

## 4. Execution schedule

Branch convention `migration/<NN>-<slug>`; every PR in P1 is a **single collapsed PR per batch** (no XL units: largest is L). Base of each PR: the previous migration branch (`00-setup → 01-inventory → 02-wave0-* → 03-* …`). Targets in `sas_legacy.<schema>` (lower_snake). Idempotency rule for every writer: MERGE on the table's T-2 key (or `INSERT OVERWRITE` partition `business_date` for full-replace tables), so a second run changes 0 rows; children prove it by running twice and diffing counts (`recon.summary.md` "idempotency" line).

| Wave | Batch | Units | Branch | Profiles | Write targets | Recon rows (analysis §6) | Required artifacts | Size |
|---|---|---|---|---|---|---|---|---|
| 0 | W0-A | scaffolding | `migration/02-wave0-scaffolding` | CORE, DATA | `sas_bronze.*`, `sas_ref.*`, `sas_recon.run_log` | bronze row counts vs manifest | PR, `sas_bronze._manifest`, CI green | M |
| 0 | W0-R | reference impl | `migration/02-wave0-reference` | recon-harness | repo files only | self-check: reference row counts logged | PR, `recon/reference/*.csv`, `manifest.json` | M |
| 1 (pilot) | B1 | U1 | `migration/03-wave1-load-customer-accounts` | PIPELINE, SQL | `sas_silver.cust_accounts_daily`, `sas_silver.acct_exceptions` | U1 rows | PR, `recon.json`, `recon.summary.md`, SKILL FEEDBACK section | M |
| 2 | B2 | U2 | `migration/04-wave2-daily-transactions` | PIPELINE | `sas_silver.daily_transactions`, `running_balances`, `txn_anomalies`, `txn_rejected` | U2 rows | same | L |
| 2 | B3 | U3 | `migration/04-wave2-credit-risk-scoring` | ML-SCORING (+ prediction-parity) | `sas_silver.risk_scores`, `risk_migration`, `sas_gold.risk_summary` | U3 rows, ML-1..8 | same + parity report with `woe_*` debug on failure | L |
| 2 | B4 | U4 | `migration/04-wave2-monthly-regulatory-reporting` | SQL, CONSUMER | `sas_gold.monthly_rwa`, `delinquency_aging`, `llp_coverage`, `capital_adequacy`; volume `landing/reports/` | U4 rows; xlsx existence | same | M |
| 3 | B5 | U5 | `migration/05-wave3-run-daily-banking` | ORCHESTRATION | `sas_silver.archive_batch_history`; job `sas_legacy_run_daily_banking` | U5 rows + full pipeline end-to-end fixture run | same + job run URL/ids | S |

Disjoint namespaces are the write-target column: no overlap within any wave. Wave 2 batches read only wave-1 outputs and bronze.

**Width**: wave 0 serial; wave 1 = 1 (pilot); wave 2 = **3** (given D3-INV-001 decision above); wave 3 = 1. Dynamic workflow: **not used** (≤ 3 batches per wave; hand-managed child sessions).
**Legacy-query concurrency cap**: n/a (no live legacy). **Warehouse**: one serverless SQL warehouse shared by ≤ 3 children + recon; no cap needed.
**Circuit breaker**: 3 same-class failures (05_progress.md) — with width 3 that means "all of wave 2", so effectively any 2 same-class failures in wave 2 pause the third launch for triage.
**Run-mode budget per child**: fixture mode unlimited (local reference CSVs, warehouse reads only); **one** live window (`--mode live`) per child at PR-ready, plus the parent-side independent live pass per wave. **Fixture volume**: full seeds (all tables < 20k rows; no sampling).
**Review rounds**: cap 2 rounds per PR before the unit is reopened as a fresh child with evidence attached. **Full re-runs**: cap 3 per unit; the 4th escalates to the requester with the cost line.
**Parallel-run window** (coexistence, `!dbx_parallel_run`): tier "snapshot" — no live legacy exists; the scheduled recon re-runs the fixture battery daily on the PAUSED-job's manual runs until REQ-05 output arrives, then upgrades to SAS-produced comparison.

**Wall-clock projection** (child ≈ 2-4 h for M/L incl. one live window; recon pass ≈ 1 h; STOP D is notify-only so it adds no wait):
wave 0 ≈ 4 h (W0-A 3 h, W0-R 3 h concurrent) → pilot ≈ 4 h + 1 h recon + feedback harvest 0.5 h → wave 2 ≈ 4 h (parallel) + 1.5 h recon → wave 3 ≈ 2 h + 1 h end-to-end recon → coexistence setup 1 h → signoff pack + independent audit 3 h. **≈ 22 h machine wall-clock, i.e. 1 orchestrator session plus STOP E turnaround.** Serial alternative (width 1) ≈ 30 h; width buys ~8 h. Per-child cost line is recorded in each wave-close brief (planning assumption 5-10 ACUs per M/L child; measured in the pilot).

## 5. Gate specification (mechanical, per batch)

A batch PR is **merge-eligible** only when all hold; the parent reads the artifacts, never the chat:
1. `databricks/recon/recon.json` for every target table in the batch, produced by `python -m recon.run_recon --unit <U> --mode live --business-date 2024-01-31 --out databricks/recon/out/<U>/`, with `verdict: PASS` on every T-/ML- rule listed in analysis §6 for the unit; baseline = `docs/migration/recon/reference/` at the manifest sha in the JSON; mode field = `DEGRADED`; caveat string present.
2. `recon.summary.md` (≤ 30 lines) rendered in the PR body with: declared populations, source-volume assertions (bronze counts = manifest), money lines, idempotency proof (run 2 delta = 0 rows), live-window count = 1.
3. Write targets registered in `05_progress.md` **before** the first load; collision check by the parent (grep of the register) before launch.
4. CI green: `ruff check`, `pytest databricks/tests` (unit's fixture test asserts row counts + key aggregates copied from the reference manifest, never from the child's own output), `databricks bundle validate -t dev`.
5. No diff under `Config/ Formats/ Macro/ Programs/ BatchJobs/ Data/`; no diff under `docs/migration/recon/reference/`.
6. PR body contains a `## SKILL FEEDBACK` section (may be "none").
7. Wave merge gate (parent): the independent `<P1>_wave<N>_recon.md` from `!dbx_data_reconciliation` reports PASS for every unit; only then the wave's PRs merge, together, and STOP D fires.

## 6. Governance mapping (D8)

| Legacy control | Target | Status |
|---|---|---|
| Libref-level access (`ORA_DW` read-only, `STG_BANK`/`CURATED`/`REPORTS` writable by batch id) | UC schema grants inside `sas_legacy` only; migration identity owns; no grants outside the catalog | GAP until wave 0 creates schemas (then closed) |
| `%lock` dataset locks | Delta ACID / MERGE | closed by design |
| `ARCHIVE.BATCH_HISTORY` audit trail | `sas_silver.archive_batch_history` + Jobs run history | closed in wave 3 |
| Email alerts (`EMAIL_ONCALL`, `EMAIL_DL`) | Jobs notifications; destination unknown | **GAP** — REQ-02 |
| Regulator xlsx delivery path | UC volume `landing/reports/` | **GAP** — REQ-02 (delivery) |
| PII columns (`PRIMARY_EMAIL`, `PHONE_NUMBER`, `CUSTOMER_NAME` in `cust_accounts_daily`, `acct_exceptions`) | no masking in legacy; reproduce as-is in the demo catalog; **flag** — column masks are a customer decision, not applied by this migration | GAP (accepted for demo; recorded) |
| Scheduler authority (Control-M) | Workflows schedule PAUSED until STOP E | GAP — REQ-03 |
| Cutover principal | never held by Devin | n/a |

## 7. Review contract

Reviewers read the unit PR in this order: `recon.summary.md` → dictionary deltas (`p1_columns.md` vs target DDL) → SKILL FEEDBACK → code. 2 review rounds max per PR; the parent harvests SKILL FEEDBACK after the pilot (mandatory before wave 2 launch) and after every wave.

## 8. Risk register (delta vs analysis §7)

| Risk | Mitigation in this plan |
|---|---|
| Reference shares a misreading with converted code (DEC-004) | W0-R is a separate session, sees SAS only; REQ-05 upgrade path; caveat on every report |
| Width-3 wave 2 masks a systematic dialect trap | pilot U1 first; each wave-2 batch is a distinct class, so a trap in one does not replicate; breaker at 3 |
| Bronze typing wrong | asserted in wave 0 (manifest) and by T-2/T-3 in the pilot |
| Trigger/consumers unverifiable | job PAUSED; REQ-02/03 gate STOP E, not conversion |
| Cost runaway on re-runs | caps in §4; cost line in every wave-close brief |

## Validation against playbook spec

(1) every dependency in the register that P1 touches has a decision (§1), no UNDECIDED; (2) every required request fired (§2); (3) schedule complete with branches, targets, recon rows, width, wall-clock (§4); (4) pilot precedes fan-out; (5) gates mechanical (§5); (6) wave-0 scaffolding delta explicit (§3); (7) governance GAP rows named (§6).
