# Reports Domain: SAS Migration Assessment

## Executive Summary

The Reports domain consists of a single SAS program (`customer_profitability.sas`, 176 lines) that calculates customer-level P&L by combining interest income, fee income, operating costs, and expected credit losses from the Banking domain. It produces three output datasets (customer-level P&L, segment summary, branch summary) and an XLSX export. All upstream data dependencies originate from Banking domain pipelines, making this a **terminal node** in the data lineage graph — it must be migrated last, after all Banking ETL and risk scoring programs are in place.

---

## 1. Artifact Inventory

| Filename | Lines | Primary Purpose | SAS PROCs Used | DATA Steps | SQL Pass-Throughs |
|---|---|---|---|---|---|
| `customer_profitability.sas` | 176 | Customer-level P&L calculation combining interest income, fee income, operating costs, and credit losses; produces segment and branch profitability roll-ups with XLSX export | PROC SQL (×3), PROC MEANS (×2), PROC DATASETS (×1) | 1 | 0 |

### PROC / Step Breakdown

| Step | Type | Purpose |
|---|---|---|
| Step 1 (lines 35–60) | PROC SQL | Aggregate interest income by customer from `STG_BANK.CUST_ACCOUNTS_DAILY` — splits lending income vs. deposit cost to derive net interest income |
| Step 2 (lines 65–80) | PROC SQL | Aggregate fee income and interest credited from `CURATED.DAILY_TRANSACTIONS` for the reporting month |
| Step 3 (lines 85–95) | PROC SQL | Pull latest expected credit loss (ECL) per customer from `CURATED.RISK_SCORES` |
| Step 4 (lines 100–135) | DATA step | Merge the three WORK tables by `CUSTOMER_ID`; compute operating cost allocation ($15/account/month), total revenue, net profit, annualized ROA, and profitability tier |
| Step 5 (lines 140–157) | PROC MEANS (×2) | Summarize customer P&L by `CUSTOMER_SEGMENT` and by `BRANCH_ID`/`REGION_CODE` |
| Export (lines 159–163) | %export_xlsx | Export segment profitability to XLSX file |
| Cleanup (lines 170–172) | PROC DATASETS | Delete temporary WORK datasets |

---

## 2. Data Lineage

### customer_profitability.sas

#### Input Datasets

| Library.Dataset | Domain | Description | Used In Step |
|---|---|---|---|
| `STG_BANK.CUST_ACCOUNTS_DAILY` | Banking (Staging) | Daily account snapshot — balances, interest rates, account types, customer segment, region, branch | Step 1 |
| `CURATED.DAILY_TRANSACTIONS` | Banking (Curated) | Processed daily transactions — fees, interest credits, transaction amounts | Step 2 |
| `CURATED.RISK_SCORES` | Banking (Curated) | Credit risk scores with expected loss amounts per customer | Step 3 |

> **Note:** The program header references `ORA_DW.COST_OF_FUNDS` as an input, but this table is **not referenced** in the actual code. This is either a dead comment from a prior version or a planned enhancement that was never implemented. Verify with business stakeholders whether cost-of-funds adjustments should be incorporated during migration.

#### Output Datasets

| Library.Dataset | Description | Granularity |
|---|---|---|
| `REPORTS.CUSTOMER_PNL` | Customer-level profitability with net interest income, fee income, operating cost, ECL, net profit, ROA, and profit tier | One row per customer per month |
| `REPORTS.SEGMENT_PROFITABILITY` | Aggregated revenue, cost, and profit metrics by customer segment | One row per segment |
| `REPORTS.BRANCH_PROFITABILITY` | Aggregated revenue, cost, and profit metrics by branch and region | One row per branch/region |

#### External File Outputs

| Path | Format | Description |
|---|---|---|
| `&REPORT_PATH/PROFITABILITY_<YYYYMM>.xlsx` | XLSX | Segment profitability export (sheet: `By_Segment`) |

> `REPORT_PATH` resolves to `/data/sas/reports/output` per `Config/autoexec.sas`.

#### Temporary WORK Datasets

| Dataset | Created In | Consumed In | Deleted In |
|---|---|---|---|
| `WORK.INTEREST_INCOME` | Step 1 | Step 4 | Cleanup |
| `WORK.FEE_INCOME` | Step 2 | Step 4 | Cleanup |
| `WORK.ECL` | Step 3 | Step 4 | Cleanup |

#### Cross-Domain Dependencies

All three input datasets originate from the **Banking domain**:

```
Programs/Banking/account_loading.sas  ──▶  STG_BANK.CUST_ACCOUNTS_DAILY
Programs/Banking/transaction_etl.sas  ──▶  CURATED.DAILY_TRANSACTIONS
Programs/Banking/credit_risk.sas      ──▶  CURATED.RISK_SCORES
                                              │
                                              ▼
                              Programs/Reports/customer_profitability.sas
                                              │
                                              ▼
                              REPORTS.CUSTOMER_PNL
                              REPORTS.SEGMENT_PROFITABILITY
                              REPORTS.BRANCH_PROFITABILITY
```

There are **no direct Insurance domain data dependencies** in this program. However, the `CURATED` library is shared across domains, and the `fmtsearch` path in `autoexec.sas` includes both `BANKING` and `INSURANCE` format catalogs.

---

## 3. Macro Dependencies

### Directly Referenced Macros

| Macro | Source File | Parameters | Purpose | Shared Across Domains |
|---|---|---|---|---|
| `%parmv` | `Macro/parmv.sas` (359 lines) | Positional: macro variable name; Named: `_req`, `_words`, `_case`, `_val`, `_def`, `_varchk`, `_msg` | Parameter validation utility — sets `parmerr=1` and writes ERROR to log for invalid values | Yes — used by virtually all programs |
| `%nobs` | `Macro/nobs.sas` (253 lines) | Positional: `DATA`; Named: `MVAR` | Returns observation count from dataset descriptor or via PROC SQL fallback | Yes — used across Banking, Insurance, Reports |
| `%export_xlsx` | `Macro/export_xlsx.sas` (101 lines) | `DATA`, `PATH`, `REPLACE`, `LABEL` | Wrapper around `%export_dbms` for XLSX export via PROC EXPORT | Yes — general-purpose utility |

### Transitively Called Macros

| Macro | Source File | Called By | Purpose |
|---|---|---|---|
| `%export_dbms` | `Macro/export_dbms.sas` (520 lines) | `%export_xlsx` | Generic PROC EXPORT wrapper supporting XLSX, XLS, SPSS, STATA output formats |

### Macro Call Graph

```
customer_profitability.sas
  ├── %parmv            (parameter validation)
  ├── %nobs             (observation count for log message)
  │     └── %parmv
  └── %export_xlsx      (Excel export)
        ├── %parmv
        └── %export_dbms
              └── %parmv
```

### Global Macro Variables Referenced

| Variable | Defined In | Value/Pattern | Usage |
|---|---|---|---|
| `&PREV_YM` | `Config/autoexec.sas` | `YYYYMM` (previous month) | Default `report_month` parameter |
| `&REPORT_PATH` | `Config/autoexec.sas` | `/data/sas/reports/output` | XLSX output directory |

### Potential Issue: Parameter Mismatch

The `%export_xlsx` invocation at lines 159–163 passes `file=` and `sheet=` parameters:
```sas
%export_xlsx(
    data=REPORTS.SEGMENT_PROFITABILITY,
    file=&REPORT_PATH/PROFITABILITY_&report_month..xlsx,
    sheet=By_Segment
)
```
However, the `%export_xlsx` macro definition accepts `PATH=` (not `file=`) and has no `sheet=` parameter. This is either:
1. A version mismatch (the production macro may have additional parameters not reflected in this codebase), or
2. A latent bug where the XLSX export silently fails because `PATH=` is required but not provided.

**Action:** Verify against the production SAS environment before migration.

---

## 4. Complexity Scores

### customer_profitability.sas

| Dimension | Score (1–5) | Rationale |
|---|---|---|
| **Data Volume Handling** | 3 | Monthly customer-level aggregation across accounts, transactions, and risk scores. Moderate volume but no explicit partitioning or performance tuning (no indexes, hash objects, or pass-through optimization). |
| **Business Logic Complexity** | 3 | Multi-component P&L calculation (interest income, fee income, operating cost allocation, ECL, ROA, profit tier). Logic is clear but domain-specific — requires financial SME validation. Lending vs. deposit classification by account type codes is hardcoded. |
| **External Dependencies** | 3 | Depends on 3 upstream Banking datasets (must all be migrated first). References Oracle DW in header (unclear if active). Produces XLSX file output requiring export tooling. Scheduled via Control-M (`BANK_MONTHLY_03`). |
| **Error Handling Sophistication** | 2 | Parameter validation via `%parmv` for `report_month`. No explicit checks for empty input datasets, no try/catch equivalent, no row count assertions, no email alerts on failure. Relies on global `ABORT_ON_ERR` and `nofmterr` options. |
| **Macro Usage Depth** | 2 | Uses 3 macros directly (4 transitively). Shallow call chain — no recursive macros, no dynamic code generation, no conditional macro logic beyond basic parameter validation. |

#### Overall Weighted Score

Using weights: Data Volume (20%), Business Logic (30%), External Dependencies (20%), Error Handling (15%), Macro Depth (15%):

**Overall: 2.65 / 5 — Medium Complexity**

```
(3 × 0.20) + (3 × 0.30) + (3 × 0.20) + (2 × 0.15) + (2 × 0.15) = 2.70
```

---

## 5. Recommended Migration Sequence

### Prerequisites: Banking Domain Outputs Required First

Since `customer_profitability.sas` is a downstream consumer of Banking domain outputs, the following Banking programs **must be migrated and validated** before this report can run:

| Priority | Banking Program | Output Dataset | Required By |
|---|---|---|---|
| 1 | `Programs/Banking/account_loading.sas` | `STG_BANK.CUST_ACCOUNTS_DAILY` | Step 1 (Interest Income) |
| 2 | `Programs/Banking/transaction_etl.sas` | `CURATED.DAILY_TRANSACTIONS` | Step 2 (Fee Income) |
| 3 | `Programs/Banking/credit_risk.sas` | `CURATED.RISK_SCORES` | Step 3 (Expected Credit Loss) |

### Migration Plan for customer_profitability.sas

| Phase | Task | Effort | Notes |
|---|---|---|---|
| **Phase 1** | Translate 3 PROC SQL queries to target SQL dialect | S | Standard SQL with SAS-specific `calculated` keyword removal; CASE/WHEN logic is portable |
| **Phase 2** | Translate DATA step MERGE to SQL JOIN or DataFrame merge | M | BY-variable merge with `if a;` (left-join semantics); computed columns for operating cost, total revenue, net profit, ROA, profit tier |
| **Phase 3** | Translate 2 PROC MEANS aggregations to GROUP BY queries | S | `CLASS` → `GROUP BY`; output statistics (N, SUM, MEAN) map directly to SQL aggregates |
| **Phase 4** | Replace `%export_xlsx` with target-platform export | S | Python: `openpyxl` / `pandas.to_excel`; Spark: write to Delta then export; Databricks: notebook widget or DBFS export |
| **Phase 5** | Replace `%parmv` / `%nobs` with target equivalents | S | Parameter validation → function args + assertions; row counts → `df.count()` or `SELECT COUNT(*)` |
| **Phase 6** | Implement scheduling (replace Control-M) | S | Target scheduler (Airflow DAG, Databricks Workflow, ADF pipeline) — depends on platform choice |
| **Phase 7** | Validation — P&L number reconciliation | M | Run SAS and target in parallel for ≥2 months; reconcile `CUSTOMER_PNL` row counts and financial totals (net profit, total revenue) to within tolerance |

### Estimated Total Effort

| Size | Definition | Estimate |
|---|---|---|
| **M (Medium)** | 3–5 developer-days | Straightforward SQL translation with moderate validation effort. Most complexity is in the reconciliation phase, not the code conversion. |

---

## 6. Risk Factors & Notes

### High Risk

| # | Risk | Impact | Mitigation |
|---|---|---|---|
| 1 | **Cross-domain data dependency** — All 3 inputs come from Banking domain pipelines. If Banking migration is delayed or produces schema changes, this report breaks. | Report cannot run until Banking pipelines are stable in the target environment. | Establish a data contract (schema + SLA) for each upstream table before beginning Reports migration. Run Banking pipelines end-to-end in target before starting this work. |
| 2 | **P&L calculation accuracy** — Financial reporting numbers (net profit, ROA) must match exactly between SAS and target. Floating-point differences in interest rate calculations or rounding could produce discrepancies. | Regulatory/audit risk if numbers diverge. | Use `DECIMAL` types (not `FLOAT`/`DOUBLE`) in target platform for monetary columns. Build automated reconciliation comparing SAS output to target output for every reporting period during parallel-run. |

### Medium Risk

| # | Risk | Impact | Mitigation |
|---|---|---|---|
| 3 | **SAS `calculated` keyword** — PROC SQL uses `calculated` to reference computed columns within the same SELECT. This is SAS-specific and has no direct SQL equivalent in most platforms. | Queries must be restructured using CTEs or subqueries. | Refactor each `calculated` reference into a CTE or inline view. |
| 4 | **DATA step MERGE semantics** — SAS MERGE with `if a;` has subtle behavior differences from SQL LEFT JOIN when there are duplicate BY-values or when datasets have different sort orders. | Potential row count differences if not translated carefully. | Verify that `CUSTOMER_ID` is unique in each WORK table before merge. Use explicit SQL LEFT JOIN with matching ON clause. |
| 5 | **PROC MEANS output options** — The `sum=` (unnamed) and `mean(NET_PROFIT)=AVG_PROFIT_PER_CUSTOMER` syntax has specific output variable naming rules in SAS. | Column names in target output may differ. | Map each output statistic explicitly in the target GROUP BY query. |
| 6 | **`%export_xlsx` parameter mismatch** — The invocation uses `file=` and `sheet=` but the macro expects `PATH=` and has no sheet parameter (see Section 3). | XLSX export may not be functioning correctly in production, or the production macro differs from this codebase. | Verify actual production behavior before assuming XLSX export works. Implement fresh in target using native export libraries. |

### Low Risk

| # | Risk | Impact | Mitigation |
|---|---|---|---|
| 7 | **Hardcoded account type codes** — Lending types (`MTG`, `AUTO`, `PERS`, `CC`, `LOC`, `HELC`) and deposit types (`CHK`, `SAV`, `MMA`, `CD`, `IRA`) are hardcoded in the SQL CASE expression. | New account types added in the future would be silently excluded from interest income calculation. | Migrate to a reference table-driven approach in the target platform. |
| 8 | **Fixed operating cost allocation** — `$15/account/month` is hardcoded (line 109). | Business rule change requires code change. | Externalize to a configuration table or parameter. |
| 9 | **Format catalog dependency** — `autoexec.sas` sets `fmtsearch=(BANKING INSURANCE COMMON WORK LIBRARY)`. While this program uses only standard SAS formats (`dollar18.2`, `percent8.4`), downstream consumers of REPORTS output may rely on banking/insurance format catalogs for display. | Target platform must replicate relevant format lookups for any dashboards or reports consuming these outputs. | Catalog relevant formats from `Formats/banking_formats.sas` (e.g., `$CUSTSEG`, `$REGION`, `$ACCTTYPE`) and implement as lookup tables or CASE expressions in the target. |
| 10 | **ORA_DW.COST_OF_FUNDS dead reference** — Listed in program header but unused in code. | No immediate impact, but may indicate missing business logic. | Confirm with stakeholders whether cost-of-funds should be incorporated into the P&L calculation. |
| 11 | **Control-M scheduling** — Program runs monthly on the 10th business day (`BANK_MONTHLY_03`). | Scheduling must be recreated in the target orchestrator. | Define equivalent schedule in Airflow/Databricks Workflows with dependency on upstream Banking pipeline completion. |

### SAS-Specific Features Requiring Translation

| SAS Feature | Location | Target Platform Equivalent |
|---|---|---|
| `PROC SQL` with `calculated` keyword | Steps 1, 2, 3 | CTE or subquery |
| `DATA step MERGE ... BY` with `if a;` | Step 4 | SQL LEFT JOIN or DataFrame merge |
| `PROC MEANS` with `CLASS` / `OUTPUT OUT=` | Step 5 | SQL GROUP BY with aggregate functions |
| `PROC DATASETS DELETE` | Cleanup | `DROP TABLE` or garbage collection |
| `%sysfunc(inputn(...))` / `%sysfunc(intnx(...))` | Date calculation | Platform date functions |
| `format dollar18.2` / `format percent8.4` | Throughout | Number formatting in presentation layer |
| `label=` dataset option | Step 4, line 100 | Table/column comments or metadata |
| `%include` for macro loading | Lines 15–17 | Import/module system in target language |

---

## Appendix A: Library Reference (from Config/autoexec.sas)

| Library | Path / Connection | Access | Used By This Program |
|---|---|---|---|
| `STG_BANK` | `/data/sas/staging/banking` | Read/Write | Yes (input) |
| `CURATED` | `/data/sas/curated` | Read/Write | Yes (input) |
| `REPORTS` | `/data/sas/reports` | Read/Write | Yes (output) |
| `BANKING` | `/data/sas/formats/banking` | Read | Indirectly (fmtsearch) |
| `INSURANCE` | `/data/sas/formats/insurance` | Read | Indirectly (fmtsearch) |
| `ORA_DW` | Oracle `FINPROD.DW_BANKING` | Read-only | Referenced in header only |
| `TERA_DW` | Teradata `ANALYTICS` | Read-only | Not used |
| `ARCHIVE` | `/data/sas/archive` | Read/Write | Not used |

## Appendix B: Related Migration Resources

| Resource | Description |
|---|---|
| `uc-data-migration-sas-to-databricks` repo | dbt/Databricks target architecture with staging, intermediate, and mart layers — provides migration patterns for SAS → SQL translation |
| `uc-data-migration-sas-to-snowflake` repo | Snowflake validation toolkit for SAS migration parity checking |
| `BatchJobs/run_daily_banking.sas` | Master orchestrator that schedules Banking domain pipelines — defines execution order and dependencies |
