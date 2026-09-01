# Target State — ts-sas-legacy-analytics → Databricks

Version 1 (draft for STOP A). Every field is **FACT** (cited), **DISCOVERED** (probed this session), or **PROPOSED** (default awaiting confirmation at STOP A). No field is left blank; surfaces that do not apply are marked N/A with a reason.

Legend for cites: `repo:` = this repository, `probe:` = live probe run in session f5aabc52 (2026-09-01), `user:` = kickoff message.

---

## CORE (applies to every unit)

| Field | Value | Status / cite |
|---|---|---|
| Source estate | Base SAS 9.4 programs + macro library + PROC FORMAT catalogs + SAS batch orchestrators; Control-M scheduled | FACT `repo:README.md`, `repo:Config/autoexec.sas` |
| Estate size | 7 programs (4 banking, 2 insurance, 1 report), 2 batch orchestrators, 2 format programs (16 `value` statements), 92 macros (93 files in `Macro/`), 2 autoexecs, seed data for the banking chain only | FACT `repo:` file census (27,255 SAS lines total) |
| Target workspace | `DATABRICKS_DEMO_HOST` (secret name), workspace id 7474651138173478, metastore `55de74dc-…` (aws:us-west-2) | FACT `user:` + DISCOVERED `probe: databricks metastores current` |
| Target credential | `DATABRICKS_DEMO_TOKEN` (secret name only). Identity is a workspace admin (groups: `users`, `admins`) → holds CREATE CATALOG on the metastore | DISCOVERED `probe: current-user me`, `SHOW GRANTS ON METASTORE` |
| Compute | Serverless only. SQL: existing warehouse `Serverless Starter Warehouse` (id `565cd2fd713738c4`, serverless=true, RUNNING). Jobs: serverless job compute. **No clusters are ever created.** | FACT `user:` + DISCOVERED `probe: warehouses list` |
| Unity Catalog layout | Catalog `sas_legacy`; schemas `sas_legacy.sas_bronze` (raw seed / feed landing as-is), `sas_legacy.sas_silver` (STG_* and CURATED equivalents), `sas_legacy.sas_gold` (REPORTS equivalents), `sas_legacy.sas_ref` (format catalogs as reference tables), `sas_legacy.sas_recon` (recon evidence tables). Libref → schema map is fixed below. | PROPOSED — user pinned catalog `sas_legacy`; schema names are mine |
| Catalog existence | **`sas_legacy` does not exist today** in `DATABRICKS_DEMO_HOST` (`Error: Catalog 'sas_legacy' does not exist`). Creatable by the migration identity. Creation is the first wave-0 action, gated on STOP A. | DISCOVERED `probe: catalogs get sas_legacy` |
| Shared-workspace rule | Everything created lives in the dedicated catalog `sas_legacy` (jobs `sas_legacy_*`, secret scope `sas_legacy`); the requester waived the workspace's `ow_tp` prefix convention for this run (DEC-009). Never touch `banking_analytics`, `migration_demo`, `de_demo_workspace`, `tsql_demo`, `redshift_src` or any unprefixed object. Never run DDL on a table another session may hold. | FACT (org knowledge note on the shared demo workspace) |
| Libref → schema map | `ORA_DW`, `RAW_BANK`, `RAW_INS`, `TERA_DW` → `sas_legacy.sas_bronze`; `STG_BANK`, `STG_INS`, `CURATED` → `sas_legacy.sas_silver`; `REPORTS` → `sas_legacy.sas_gold`; `BANKING`/`INSURANCE`/`COMMON` format libs → `sas_legacy.sas_ref`; `ARCHIVE` → `sas_legacy.sas_silver` with `archive_` prefix. Table names: legacy member name lower-cased, e.g. `STG_BANK.CUST_ACCOUNTS_DAILY` → `sas_legacy.sas_silver.cust_accounts_daily`. | PROPOSED |
| Code language policy | Databricks SQL for PROC SQL / set-based DATA steps; PySpark (Python) for row-sequential logic that has no clean SQL form (RETAIN/BY-group running balances → window functions first; hash-object lookups → broadcast joins; macro control flow → Python). One notebook or `.py` per legacy program; shared macros become a Python package `dbx/sas_macros/`. | PROPOSED |
| Repo topology | Single repo, three roles: SOURCE = existing `Config/ Formats/ Macro/ Programs/ BatchJobs/ Data/` (read-only, never edited); TARGET = new `databricks/` (bundle, notebooks, `src/`, tests); DOCS = `docs/migration/` + `.migration/`. Existing `migration/wave1*` and `devin/*` branches are prior exploratory work and are **not** a reference implementation for this run. | PROPOSED (user excluded `uc-data-migration-sas-to-databricks` as a reference) |
| Deployment | Databricks Asset Bundle at `databricks/databricks.yml`, target `demo`, serverless job compute; `databricks bundle validate` is a CI gate. | PROPOSED |
| Branch / PR conventions | Setup: `migration/00-setup`. Units: `migrate/<pipeline>/<wave>-<unit>`; one PR per unit into `main`; PR body carries the recon output block. PR text never names the requester. | PROPOSED |
| CI gates | `pytest databricks/tests` (unit tests on PySpark logic with local fixtures), `databricks bundle validate`, `ruff`, recon-evidence block present in PR body. | PROPOSED |
| Secrets | Referenced by name only (`DATABRICKS_DEMO_HOST`, `DATABRICKS_DEMO_TOKEN`). No values in any artifact. | FACT (guardrail rules) |
| Forbidden patterns | Editing anything under SOURCE dirs; creating clusters; unprefixed UC objects; DDL on shared tables; `SELECT *` into silver/gold without an explicit column list; hard-coded dates (legacy `CURR_DT` becomes a job parameter `business_date`, default `2024-01-31` for recon). | PROPOSED |
| Test conventions | Each converted program ships with a pytest that runs it on the seed CSVs (local Spark or `databricks-connect` serverless) and asserts the row counts + key aggregates recorded in `03_recon_tolerances.md`. | PROPOSED |

## SQL profile (PROC SQL, reporting queries)

| Field | Value | Status |
|---|---|---|
| Dialect policy | PROC SQL → Databricks SQL. `CALCULATED` → CTE or repeat expression. `"&date"d` literals → `DATE '...'` parameters. SAS date/datetime numerics → `DATE`/`TIMESTAMP`. `PUT(x, fmt.)` with custom format → join to `sas_legacy.sas_ref.<format>` table; built-in formats → `date_format`/`format_number`. | PROPOSED |
| Function equivalence | `INTNX`/`INTCK` → `add_months`/`datediff`/`months_between` with explicit rounding rule; `INPUT`/`PUT` → `CAST`/`format`; `COALESCE` same; `SUM()` over missing → SAS ignores missing, Spark ignores NULL (same); **`MEAN`/`AVG` truncation and `ROUND` half-away-from-zero vs Spark HALF_UP: decided in `03_recon_tolerances.md`**. | PROPOSED |
| Materialization | STG_*/CURATED → Delta tables (full rewrite per business_date partition); REPORTS → Delta tables (not views) because legacy exports them. | PROPOSED |
| Output contract | Column names lower-snake; types per field dictionary produced in analysis; no SAS `format=` retained (formatting is presentation). | PROPOSED |

## PIPELINE profile (DATA step ETL, PROC APPEND, batch orchestrators)

| Field | Value | Status |
|---|---|---|
| Target runtime | Databricks Jobs (serverless) with one task per legacy program, dependency order copied from `BatchJobs/run_daily_banking.sas` (steps 1→4) and `run_daily_insurance.sas`. DLT not used (see `dlt-pipelines` skill: rule-driven append/lock semantics port more faithfully to Jobs + MERGE). | PROPOSED |
| Layering | bronze = seed CSV / feed as landed; silver = STG_*, CURATED; gold = REPORTS. | PROPOSED |
| Incremental vs full | `PROC APPEND` with `%lock` → `MERGE INTO` keyed on the legacy business key + `business_date`, idempotent on re-run. Snapshot tables → `INSERT OVERWRITE` the `business_date` partition. | PROPOSED |
| Reject / exception rows | Legacy reject datasets (`WORK.TXN_REJECTED`, `STG_BANK.ACCT_EXCEPTIONS`) become first-class silver tables with `reject_reason`; counts are recon metrics. | PROPOSED |
| Restart semantics | Legacy `run_step` restartability → job task retry with the partition-overwrite/MERGE idempotency above; `ABORT_ON_ERR=Y` → task failure fails the run. | PROPOSED |
| Parameterization | Job params `business_date`, `env`; `SAS_DATA_ROOT`-style paths disappear. | PROPOSED |
| Logging | `%nobs` row-count logging → a `sas_legacy.sas_recon.run_log` table row per task (table, rows_in, rows_out, rejected). | PROPOSED |

## ORCHESTRATION profile

| Field | Value | Status |
|---|---|---|
| Scheduler | Control-M is retained as the trigger during coexistence (fires the Databricks job via REST) — **cannot be probed here; no Control-M export is in the repo**. Post-cutover: Databricks Workflows schedule. | PROPOSED; D5 dependency |
| Completion signalling | Job run state via Jobs API; legacy `%sendmail` batch status → job-level email/Slack notification destination. | PROPOSED |
| Calendar | Daily banking, daily insurance, month-end regulatory (legacy gate: `PREV_YM`). | FACT `repo:BatchJobs/*`, `Config/autoexec.sas:89-92` |
| Alerting | Legacy `EMAIL_DL`/`EMAIL_ONCALL` → job notification settings; not wired in demo (no SMTP). | PROPOSED |

## CONSUMER profile

| Field | Value | Status |
|---|---|---|
| Excel exports (`%export_xlsx` in regulatory reporting, customer profitability) | Rebuild: gold Delta tables are the contract; workbook generation is a downstream notebook task using openpyxl, out of the recon gate (compared at table level). | PROPOSED; D4 |
| Email alerts (`%sendmail`) | Re-point to job notifications; body content not reconciled. | PROPOSED; D4 |
| Downstream BI | None declared in repo. | DISCOVERED (absence) — confirm at STOP A |

## ML-SCORING profile (credit_risk_scoring.sas)

| Field | Value | Status |
|---|---|---|
| What the model is | A fixed-coefficient logistic scorecard (model id `CRM-2023-Q4-v2`): hard-coded intercept, five WoE binnings, PD = 1/(1+exp(−logodds)), LGD/EAD rules, EL, rating bands 1–7. **No training, no PROC LOGISTIC, no random numbers.** | FACT `repo:Programs/Banking/credit_risk_scoring.sas:92-197` |
| Partition | This is the only model-code unit. All other programs are data code. | FACT (grep of all programs) |
| Target framework | PySpark/SQL re-expression of the scorecard, coefficients held in `sas_legacy.sas_ref.scorecard_crm_2023_q4_v2` (versioned reference table), **not** MLflow-trained. MLflow model registry: N/A — nothing is trained. | PROPOSED |
| Prediction-parity gate | Per `prediction-parity` skill; tolerance in `03_recon_tolerances.md` rows ML-1..ML-5. | PROPOSED tolerances |
| Nondeterminism | Only `SCORE_TIMESTAMP = datetime()` (excluded from parity). `exp()` may differ in the last ulp between SAS and JVM; hence PD tolerance rather than exact match. | FACT (code) / PROPOSED (tolerance) |
| Legacy bit-stability probe | **Could not be run**: no SAS runtime on this machine or in the repo's blueprint. By inspection the scorer is deterministic. Exact-match is therefore NOT promised; see `03_recon_tolerances.md` §ML. | DISCOVERED |
| Scientific judgment | Stays with the customer. No re-binning, no coefficient change, no "improvement". | FACT (kit scope) |
| D9 consumers | `customer_profitability.sas` reads `CURATED.RISK_SCORES`; `monthly_regulatory_reporting` reads risk ratings via `CUST_ACCOUNTS_DAILY`. | FACT `repo:Programs/Reports/customer_profitability.sas:8,90` |

## DATA / DEPENDENCY profile

| Field | Value | Status |
|---|---|---|
| Coexistence mechanism | **Exported snapshots** (`Data/csv/*` as committed) — there is no live Oracle/Teradata/SAS to federate to. Recon mode = **DEGRADED** (see tolerances file). | FACT `user:` "Seed data in Data/ is the recon baseline" |
| Legacy output baseline | **Gap**: `Data/` holds *inputs* only; no SAS-produced output tables are committed, and SAS cannot run here. The legacy-side comparison values must come from one of: (a) the customer running `Data/bootstrap_local_env.sh` on a SAS host and committing the outputs under `Data/expected/` — **recommended**; (b) an independent reference implementation written by the recon session (not the migrating child) from the SAS source, with the caveat that both sides are then derived from the same reading of the code. | PROPOSED decision for STOP A |
| Data target per legacy store | Oracle DW / Teradata extracts → bronze Delta (loaded from CSV via `COPY INTO`/`read_files` on a UC volume `sas_legacy.sas_bronze.landing`); flat-file feeds → same; SAS datasets (STG/CURATED/REPORTS) → silver/gold Delta. | PROPOSED |
| PII / masking | Seed data is synthetic; no masking rules. Insurance formats include policy/claim codes only. | DISCOVERED |
| Sample-data fallback | Insurance programs have **no seed data** (`Data/README.md` "Known limitations"), `ORA_DW.COST_OF_FUNDS` (read by customer_profitability) and `TERA_DW.*` have no seed either → those units can be converted but not reconciled until data is supplied (D10). | FACT `repo:Data/README.md` |
| Decommission criteria | Out of demo scope; recorded as N/A-for-now. | PROPOSED |

## Cross-profile reconciliation
- Rounding/`AVG` behaviour is shared by SQL and PIPELINE surfaces → pushed to CORE via the tolerance file (single rule).
- Exception/reject tables are defined in PIPELINE and consumed as recon metrics → single definition lives here, recon file cites it.
- ML-SCORING uses the same bronze/silver inputs as PIPELINE; its parity gate is *additional* to, not instead of, the table recon on `risk_scores`.

## Drift rules (what gets a PR rejected)
1. Any diff under `Config/ Formats/ Macro/ Programs/ BatchJobs/ Data/`.
2. Any UC object outside `sas_legacy`, any cluster definition, any non-serverless compute.
3. PR without a recon evidence block citing tolerance version.
4. Changed coefficient, bin edge, or rating band in the scorecard.
5. Hard-coded business date.
6. Requester-identifying information in PR text.

## Open questions (queued for STOP A)
See `.migration/00_context.md` §STOP A decision list.
