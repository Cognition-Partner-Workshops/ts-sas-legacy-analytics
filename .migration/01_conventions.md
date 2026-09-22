# Databricks Conventions

| Status | Convention | Evidence |
|---|---|---|
| PROPOSED | Catalog, schema, table, and column names use lower_snake_case. | `docs/migration/ts-sas-legacy-analytics_target_state.md:19,22-23` |
| PROPOSED | Jobs are named `sas_legacy_<program>`. | Target-state CORE; shared-workspace prefix rule. |
| PROPOSED | The Databricks Asset Bundle target is `demo`; validate with `databricks bundle validate`. | `docs/migration/ts-sas-legacy-analytics_target_state.md:25,27` |
| PROPOSED | **Libref → schema:** `ORA_DW`, `RAW_BANK`, `RAW_INS`, `TERA_DW` → `sas_legacy.sas_bronze`; `STG_BANK`, `STG_INS`, `CURATED` → `sas_legacy.sas_silver`; `REPORTS` → `sas_legacy.sas_gold`; `BANKING`/`INSURANCE`/`COMMON` format libs → `sas_legacy.sas_ref`; `ARCHIVE` → `sas_legacy.sas_silver` with `archive_` prefix. Table names: legacy member name lower-cased, e.g. `STG_BANK.CUST_ACCOUNTS_DAILY` → `sas_legacy.sas_silver.cust_accounts_daily`. | PROPOSED, copied from target-state CORE. |
| FACT | Serverless only: the existing SQL warehouse and serverless job compute are allowed; never create clusters. | `docs/migration/ts-sas-legacy-analytics_target_state.md:18` |
| PROPOSED | Use Databricks SQL for PROC SQL and set-based DATA steps; use PySpark only where row-sequential logic has no clean SQL form. Shared macros become `dbx/sas_macros/`. | `docs/migration/ts-sas-legacy-analytics_target_state.md:23` |
| PROPOSED | Never edit `Config/`, `Formats/`, `Macro/`, `Programs/`, `BatchJobs/`, or `Data/`; never create unprefixed UC objects or DDL on shared tables; never use `SELECT *` into silver/gold without an explicit column list; never hard-code dates. | `docs/migration/ts-sas-legacy-analytics_target_state.md:24,29` |
| PROPOSED | A legacy `CURR_DT` becomes the `business_date` job parameter, with `2024-01-31` as the recon default. | `docs/migration/ts-sas-legacy-analytics_target_state.md:29` |
| PROPOSED | Setup uses `migration/00-setup`; units use `migrate/<pipeline>/<wave>-<unit>`; one PR per unit into `main`; PR text never names the requester and carries the recon output block. | `docs/migration/ts-sas-legacy-analytics_target_state.md:26` |
| FACT | Refer to credentials by name only: `DATABRICKS_DEMO_HOST` and `DATABRICKS_DEMO_TOKEN`; never write values to artifacts. | `docs/migration/ts-sas-legacy-analytics_target_state.md:28` |
| PROPOSED | Each converted program ships with pytest coverage using seed/local fixtures and asserts row counts and key aggregates from `03_recon_tolerances.md`. | `docs/migration/ts-sas-legacy-analytics_target_state.md:30` |
| PROPOSED | CI gates are `pytest databricks/tests`, `databricks bundle validate`, `ruff`, and a recon-evidence block in the PR body. | `docs/migration/ts-sas-legacy-analytics_target_state.md:27` |

## What every child session must read

1. `[FACT]` Read `.migration/00_context.md` and confirm the session is awaiting STOP A.
2. `[FACT]` Read `docs/migration/ts-sas-legacy-analytics_target_state.md`.
3. `[FACT]` Read `.migration/03_recon_tolerances.md`.
4. `[PROPOSED]` Read this file and `.migration/02_glossary.md` before editing target code.
5. `[FACT]` Do not edit source directories, consult excluded repositories/branches, or write credential values.
