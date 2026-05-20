# SAS Migration Assessment — `ts-sas-legacy-analytics`

> **Assessment Date:** 2026-05-20
> **Source Codebase:** `Cognition-Partner-Workshops/ts-sas-legacy-analytics`
> **Target Platform:** dbt on Databricks (see `uc-data-migration-sas-to-databricks`)
> **SAS Version:** SAS 9.4 M7 on Linux (RHEL 7)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Artifact Inventory](#2-artifact-inventory)
3. [Environment Configuration (autoexec.sas)](#3-environment-configuration)
4. [Program Analysis — Banking](#4-program-analysis--banking)
5. [Program Analysis — Insurance](#5-program-analysis--insurance)
6. [Program Analysis — Reports](#6-program-analysis--reports)
7. [Batch Orchestration & Execution Dependency Chain](#7-batch-orchestration--execution-dependency-chain)
8. [Custom Format Definitions (Formats/)](#8-custom-format-definitions)
9. [Macro Library Analysis (Macro/)](#9-macro-library-analysis)
10. [Production Data Volumes & Execution Times (Logs/)](#10-production-data-volumes--execution-times)
11. [Data Lineage Diagram](#11-data-lineage-diagram)
12. [Macro Dependency Graph](#12-macro-dependency-graph)
13. [Dataset Usage Matrix](#13-dataset-usage-matrix)
14. [Complexity Scores](#14-complexity-scores)
15. [Risk Areas](#15-risk-areas)
16. [Recommended Migration Sequence](#16-recommended-migration-sequence)
17. [dbt Target Mapping Summary](#17-dbt-target-mapping-summary)
18. [Appendix A — Full Macro Library Inventory](#appendix-a--full-macro-library-inventory)

---

## 1. Executive Summary

This SAS estate comprises **7 application programs**, **2 batch orchestrators**, **2 format catalogs**, and **92 utility macros** (~25,000 lines of macro code) supporting banking and insurance analytics for an enterprise financial institution. The codebase handles:

- **Daily transaction ETL** processing ~2.3M records/day (6:48 wall-clock)
- **Customer account snapshots** of ~847K accounts (2:55 wall-clock)
- **Credit risk scoring** with PD/LGD/EAD models (Basel III)
- **Monthly regulatory reporting** (RWA, capital adequacy, delinquency aging)
- **Insurance claims intake** with auto-adjudication and fraud screening
- **Policy book valuation** with loss ratios and IBNR reserves
- **Customer profitability P&L** with segment/branch rollups

### External Dependencies

| System | LIBNAME | Purpose |
|--------|---------|---------|
| Oracle DW | `ORA_DW` | Customer demographics, loans, bureau scores, collateral, payment history, cost of funds |
| Teradata | `TERA_DW` | Actuarial tables, fraud indicators |
| File Feeds | `RAW_BANK`, `RAW_INS` | Daily transaction & claims flat files |
| Control-M | — | Job scheduling and dependency management |
| SMTP | — | Operational alerts and batch notifications |

### Overall Complexity

| Metric | Value |
|--------|-------|
| Total SAS programs | 7 application + 2 orchestrators |
| Total macro library files | 92 (.sas) + 1 (.txt) |
| Total lines (application programs) | ~1,571 |
| Total lines (macro library) | ~24,979 |
| PROC FORMAT definitions | 14 formats across 2 catalogs |
| Distinct LIBNAME references | 14 |
| External DB connections | 2 (Oracle, Teradata) |
| Unique datasets read | 20+ |
| Unique datasets written | 18+ |

---

## 2. Artifact Inventory

### Application Programs

| File | Domain | Lines | Schedule |
|------|--------|-------|----------|
| `Programs/Banking/load_customer_accounts.sas` | Banking | 216 | Daily 06:00 (BANK_DAILY_01) |
| `Programs/Banking/daily_transaction_processing.sas` | Banking | 246 | Daily 07:30 (BANK_DAILY_02) |
| `Programs/Banking/credit_risk_scoring.sas` | Banking | 270 | Weekly Sun 02:00 (BANK_WEEKLY_01) |
| `Programs/Banking/monthly_regulatory_reporting.sas` | Banking | 199 | Monthly 3rd bus day (BANK_MONTHLY_01) |
| `Programs/Insurance/claims_processing.sas` | Insurance | 238 | Daily 08:00 (INS_DAILY_01) |
| `Programs/Insurance/policy_valuation.sas` | Insurance | 206 | Monthly 5th bus day (INS_MONTHLY_01) |
| `Programs/Reports/customer_profitability.sas` | Reports | 176 | Monthly 10th bus day (BANK_MONTHLY_03) |

### Batch Orchestrators

| File | Lines | Schedule |
|------|-------|----------|
| `BatchJobs/run_daily_banking.sas` | 161 | Daily 05:45 (BANK_MASTER) |
| `BatchJobs/run_daily_insurance.sas` | 133 | Daily 07:00 (INS_MASTER) |

### Format Catalogs

| File | Lines | Formats Defined |
|------|-------|-----------------|
| `Formats/banking_formats.sas` | 131 | 8 ($ACCTTYPE, $ACCTSTAT, RISKRATE, $TXNCAT, DELQBKT, BALRANGE, $REGION, $CUSTSEG, $LNPURP) |
| `Formats/insurance_formats.sas` | 85 | 5 ($POLTYPE, $CLMSTAT, $RISKCAT, $COVTYPE, LOSSRANGE) |

### Support Files

| File | Purpose |
|------|---------|
| `Config/autoexec.sas` | Library assignments, global macro vars, DB connections |
| `Macro/` (92 files) | Utility macro library (~24,979 lines) |
| `Logs/` (2 files) | Production execution logs (2024-01-15) |
| `Programs/Parent-Child-Index.sas` | Standalone hierarchical dimension example |

---

## 3. Environment Configuration

**File:** `Config/autoexec.sas` (118 lines)

### Library Assignments (14 total)

| LIBNAME | Path / Connection | Access | Purpose |
|---------|-------------------|--------|---------|
| `RAW` | `/data/sas/raw` | readonly | Raw data landing zone |
| `RAW_BANK` | `/data/sas/raw/banking` | readonly | Raw banking feeds |
| `RAW_INS` | `/data/sas/raw/insurance` | readonly | Raw insurance feeds |
| `STAGING` | `/data/sas/staging` | read/write | Intermediate processing |
| `STG_BANK` | `/data/sas/staging/banking` | read/write | Banking staging |
| `STG_INS` | `/data/sas/staging/insurance` | read/write | Insurance staging |
| `CURATED` | `/data/sas/curated` | read/write | Final analytical layer |
| `REPORTS` | `/data/sas/reports` | read/write | Reporting outputs |
| `ARCHIVE` | `/data/sas/archive` | read/write | Historical batch logs |
| `BANKING` | `/data/sas/formats/banking` | read/write | Banking format catalog |
| `INSURANCE` | `/data/sas/formats/insurance` | read/write | Insurance format catalog |
| `COMMON` | `/data/sas/formats/common` | read/write | Shared format catalog |
| `ORA_DW` | Oracle `FINPROD.DW_BANKING` | readonly | Oracle data warehouse |
| `TERA_DW` | Teradata `tdprod.internal.corp/ANALYTICS` | readonly | Teradata analytics |

### Database Connections

| Connection | Type | Server | Schema | Auth | Options |
|------------|------|--------|--------|------|---------|
| `ORA_DW` | Oracle (SAS/ACCESS) | `FINPROD` | `DW_BANKING` | `&ora_uid / &ora_pwd` | `readbuff=5000, insertbuff=2000` |
| `TERA_DW` | Teradata (SAS/ACCESS) | `tdprod.internal.corp` | `ANALYTICS` | `&tera_uid / &tera_pwd` | `bulkload=yes` |

### Global Macro Variables

| Variable | Value/Expression | Purpose |
|----------|-----------------|---------|
| `&ENVIRONMENT` | `PROD` | Environment identifier |
| `&BASE_PATH` | `/data/sas` | Base data directory |
| `&LOG_PATH` | `/data/sas/logs` | Log file location |
| `&REPORT_PATH` | `/data/sas/reports/output` | Report output location |
| `&ARCHIVE_PATH` | `/data/sas/archive` | Archive location |
| `&CURR_DT` | `%sysfunc(today(), date9.)` | Current date |
| `&CURR_YM` | `%sysfunc(today(), yymmn6.)` | Current year-month |
| `&PREV_YM` | Previous month (yymmn6.) | Prior reporting period |
| `&FY_START` | Fiscal year start | Fiscal year boundary |
| `&EMAIL_DL` | `sas-ops@corp.internal` | Operations distribution list |
| `&EMAIL_ONCALL` | `oncall-data@corp.internal` | On-call alert recipient |
| `&MAX_OBS_WARN` | `10000000` | Row count warning threshold |
| `&ABORT_ON_ERR` | `Y` | Halt batch on error flag |

### System Options

```
mautosource sasautos=(...) mrecall mlogic mprint symbolgen
compress=yes fmtsearch=(BANKING INSURANCE COMMON WORK LIBRARY)
validvarname=v7 nofmterr yearcutoff=1920 obs=MAX msglevel=i noerrorabend
```

### Migration Impact

- 14 LIBNAMEs → Unity Catalog schemas + dbt sources
- 2 external DB connections → Databricks external tables or Lakehouse Federation
- Credential management (`&ora_uid`, `&ora_pwd`, `&tera_uid`, `&tera_pwd`) → Databricks Secrets
- Format search path (`fmtsearch=`) → dbt macro availability (already global)
- Autocall macro paths → dbt `macro-paths` in `dbt_project.yml`

---

## 4. Program Analysis — Banking

### 4.1 load_customer_accounts.sas

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Daily customer account snapshot from Oracle DW |
| **Lines** | 216 |
| **Schedule** | Daily 06:00 — Control-M `BANK_DAILY_01` |

**Data Sources (Reads):**
| Dataset | Library | Source Type |
|---------|---------|-------------|
| `CUST_ACCOUNTS` | `ORA_DW` | Oracle DW table |
| `CUST_DEMOGRAPHICS` | `ORA_DW` | Oracle DW table |
| `DAILY_RATES` | `RAW_BANK` | Flat file (referenced in header) |

**Outputs (Writes):**
| Dataset | Library | Type |
|---------|---------|------|
| `CUST_ACCOUNTS_DAILY` | `STG_BANK` | Staging table (daily snapshot) |
| `ACCT_EXCEPTIONS` | `STG_BANK` | Exception/DQ report |

**Macro Dependencies:**
| Macro | Source | Usage |
|-------|--------|-------|
| `%parmv` | `Macro/parmv.sas` | Parameter validation |
| `%nobs` | `Macro/nobs.sas` | Row count checks |
| `%lock` | `Macro/lock.sas` | Dataset locking (included but not invoked) |
| `%sendmail` | `Macro/sendmail.sas` | Exception email alerts (>100 exceptions) |

**SAS Constructs:**
- `PROC SQL` with inner join (Oracle pass-through implied)
- `DATA` step with conditional business logic (IF/THEN/ELSE)
- Custom format application (`$ACCTTYPE.`, `$ACCTSTAT.`, `RISKRATE.`, `$CUSTSEG.`, `$REGION.`)
- Conditional macro logic (`%if &region ne ALL`)
- Derived metrics: `ACCT_AGE_MONTHS`, `DAYS_INACTIVE`, `UTILIZATION_PCT`, `DORMANCY_FLAG`, `HIGH_BALANCE_FLAG`
- Exception routing: negative balance, high utilization, missing risk rating
- `PROC MEANS` with `CLASS` for summary statistics
- `PROC DATASETS` for WORK cleanup

**Complexity:** ⬛⬛⬛⬜⬜ **MEDIUM** — Standard ETL pattern with business rules, straightforward SQL-to-SQL migration.

---

### 4.2 daily_transaction_processing.sas

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Transaction ETL: validate, classify, running balances, anomaly detection |
| **Lines** | 246 |
| **Schedule** | Daily 07:30 — Control-M `BANK_DAILY_02` |
| **Depends On** | `load_customer_accounts.sas` (BANK_DAILY_01) |

**Data Sources (Reads):**
| Dataset | Library | Source Type |
|---------|---------|-------------|
| `TXN_FEED_YYYYMMDD` | `RAW_BANK` | Daily flat file (dynamic name) |
| `CUST_ACCOUNTS_DAILY` | `STG_BANK` | Output from load_customer_accounts |
| `DAILY_TRANSACTIONS` | `CURATED` | Historical transactions (90-day lookback) |

**Outputs (Writes):**
| Dataset | Library | Type |
|---------|---------|------|
| `DAILY_TRANSACTIONS` | `CURATED` | Append daily validated transactions |
| `TXN_ANOMALIES` | `CURATED` | Append anomaly records |
| `RUNNING_BALANCES` | `CURATED` | Running balance snapshot |

**Macro Dependencies:**
| Macro | Source | Usage |
|-------|--------|-------|
| `%parmv` | `Macro/parmv.sas` | Parameter validation |
| `%nobs` | `Macro/nobs.sas` | Row count checks |
| `%lock` | `Macro/lock.sas` | Dataset locking (CURATED tables) |

**SAS Constructs:**
- **Dynamic dataset name:** `TXN_FEED_%sysfunc(putn("&txn_date"d, yymmddn8.))` — date-based naming
- `DATA` step validation with multiple reject conditions
- `PROC SQL` join for enrichment
- **`RETAIN` + BY-group processing** for running balance calculation — _key migration pattern (→ window functions)_
- **Z-score anomaly detection** — statistical outlier identification
- `PROC APPEND` with **dataset locking** (`%lock`) — _concurrent access pattern (→ Delta MERGE)_
- `%GOTO` error handling (ABORT/EXIT labels)
- `PROC DATASETS` for WORK cleanup

**Complexity:** ⬛⬛⬛⬛⬜ **HIGH** — RETAIN-based running balance, dynamic dataset naming, Z-score statistics, concurrent locking. Most complex daily program.

---

### 4.3 credit_risk_scoring.sas

| Attribute | Detail |
|-----------|--------|
| **Purpose** | PD/LGD/EAD credit risk model execution |
| **Lines** | 270 |
| **Schedule** | Weekly Sunday 02:00 — Control-M `BANK_WEEKLY_01` |

**Data Sources (Reads):**
| Dataset | Library | Source Type |
|---------|---------|-------------|
| `CUST_ACCOUNTS_DAILY` | `STG_BANK` | Staging (from load_customer_accounts) |
| `BUREAU_SCORES` | `ORA_DW` | Oracle — credit bureau data |
| `PAYMENT_HISTORY` | `ORA_DW` | Oracle — payment behavior |
| `COLLATERAL` | `ORA_DW` | Oracle — collateral values |

**Outputs (Writes):**
| Dataset | Library | Type |
|---------|---------|------|
| `RISK_SCORES` | `CURATED` | Append scored portfolio |
| `RISK_MIGRATION` | `CURATED` | Append rating changes |
| `RISK_SUMMARY` | `REPORTS` | Aggregated risk summary |

**Macro Dependencies:**
| Macro | Source | Usage |
|-------|--------|-------|
| `%parmv` | `Macro/parmv.sas` | Parameter validation |
| `%nobs` | `Macro/nobs.sas` | Row count checks |
| `%lock` | `Macro/lock.sas` | Dataset locking |

**SAS Constructs:**
- `PROC SQL` with **correlated subquery** for latest bureau scores
- 4-table join (accounts + bureau + payment + collateral)
- **WOE (Weight of Evidence) binning** — nested IF/THEN/ELSE chains for 5 risk factors
- **Logistic regression scoring** — `PD = 1 / (1 + exp(-LOG_ODDS))` in DATA step
- **LGD estimation** — secured vs. unsecured logic
- **EAD estimation** — unused credit facility conversion
- **Expected Loss** = PD × LGD × EAD
- **Risk rating assignment** — 7-tier PD-based classification
- **Risk migration matrix** — `PROC SQL` comparing current vs. prior ratings
- `PROC MEANS` for risk summary aggregation
- `PROC APPEND` with locking for curated tables

**Complexity:** ⬛⬛⬛⬛⬛ **VERY HIGH** — Most complex program. Regulatory model with WOE binning, logistic regression, multi-source scoring, and risk migration tracking. Requires careful validation during migration.

---

### 4.4 monthly_regulatory_reporting.sas

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Basel III / Call Report: RWA, capital adequacy, delinquency aging, LLP coverage |
| **Lines** | 199 |
| **Schedule** | Monthly 3rd business day — Control-M `BANK_MONTHLY_01` |

**Data Sources (Reads):**
| Dataset | Library | Source Type |
|---------|---------|-------------|
| `DAILY_TRANSACTIONS` | `CURATED` | Curated transactions |
| `CUST_ACCOUNTS_DAILY` | `STG_BANK` | Staging accounts |
| `LOAN_DETAILS` | `ORA_DW` | Oracle — loan-level detail |
| `COLLATERAL` | `ORA_DW` | Oracle — collateral |

**Outputs (Writes):**
| Dataset | Library | Type |
|---------|---------|------|
| `MONTHLY_RWA` | `REPORTS` | Risk-weighted assets by category |
| `DELINQUENCY_AGING` | `REPORTS` | 30/60/90/120/180+ buckets |
| `LLP_COVERAGE` | `REPORTS` | Loan loss provision coverage |
| `CAPITAL_ADEQUACY` | `REPORTS` | CET1, Tier 1, Total Capital ratios |
| `REG_REPORT_YYYYMM.xlsx` | Filesystem | Excel export for regulators |

**Macro Dependencies:**
| Macro | Source | Usage |
|-------|--------|-------|
| `%parmv` | `Macro/parmv.sas` | Parameter validation |
| `%nobs` | `Macro/nobs.sas` | Row count checks |
| `%export_xlsx` | `Macro/export_xlsx.sas` | Excel output (→ `%export_dbms`) |

**SAS Constructs:**
- `PROC SQL` with `CASE` for Basel III risk weight assignment
- `PROC SQL` with `BETWEEN` for delinquency bucket classification
- `PROC SQL` aggregation for loan loss provision
- **`PROC EXPORT` (via %export_xlsx)** for Excel output — _needs Python/notebook migration_
- `PROC SQL` for capital adequacy ratios (CET1 ≥ 4.5%, Tier1 ≥ 6%, Total ≥ 8%)
- Calculated columns (`calculated` keyword in SAS SQL)

**Complexity:** ⬛⬛⬛⬛⬜ **HIGH** — Regulatory compliance with multiple output tables, Basel III logic, Excel export.

---

## 5. Program Analysis — Insurance

### 5.1 claims_processing.sas

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Claims intake, validation, fraud screening, auto-adjudication |
| **Lines** | 238 |
| **Schedule** | Daily 08:00 — Control-M `INS_DAILY_01` |

**Data Sources (Reads):**
| Dataset | Library | Source Type |
|---------|---------|-------------|
| `CLAIMS_FEED_YYYYMMDD` | `RAW_INS` | Daily flat file (dynamic name) |
| `POLICIES` | `RAW_INS` | Policy master (for hash lookup) |
| `FRAUD_INDICATORS` | `TERA_DW` | Teradata — fraud scoring |

**Outputs (Writes):**
| Dataset | Library | Type |
|---------|---------|------|
| `CLAIMS_REGISTER` | `STG_INS` | Append processed claims |
| `CLAIMS_REVIEW_QUEUE` | `STG_INS` | Append manual review items |
| `FRAUD_ALERTS` | `STG_INS` | Append SIU referrals |

**Macro Dependencies:**
| Macro | Source | Usage |
|-------|--------|-------|
| `%parmv` | `Macro/parmv.sas` | Parameter validation |
| `%nobs` | `Macro/nobs.sas` | Row count checks |
| `%sendmail` | `Macro/sendmail.sas` | SIU fraud alert notifications |

**SAS Constructs:**
- **Hash object (`declare hash`)** — in-memory policy lookup — _key migration pattern (→ broadcast join)_
- Multi-output DATA step (VALID/INVALID routing)
- `PROC SQL` join with Teradata for fraud screening
- **Auto-adjudication rules** — tiered IF/THEN/ELSE approval/denial logic
- Fraud risk categorization (HIGH/MEDIUM/LOW thresholds)
- `PROC APPEND` for claims register, review queue, fraud alerts
- Dynamic dataset name for daily feed
- `%sendmail` for SIU alerts
- `%GOTO` error handling

**Complexity:** ⬛⬛⬛⬛⬛ **VERY HIGH** — Hash object lookup, multi-output routing, fraud integration with Teradata, auto-adjudication business rules. Hash-to-join conversion needs careful validation.

---

### 5.2 policy_valuation.sas

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Monthly policy book valuation, loss ratios, IBNR reserves |
| **Lines** | 206 |
| **Schedule** | Monthly 5th business day — Control-M `INS_MONTHLY_01` |

**Data Sources (Reads):**
| Dataset | Library | Source Type |
|---------|---------|-------------|
| `POLICIES` | `RAW_INS` | Policy master |
| `CLAIMS` | `RAW_INS` | Claims history |
| `PREMIUMS` | `RAW_INS` | Premium collections |
| `ACTUARIAL_TABLES` | `TERA_DW` | Teradata — actuarial data (referenced in header) |

**Outputs (Writes):**
| Dataset | Library | Type |
|---------|---------|------|
| `POLICY_VALUATION` | `STG_INS` | Detailed policy-level valuation |
| `LOSS_RATIO_SUMMARY` | `REPORTS` | LOB-level loss ratio report |
| `RESERVE_ADEQUACY` | `REPORTS` | Reserve adequacy report (header ref) |

**Macro Dependencies:**
| Macro | Source | Usage |
|-------|--------|-------|
| `%parmv` | `Macro/parmv.sas` | Parameter validation |
| `%nobs` | `Macro/nobs.sas` | Row count checks |

**SAS Constructs:**
- `PROC SQL` for in-force policy extraction with earned premium pro-rata calculation
- `PROC SQL` aggregation for 12-month claims experience
- `PROC SQL` for premium collections
- **`MERGE BY`** — 3-way merge (in-force + claims + premiums) — _classic SAS pattern (→ SQL multi-join)_
- Custom format application (`$POLTYPE.`, `$RISKCAT.`)
- **Loss ratio, combined ratio** calculations
- **IBNR estimate** — basic actuarial: `15% of earned premium - paid`
- **Total reserve** = open case reserves + IBNR
- `PROC MEANS` with post-processing DATA step for aggregated loss ratios

**Complexity:** ⬛⬛⬛⬛⬜ **HIGH** — Actuarial calculations, 3-way merge, earned premium pro-rata logic, IBNR estimation.

---

## 6. Program Analysis — Reports

### 6.1 customer_profitability.sas

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Customer-level P&L: interest income, fees, ECL, operating costs |
| **Lines** | 176 |
| **Schedule** | Monthly 10th business day — Control-M `BANK_MONTHLY_03` |

**Data Sources (Reads):**
| Dataset | Library | Source Type |
|---------|---------|-------------|
| `CUST_ACCOUNTS_DAILY` | `STG_BANK` | Staging accounts |
| `DAILY_TRANSACTIONS` | `CURATED` | Curated transactions |
| `RISK_SCORES` | `CURATED` | Credit risk scores |
| `COST_OF_FUNDS` | `ORA_DW` | Oracle — cost of funds (referenced in header) |

**Outputs (Writes):**
| Dataset | Library | Type |
|---------|---------|------|
| `CUSTOMER_PNL` | `REPORTS` | Customer-level P&L |
| `SEGMENT_PROFITABILITY` | `REPORTS` | Segment rollup |
| `BRANCH_PROFITABILITY` | `REPORTS` | Branch rollup |
| `PROFITABILITY_YYYYMM.xlsx` | Filesystem | Excel export |

**Macro Dependencies:**
| Macro | Source | Usage |
|-------|--------|-------|
| `%parmv` | `Macro/parmv.sas` | Parameter validation |
| `%nobs` | `Macro/nobs.sas` | Row count checks |
| `%export_xlsx` | `Macro/export_xlsx.sas` | Excel output |

**SAS Constructs:**
- `PROC SQL` with `CASE` for interest income / deposit cost split
- `PROC SQL` for fee income aggregation
- `PROC SQL` with correlated subquery for latest ECL
- **`MERGE BY`** — 3-way merge (interest + fees + ECL)
- Operating cost allocation ($15/account/month)
- **ROA calculation** (annualized)
- Profitability tier assignment (Highly Profitable / Profitable / Marginal / Unprofitable)
- `PROC MEANS` for segment and branch summaries
- `%export_xlsx` for Excel output

**Complexity:** ⬛⬛⬛⬜⬜ **MEDIUM** — Standard P&L assembly with rollups. Well-structured for SQL migration.

---

## 7. Batch Orchestration & Execution Dependency Chain

### 7.1 Banking Batch — `run_daily_banking.sas`

**Control-M Job:** `BANK_MASTER` — Daily 05:45

```
BANK_MASTER (05:45)
  │
  ├─ Step 1: Load Customer Accounts
  │   Program: load_customer_accounts.sas
  │   Control-M: BANK_DAILY_01 (06:00)
  │   Writes: STG_BANK.CUST_ACCOUNTS_DAILY, STG_BANK.ACCT_EXCEPTIONS
  │
  ├─ Step 2: Daily Transaction Processing   ← depends on Step 1
  │   Program: daily_transaction_processing.sas
  │   Control-M: BANK_DAILY_02 (07:30)
  │   Reads:  STG_BANK.CUST_ACCOUNTS_DAILY (from Step 1)
  │   Writes: CURATED.DAILY_TRANSACTIONS, CURATED.TXN_ANOMALIES,
  │           CURATED.RUNNING_BALANCES
  │
  ├─ Step 3: Credit Risk Scoring            ← depends on Step 1
  │   Program: credit_risk_scoring.sas
  │   Control-M: BANK_WEEKLY_01 (weekly)
  │   Reads:  STG_BANK.CUST_ACCOUNTS_DAILY (from Step 1)
  │   Writes: CURATED.RISK_SCORES, CURATED.RISK_MIGRATION,
  │           REPORTS.RISK_SUMMARY
  │
  └─ Step 4: Monthly Regulatory Reporting   ← depends on Steps 1+2
      Program: monthly_regulatory_reporting.sas
      Control-M: BANK_MONTHLY_01 (monthly)
      Reads:  STG_BANK.CUST_ACCOUNTS_DAILY, CURATED.DAILY_TRANSACTIONS
      Writes: REPORTS.MONTHLY_RWA, REPORTS.DELINQUENCY_AGING,
              REPORTS.LLP_COVERAGE, REPORTS.CAPITAL_ADEQUACY,
              .xlsx file
```

### 7.2 Insurance Batch — `run_daily_insurance.sas`

**Control-M Job:** `INS_MASTER` — Daily 07:00

```
INS_MASTER (07:00)
  │
  ├─ Step 1: Claims Processing
  │   Program: claims_processing.sas
  │   Control-M: INS_DAILY_01 (08:00)
  │   Writes: STG_INS.CLAIMS_REGISTER, STG_INS.CLAIMS_REVIEW_QUEUE,
  │           STG_INS.FRAUD_ALERTS
  │
  └─ Step 2: Policy Valuation               ← depends on Step 1
      Program: policy_valuation.sas
      Control-M: INS_MONTHLY_01 (monthly)
      Writes: STG_INS.POLICY_VALUATION, REPORTS.LOSS_RATIO_SUMMARY,
              REPORTS.RESERVE_ADEQUACY
```

### 7.3 Cross-Batch Dependencies

```
customer_profitability.sas (BANK_MONTHLY_03)
  ├── Reads STG_BANK.CUST_ACCOUNTS_DAILY  ← from Banking Step 1
  ├── Reads CURATED.DAILY_TRANSACTIONS     ← from Banking Step 2
  └── Reads CURATED.RISK_SCORES            ← from Banking Step 3
```

### Orchestrator Features

| Feature | SAS Implementation | dbt/Databricks Target |
|---------|-------------------|----------------------|
| Step sequencing | `%include` via `%run_step` wrapper | dbt `ref()` DAG / Databricks Workflow tasks |
| Error handling | `%SYSCC` check after each `%include` | dbt `on-run-end` hooks / Workflow failure handling |
| Restart from step | `restart_from=` parameter | Databricks Workflow retry from failed task |
| Batch tracking | `WORK.BATCH_CONTROL` → `ARCHIVE.BATCH_HISTORY` | dbt artifacts / Databricks Workflow run history |
| Email notifications | `%sendmail` on failure/completion | Databricks Alerts / PagerDuty / Slack webhook |
| Abort on error | `&ABORT_ON_ERR = Y` → `%let _batch_abort = 1` | Workflow `on_failure` configuration |

---

## 8. Custom Format Definitions

### 8.1 Banking Formats (`Formats/banking_formats.sas`)

| Format Name | Type | Values | Used By | dbt Migration |
|-------------|------|--------|---------|---------------|
| `$ACCTTYPE` | Character | 11 values (CHK, SAV, MMA, CD, IRA, LOC, MTG, AUTO, PERS, CC, HELC) | load_customer_accounts, all banking programs | `macros/format_account_type.sql` ✅ |
| `$ACCTSTAT` | Character | 8 values (A, C, D, F, R, S, P, W) | load_customer_accounts | `macros/format_account_status.sql` ✅ |
| `RISKRATE` | Numeric | 7 tiers (1=Minimal … 7=Loss Expected) | load_customer_accounts, credit_risk_scoring | Seed table or CASE macro needed |
| `$TXNCAT` | Character | 10 types (DEP, WDR, TRF, PMT, FEE, INT, ADJ, REV, CHG, REF) | daily_transaction_processing | `macros/format_txn_category.sql` ✅ |
| `DELQBKT` | Numeric Range | 7 buckets (Current through 180+) | monthly_regulatory_reporting | SQL CASE in model |
| `BALRANGE` | Numeric Range | 8 ranges (Negative through $500K+) | Reporting | SQL CASE in model |
| `$REGION` | Character | 7 values (NE, SE, MW, SW, W, NW, HQ) | load_customer_accounts, all banking programs | Seed table or CASE macro needed |
| `$CUSTSEG` | Character | 6 values (RET, PREM, PB, SMB, COMM, CORP) | load_customer_accounts, credit_risk_scoring, customer_profitability | `macros/format_customer_segment.sql` ✅ |
| `$LNPURP` | Character | 8 values (PURCH, REFI, CASHOUT, CONST, RENO, CONSOL, EDUC, MEDIC) | Regulatory reporting | Seed table or CASE macro needed |

### 8.2 Insurance Formats (`Formats/insurance_formats.sas`)

| Format Name | Type | Values | Used By | dbt Migration |
|-------------|------|--------|---------|---------------|
| `$POLTYPE` | Character | 13 values (WL, TL, UL, VL, AUTO, HOME, RENT, UMBR, HLTH, DNTL, VIS, DISAB, LTCI) | policy_valuation | CASE macro needed |
| `$CLMSTAT` | Character | 12 values (NEW, OPEN, INV, ADJ, PEND, APPR, DENY, PAID, CLOS, REOP, SUSP, LITI) | claims_processing | CASE macro needed |
| `$RISKCAT` | Character | 5 values (STD, PREF, SPRM, SUB, DEC) | policy_valuation | CASE macro needed |
| `$COVTYPE` | Character | 9 values (COMP, COLL, LIAB, PIP, UMBI, UMPD, MED, TOW, RENT) | Claims detail | CASE macro needed |
| `LOSSRANGE` | Numeric Range | 7 ranges (Recovery through $500K+) | Reporting | SQL CASE in model |

**Migration Status:** 4 of 14 formats already migrated to dbt macros in target repo. Remaining 10 need CASE macros or seed tables.

---

## 9. Macro Library Analysis

### 9.1 Directly Used Macros (by application programs)

These 6 macros are explicitly `%include`d or called by the 7 application programs:

| Macro | Called By | Purpose | Migration Priority |
|-------|-----------|---------|-------------------|
| `%parmv` | All 7 programs | Parameter validation (type, required, value list) | **P1** — Replace with dbt `run-time` var validation or Jinja assertion |
| `%nobs` | All 7 programs | Return observation count from dataset | **P1** — `{{ adapter.get_relation(...) }}` or audit macros |
| `%lock` | daily_transaction_processing, credit_risk_scoring | Dataset locking for concurrent access | **P2** — Delta Lake handles concurrency natively |
| `%sendmail` | load_customer_accounts, claims_processing, batch orchestrators | SMTP email notifications | **P2** — Databricks Alerts / webhook integration |
| `%export_xlsx` | monthly_regulatory_reporting, customer_profitability | Excel output via `%export_dbms` | **P2** — Python openpyxl / Databricks notebook |
| `%seplist` | Parent-Child-Index.sas (indirectly via sendmail) | Generate separated lists for SQL | **P3** — Jinja `join` filter |

### 9.2 Macro Dependency Chain (within the 6 used macros)

```
%parmv          (standalone — no dependencies)
  ↑
%nobs           (calls %parmv)
  ↑
%lock           (calls %parmv, %get_data_attr, %handle)
  ↑
%sendmail       (calls %parmv, %seplist)
  ↑
%export_xlsx    (calls %export_dbms → calls %parmv)
```

### 9.3 Utility Macro Categories (full 92-file library)

| Category | Count | Key Macros | Migration Relevance |
|----------|-------|------------|-------------------|
| **Parameter Validation** | 1 | `parmv` | Core — used everywhere |
| **Data Inspection** | 8 | `nobs`, `varexist`, `varlist`, `varlist2`, `get_data_attr`, `get_lib_attr`, `get_dups`, `guess_pk` | Moderate — audit/testing macros |
| **Export/Import** | 12 | `export`, `export_xlsx`, `export_csv`, `export_dlm`, `export_tab`, `export_dbms`, `export_sas`, `export_spss`, `export_stata`, `export_rldx`, `export_saphari`, `excel2sas` | High — file I/O patterns |
| **Dataset Operations** | 8 | `lock`, `compare`, `subset_data`, `transpose`, `hash_define`, `hash_lookup`, `hash_split_dataset`, `check_if_empty` | High — core data patterns |
| **String/Text Utilities** | 10 | `seplist`, `squote`, `splitvar`, `format_text`, `justify`, `align_decimals`, `dedup_string`, `dedup_mstring`, `count_words`, `max_decimals` | Low — string manipulation |
| **Execution Control** | 10 | `RunAll`, `RunAll_ControlTable`, `batch_submit`, `stp_batch_submit`, `loop`, `loop_control`, `execute_macro`, `marker`, `bench`, `kill` | Medium — orchestration |
| **System Utilities** | 10 | `optload`, `optsave`, `optval`, `dump_mvars`, `symget`, `execpath`, `create_directory`, `delete_file`, `dirlist`, `create_datetime_range` | Low — SAS-specific |
| **Format Utilities** | 3 | `fmtexist`, `fmtlist`, `create_format` | Medium — format management |
| **Communication** | 3 | `sendmail`, `handle`, `handle_email.txt` | Medium — alerting |
| **Date/Time** | 3 | `age`, `date_impute`, `time_interval`, `sql_datetime` | Low — date functions |
| **Reporting** | 4 | `pagexofy`, `log2pdf`, `txt2pdf`, `txt2rtf` | Low — output formatting |
| **Security** | 2 | `getpassword`, `queryActiveDirectory` | Medium — auth patterns |
| **SAS-specific** | 7+ | `IsNum`, `IsNumD`, `IsNumM`, `attrib`, `logparse`, `realloc_concat_libs`, `libname_sqlsvr`, `libname_attr_sqlsvr`, `stp_session`, `stp_seplist`, `reduce_pixel`, `randlist`, `get_parameters`, `get_permutations`, `CreateTableOrView`, `@TEMPLATE`, `empty` | Low — SAS platform-specific |

---

## 10. Production Data Volumes & Execution Times

### From Logs (2024-01-15 production run)

#### load_customer_accounts_20240115.log

| Metric | Value |
|--------|-------|
| **Total wall-clock time** | **2:55** (2 min 55 sec) |
| **CPU time** | 2:24 |
| **Records extracted (Oracle)** | 847,293 rows × 22 columns |
| Oracle SQL execution time | 2:14 (real) / 1:48 (CPU) |
| DATA step processing time | 0:32 (real) / 0:28 (CPU) |
| Records loaded to staging | 847,293 |
| Data quality exceptions | 1,247 |
| PROC MEANS summary time | 0:08 |

#### daily_transaction_processing_20240115.log

| Metric | Value |
|--------|-------|
| **Total wall-clock time** | **6:48** (6 min 48 sec) |
| **CPU time** | 5:11 |
| **Feed records ingested** | 2,341,567 rows × 18 columns |
| Validated records | 2,338,912 (99.89% pass rate) |
| Rejected records | 2,655 (0.11%) |
| DATA step validation time | 1:12 (real) / 0:58 (CPU) |
| SQL enrichment join time | 3:45 (real) / 2:56 (CPU) |
| Anomalies detected | 3,421 |
| CURATED.DAILY_TRANSACTIONS size | 67,234,891 cumulative rows |
| PROC APPEND time | 0:45 |
| Running balance DATA step | 0:52 |

### Estimated Monthly/Weekly Volumes

| Dataset | Daily | Monthly (est.) | Annual (est.) |
|---------|-------|----------------|---------------|
| Customer accounts | 847K | ~847K (snapshot) | ~847K (snapshot) |
| Transactions | 2.3M | ~50M | ~600M |
| Transaction anomalies | 3.4K | ~75K | ~900K |
| Cumulative transactions | 67.2M | — | — |

---

## 11. Data Lineage Diagram

```
                    EXTERNAL SOURCES
    ┌──────────────────────────────────────────┐
    │  Oracle DW (ORA_DW)    Teradata (TERA_DW)│
    │  ├─ CUST_ACCOUNTS      ├─ ACTUARIAL_TABLES
    │  ├─ CUST_DEMOGRAPHICS   ├─ FRAUD_INDICATORS
    │  ├─ BUREAU_SCORES       │
    │  ├─ PAYMENT_HISTORY     │
    │  ├─ COLLATERAL          │
    │  ├─ LOAN_DETAILS        │
    │  └─ COST_OF_FUNDS       │
    └──────────────────┬───────────────────────┘
                       │
    RAW LAYER          │     FILE FEEDS
    ┌──────────────────┼─────────────────────┐
    │ RAW_BANK         │    RAW_INS           │
    │ ├─ TXN_FEED_*    │    ├─ CLAIMS_FEED_*  │
    │ └─ DAILY_RATES   │    ├─ POLICIES       │
    │                  │    ├─ CLAIMS          │
    │                  │    └─ PREMIUMS        │
    └──────────────────┼─────────────────────┘
                       │
                       ▼
    STAGING LAYER ═════════════════════════════
    ┌──────────────────┬─────────────────────┐
    │ STG_BANK         │    STG_INS           │
    │ ├─ CUST_ACCOUNTS │    ├─ CLAIMS_REGISTER│
    │ │  _DAILY ◄──────┤    ├─ CLAIMS_REVIEW  │
    │ └─ ACCT_         │    │  _QUEUE          │
    │    EXCEPTIONS    │    ├─ FRAUD_ALERTS    │
    │        ▲         │    └─ POLICY_VALUATION│
    │        │         │           ▲           │
    │   load_customer  │    claims_processing  │
    │   _accounts      │    policy_valuation   │
    └──────────────────┼─────────────────────┘
                       │
                       ▼
    CURATED LAYER ═════════════════════════════
    ┌──────────────────────────────────────────┐
    │ CURATED                                  │
    │ ├─ DAILY_TRANSACTIONS ◄── daily_txn_proc │
    │ ├─ TXN_ANOMALIES      ◄── daily_txn_proc │
    │ ├─ RUNNING_BALANCES    ◄── daily_txn_proc │
    │ ├─ RISK_SCORES         ◄── credit_risk    │
    │ └─ RISK_MIGRATION      ◄── credit_risk    │
    └──────────────────┬───────────────────────┘
                       │
                       ▼
    REPORTING LAYER ═══════════════════════════
    ┌──────────────────────────────────────────┐
    │ REPORTS                                  │
    │ ├─ RISK_SUMMARY        ◄── credit_risk   │
    │ ├─ MONTHLY_RWA         ◄── regulatory_rpt│
    │ ├─ DELINQUENCY_AGING   ◄── regulatory_rpt│
    │ ├─ LLP_COVERAGE        ◄── regulatory_rpt│
    │ ├─ CAPITAL_ADEQUACY    ◄── regulatory_rpt│
    │ ├─ LOSS_RATIO_SUMMARY  ◄── policy_val    │
    │ ├─ RESERVE_ADEQUACY    ◄── policy_val    │
    │ ├─ CUSTOMER_PNL        ◄── cust_profit   │
    │ ├─ SEGMENT_PROFITAB.   ◄── cust_profit   │
    │ └─ BRANCH_PROFITAB.    ◄── cust_profit   │
    └──────────────────┬───────────────────────┘
                       │
                       ▼
    ARCHIVE / FILE OUTPUT ════════════════════
    ├─ ARCHIVE.BATCH_HISTORY
    ├─ REG_REPORT_YYYYMM.xlsx
    └─ PROFITABILITY_YYYYMM.xlsx
```

---

## 12. Macro Dependency Graph

### Application-Level Macro Usage

```
run_daily_banking.sas
  ├── %sendmail ─────────────── → %parmv, %seplist
  └── %include (4 programs):
      │
      ├── load_customer_accounts.sas
      │   ├── %parmv
      │   ├── %nobs ──────────── → %parmv
      │   ├── %lock ──────────── → %parmv, %get_data_attr, %handle
      │   └── %sendmail ──────── → %parmv, %seplist
      │
      ├── daily_transaction_processing.sas
      │   ├── %parmv
      │   ├── %nobs ──────────── → %parmv
      │   └── %lock ──────────── → %parmv, %get_data_attr, %handle
      │
      ├── credit_risk_scoring.sas
      │   ├── %parmv
      │   ├── %nobs ──────────── → %parmv
      │   └── %lock ──────────── → %parmv, %get_data_attr, %handle
      │
      └── monthly_regulatory_reporting.sas
          ├── %parmv
          ├── %nobs ──────────── → %parmv
          └── %export_xlsx ───── → %export_dbms → %parmv

run_daily_insurance.sas
  ├── %sendmail ─────────────── → %parmv, %seplist
  └── %include (2 programs):
      │
      ├── claims_processing.sas
      │   ├── %parmv
      │   ├── %nobs ──────────── → %parmv
      │   └── %sendmail ──────── → %parmv, %seplist
      │
      └── policy_valuation.sas
          ├── %parmv
          └── %nobs ──────────── → %parmv

customer_profitability.sas
  ├── %parmv
  ├── %nobs ──────────────────── → %parmv
  └── %export_xlsx ───────────── → %export_dbms → %parmv
```

### Unique Macro Call Count

| Macro | Direct Callers | Transitive Callers |
|-------|---------------|-------------------|
| `%parmv` | 7 programs + 5 macros | All 9 programs |
| `%nobs` | 7 programs | 7 programs |
| `%lock` | 3 programs | 3 programs |
| `%sendmail` | 4 programs | 4 programs |
| `%export_xlsx` | 2 programs | 2 programs |
| `%export_dbms` | 1 macro (export_xlsx) | 2 programs |
| `%seplist` | 1 macro (sendmail) | 4 programs |
| `%get_data_attr` | 1 macro (lock) | 3 programs |
| `%handle` | 1 macro (lock) | 3 programs |

---

## 13. Dataset Usage Matrix

### Read Matrix (Programs × Source Datasets)

| Dataset | load_cust | daily_txn | credit_risk | reg_report | claims_proc | policy_val | cust_profit |
|---------|:---------:|:---------:|:-----------:|:----------:|:-----------:|:----------:|:-----------:|
| ORA_DW.CUST_ACCOUNTS | R | | | | | | |
| ORA_DW.CUST_DEMOGRAPHICS | R | | | | | | |
| ORA_DW.BUREAU_SCORES | | | R | | | | |
| ORA_DW.PAYMENT_HISTORY | | | R | | | | |
| ORA_DW.COLLATERAL | | | R | R | | | |
| ORA_DW.LOAN_DETAILS | | | | R | | | |
| ORA_DW.COST_OF_FUNDS | | | | | | | R* |
| RAW_BANK.TXN_FEED_* | | R | | | | | |
| RAW_BANK.DAILY_RATES | R* | | | | | | |
| RAW_INS.CLAIMS_FEED_* | | | | | R | | |
| RAW_INS.POLICIES | | | | | R | R | |
| RAW_INS.CLAIMS | | | | | | R | |
| RAW_INS.PREMIUMS | | | | | | R | |
| TERA_DW.FRAUD_INDICATORS | | | | | R | | |
| TERA_DW.ACTUARIAL_TABLES | | | | | | R* | |
| STG_BANK.CUST_ACCOUNTS_DAILY | | R | R | R | | | R |
| CURATED.DAILY_TRANSACTIONS | | R | | R | | | R |
| CURATED.RISK_SCORES | | | | | | | R |

_R = Read, R* = Referenced in header but not directly in code body_

### Write Matrix (Programs × Output Datasets)

| Dataset | load_cust | daily_txn | credit_risk | reg_report | claims_proc | policy_val | cust_profit |
|---------|:---------:|:---------:|:-----------:|:----------:|:-----------:|:----------:|:-----------:|
| STG_BANK.CUST_ACCOUNTS_DAILY | W | | | | | | |
| STG_BANK.ACCT_EXCEPTIONS | W | | | | | | |
| CURATED.DAILY_TRANSACTIONS | | W | | | | | |
| CURATED.TXN_ANOMALIES | | W | | | | | |
| CURATED.RUNNING_BALANCES | | W | | | | | |
| CURATED.RISK_SCORES | | | W | | | | |
| CURATED.RISK_MIGRATION | | | W | | | | |
| REPORTS.RISK_SUMMARY | | | W | | | | |
| REPORTS.MONTHLY_RWA | | | | W | | | |
| REPORTS.DELINQUENCY_AGING | | | | W | | | |
| REPORTS.LLP_COVERAGE | | | | W | | | |
| REPORTS.CAPITAL_ADEQUACY | | | | W | | | |
| STG_INS.CLAIMS_REGISTER | | | | | W | | |
| STG_INS.CLAIMS_REVIEW_QUEUE | | | | | W | | |
| STG_INS.FRAUD_ALERTS | | | | | W | | |
| STG_INS.POLICY_VALUATION | | | | | | W | |
| REPORTS.LOSS_RATIO_SUMMARY | | | | | | W | |
| REPORTS.CUSTOMER_PNL | | | | | | | W |
| REPORTS.SEGMENT_PROFITABILITY | | | | | | | W |
| REPORTS.BRANCH_PROFITABILITY | | | | | | | W |
| .xlsx file exports | | | | W | | | W |
| ARCHIVE.BATCH_HISTORY | orchestrators | orchestrators | | | | | |

---

## 14. Complexity Scores

| Program | SAS Constructs | External Deps | Business Logic | Data Volume | Regulatory | **Overall** |
|---------|:-:|:-:|:-:|:-:|:-:|:-:|
| `load_customer_accounts.sas` | 3 | 3 | 3 | 3 | 1 | **⬛⬛⬛⬜⬜ MEDIUM** |
| `daily_transaction_processing.sas` | 4 | 2 | 4 | 5 | 1 | **⬛⬛⬛⬛⬜ HIGH** |
| `credit_risk_scoring.sas` | 5 | 4 | 5 | 3 | 5 | **⬛⬛⬛⬛⬛ VERY HIGH** |
| `monthly_regulatory_reporting.sas` | 3 | 3 | 4 | 3 | 5 | **⬛⬛⬛⬛⬜ HIGH** |
| `claims_processing.sas` | 5 | 3 | 5 | 3 | 3 | **⬛⬛⬛⬛⬛ VERY HIGH** |
| `policy_valuation.sas` | 4 | 3 | 4 | 3 | 4 | **⬛⬛⬛⬛⬜ HIGH** |
| `customer_profitability.sas` | 3 | 2 | 3 | 3 | 2 | **⬛⬛⬛⬜⬜ MEDIUM** |

### Scoring Criteria (1-5)

- **SAS Constructs:** 1=basic SQL/DATA, 3=PROC MEANS/FORMAT/MERGE, 5=Hash objects/RETAIN/WOE
- **External Deps:** 1=file-based only, 3=one DB, 5=multi-DB + external services
- **Business Logic:** 1=simple transforms, 3=derived metrics, 5=regulatory models/scoring
- **Data Volume:** 1=<10K rows, 3=100K-1M, 5=>1M daily
- **Regulatory:** 1=none, 3=audit trail, 5=Basel III/actuarial compliance

---

## 15. Risk Areas

### HIGH Risk

| # | Risk | Affected Programs | Mitigation |
|---|------|-------------------|------------|
| 1 | **WOE scorecard model fidelity** | `credit_risk_scoring.sas` | Requires numeric parity testing (PD values to 4 decimal places). Build a validation harness comparing SAS vs. dbt output for a frozen test portfolio. |
| 2 | **RETAIN/running balance semantics** | `daily_transaction_processing.sas` | Window function `SUM() OVER (ROWS UNBOUNDED PRECEDING)` must match SAS BY-group RETAIN exactly. Test with known multi-transaction accounts. |
| 3 | **Hash object → broadcast join parity** | `claims_processing.sas` | SAS hash returns `rc≠0` for misses; SQL LEFT JOIN returns NULL. Verify exception routing produces identical VALID/INVALID splits. |
| 4 | **Regulatory report accuracy** | `monthly_regulatory_reporting.sas` | Capital adequacy ratios, RWA calculations, and delinquency aging must match regulatory filing standards. Parallel-run SAS and dbt outputs for ≥2 monthly cycles. |

### MEDIUM Risk

| # | Risk | Affected Programs | Mitigation |
|---|------|-------------------|------------|
| 5 | **Dynamic dataset names** | `daily_transaction_processing`, `claims_processing` | `TXN_FEED_YYYYMMDD` / `CLAIMS_FEED_YYYYMMDD` patterns need Jinja date logic or Databricks Auto Loader. |
| 6 | **SAS date literal semantics** | All programs | `"&run_date"d` date constant handling — ensure date parsing in SQL matches SAS DATE9. format. |
| 7 | **PROC APPEND + locking** | `daily_transaction_processing`, `credit_risk_scoring` | Delta Lake MERGE/INSERT replaces PROC APPEND + %lock. Concurrent write semantics differ — test under load. |
| 8 | **Excel export** | `monthly_regulatory_reporting`, `customer_profitability` | `%export_xlsx` → Python openpyxl or Databricks notebook. Multi-sheet workbooks need explicit handling. |
| 9 | **MERGE BY (3-way)** | `policy_valuation`, `customer_profitability` | SAS MERGE BY has implicit outer-join semantics. Ensure dbt JOIN type matches (IN= flags simulate inner join). |
| 10 | **Email/SMTP integration** | Orchestrators, `claims_processing`, `load_customer_accounts` | `%sendmail` → Databricks Alerts / webhook. Maintain alert routing for SIU, on-call, and distribution lists. |

### LOW Risk

| # | Risk | Affected Programs | Mitigation |
|---|------|-------------------|------------|
| 11 | **Custom format migration** | All programs | 4/14 already done in dbt. Remaining 10 are simple CASE mappings. |
| 12 | **PROC MEANS → GROUP BY** | Multiple | Direct translation with `SUM()`, `AVG()`, `COUNT()`. Minor: SAS `_TYPE_`/`_FREQ_` columns dropped. |
| 13 | **Macro variable resolution** | All programs | `&var` → dbt `var()` / `env_var()` / Jinja `{{ }}`. Well-documented mapping. |

---

## 16. Recommended Migration Sequence

### Wave 1 — Foundation (Weeks 1-2)

**Goal:** Establish infrastructure and migrate lowest-risk, highest-dependency programs.

| Order | Program | Rationale | dbt Target | Status |
|-------|---------|-----------|------------|--------|
| 1.1 | `Config/autoexec.sas` | Foundation — all programs depend on this | `dbt_project.yml` sources + profiles | Partially done |
| 1.2 | `Formats/banking_formats.sas` | Required by all banking programs | dbt macros (`format_*.sql`) | 4/9 done |
| 1.3 | `Formats/insurance_formats.sas` | Required by insurance programs | dbt macros | 0/5 done |
| 1.4 | `load_customer_accounts.sas` | Foundation — most programs read its output | `stg_cust_accounts` → `int_account_metrics` | ✅ Exists |

### Wave 2 — Core ETL (Weeks 3-4)

| Order | Program | Rationale | dbt Target | Status |
|-------|---------|-----------|------------|--------|
| 2.1 | `daily_transaction_processing.sas` | Second in dependency chain; high volume | `stg_daily_transactions` → `mart_daily_transactions` | ✅ Exists |
| 2.2 | `claims_processing.sas` | Independent of banking; tests hash→join | `stg_claims` → `int_claims_adjudication` | Planned |

### Wave 3 — Analytics & Scoring (Weeks 5-6)

| Order | Program | Rationale | dbt Target | Status |
|-------|---------|-----------|------------|--------|
| 3.1 | `credit_risk_scoring.sas` | Highest complexity; needs parallel-run validation | `mart_risk_scores` | ✅ Exists |
| 3.2 | `policy_valuation.sas` | Actuarial logic; depends on claims | `int_policy_valuation` → `mart_loss_ratios` | Planned |

### Wave 4 — Reporting & Regulatory (Weeks 7-8)

| Order | Program | Rationale | dbt Target | Status |
|-------|---------|-----------|------------|--------|
| 4.1 | `monthly_regulatory_reporting.sas` | Depends on accounts + transactions + loan details | `mart_regulatory_rwa` + `mart_delinquency_aging` | Planned |
| 4.2 | `customer_profitability.sas` | Depends on accounts + transactions + risk scores | `mart_customer_pnl` | Planned |

### Wave 5 — Orchestration & Cutover (Weeks 9-10)

| Order | Component | Rationale |
|-------|-----------|-----------|
| 5.1 | Batch orchestrators → Databricks Workflows | Replace `%run_step` chain with Workflow DAG |
| 5.2 | Email notifications → Databricks Alerts | Replace `%sendmail` with webhook/alert integration |
| 5.3 | Parallel-run validation | Run SAS and dbt side-by-side for ≥1 full monthly cycle |
| 5.4 | Production cutover | Switch Control-M triggers from SAS to Databricks Workflows |

---

## 17. dbt Target Mapping Summary

### Current State in `uc-data-migration-sas-to-databricks`

| Layer | Models Implemented | Source Program |
|-------|-------------------|----------------|
| **Staging** | `stg_cust_accounts.sql`, `stg_daily_transactions.sql` | `load_customer_accounts`, `daily_transaction_processing` |
| **Intermediate** | `int_account_metrics.sql` | `load_customer_accounts` (derived metrics) |
| **Marts** | `mart_daily_transactions.sql`, `mart_risk_scores.sql`, `mart_transaction_anomalies.sql` | `daily_transaction_processing`, `credit_risk_scoring` |
| **Macros** | `format_account_type.sql`, `format_account_status.sql`, `format_customer_segment.sql`, `format_txn_category.sql` | `banking_formats.sas` (4 of 9 formats) |

### Remaining Work

| Gap | SAS Source | dbt Target Needed |
|-----|-----------|-------------------|
| Insurance staging | `claims_processing.sas` | `stg_claims.sql`, `stg_policies.sql` |
| Claims adjudication | `claims_processing.sas` | `int_claims_adjudication.sql` |
| Fraud screening | `claims_processing.sas` | `int_fraud_screening.sql` |
| Policy valuation | `policy_valuation.sas` | `int_policy_valuation.sql` |
| Loss ratios | `policy_valuation.sas` | `mart_loss_ratios.sql` |
| Regulatory RWA | `monthly_regulatory_reporting.sas` | `mart_regulatory_rwa.sql` |
| Delinquency aging | `monthly_regulatory_reporting.sas` | `mart_delinquency_aging.sql` |
| LLP coverage | `monthly_regulatory_reporting.sas` | `mart_llp_coverage.sql` |
| Capital adequacy | `monthly_regulatory_reporting.sas` | `mart_capital_adequacy.sql` |
| Customer P&L | `customer_profitability.sas` | `mart_customer_pnl.sql` |
| Segment profitability | `customer_profitability.sas` | `mart_segment_profitability.sql` |
| Branch profitability | `customer_profitability.sas` | `mart_branch_profitability.sql` |
| 5 insurance formats | `insurance_formats.sas` | 5 new CASE macros |
| 5 banking formats | `banking_formats.sas` | 5 new CASE macros (`format_risk_rating`, `format_delinquency_bucket`, `format_balance_range`, `format_region`, `format_loan_purpose`) |
| Excel export | 2 programs | Databricks notebook or Python script |
| Orchestration | Batch orchestrators | Databricks Workflow YAML |

---

## Appendix A — Full Macro Library Inventory

92 SAS macro files in `Macro/`:

| # | Macro | Lines | Purpose |
|---|-------|-------|---------|
| 1 | `@TEMPLATE` | — | Template for new macros |
| 2 | `CreateTableOrView` | — | Dynamic table/view creation |
| 3 | `IsNum` | — | Numeric check |
| 4 | `IsNumD` | — | Numeric check (date) |
| 5 | `IsNumM` | — | Numeric check (macro) |
| 6 | `RunAll` | — | Batch runner |
| 7 | `RunAll_ControlTable` | — | Batch runner with control table |
| 8 | `age` | — | Age calculation |
| 9 | `align_decimals` | — | Decimal alignment |
| 10 | `attrib` | — | Variable attributes |
| 11 | `batch_submit` | — | Batch job submission |
| 12 | `bench` | — | Benchmarking |
| 13 | `check_if_empty` | — | Empty dataset check |
| 14 | `compare` | — | Dataset comparison |
| 15 | `count_words` | — | Word counter |
| 16 | `create_datetime_range` | — | Date range generator |
| 17 | `create_directory` | — | Directory creation |
| 18 | `create_format` | — | Dynamic format creation |
| 19 | `date_impute` | — | Date imputation |
| 20 | `dedup_mstring` | — | Macro string dedup |
| 21 | `dedup_string` | — | String dedup |
| 22 | `delete_file` | — | File deletion |
| 23 | `dirlist` | — | Directory listing |
| 24 | `dump_mvars` | — | Macro variable dump |
| 25 | `empty` | — | Create empty dataset |
| 26 | `excel2sas` | — | Excel to SAS import |
| 27 | `execpath` | — | Execution path |
| 28 | `execute_macro` | — | Dynamic macro execution |
| 29 | `export` | — | Generic export wrapper |
| 30 | `export_csv` | — | CSV export |
| 31 | `export_dbms` | — | DBMS export (core) |
| 32 | `export_dlm` | — | Delimited export |
| 33 | `export_rldx` | — | RLDX export |
| 34 | `export_saphari` | — | SAPHARI export |
| 35 | `export_sas` | — | SAS transport export |
| 36 | `export_spss` | — | SPSS export |
| 37 | `export_stata` | — | Stata export |
| 38 | `export_tab` | — | Tab-delimited export |
| 39 | `export_xlsx` | 101 | Excel export (→ `export_dbms`) |
| 40 | `fmtexist` | — | Format existence check |
| 41 | `fmtlist` | — | Format listing |
| 42 | `format_text` | — | Text formatting |
| 43 | `get_data_attr` | — | Dataset attributes |
| 44 | `get_dups` | — | Duplicate finder |
| 45 | `get_lib_attr` | — | Library attributes |
| 46 | `get_parameters` | — | Parameter retrieval |
| 47 | `get_permutations` | — | Permutation generator |
| 48 | `getpassword` | — | Password retrieval |
| 49 | `guess_pk` | — | Primary key guesser |
| 50 | `handle` | — | File handle management |
| 51 | `hash_define` | — | Hash object definition |
| 52 | `hash_lookup` | — | Hash object lookup |
| 53 | `hash_split_dataset` | — | Hash-based dataset split |
| 54 | `justify` | — | Text justification |
| 55 | `kill` | — | Process termination |
| 56 | `libname_attr_sqlsvr` | — | SQL Server LIBNAME attributes |
| 57 | `libname_sqlsvr` | — | SQL Server LIBNAME |
| 58 | `lock` | 352 | Dataset locking |
| 59 | `log2pdf` | — | Log to PDF conversion |
| 60 | `logparse` | — | Log file parser |
| 61 | `loop` | — | Loop execution |
| 62 | `loop_control` | — | Loop with control table |
| 63 | `marker` | — | Code section marker |
| 64 | `max_decimals` | — | Max decimal places |
| 65 | `nobs` | 253 | Observation counter |
| 66 | `optload` | — | Options loader |
| 67 | `optsave` | — | Options saver |
| 68 | `optval` | — | Option value retrieval |
| 69 | `pagexofy` | — | Page X of Y numbering |
| 70 | `parmv` | 359 | Parameter validation |
| 71 | `queryActiveDirectory` | — | Active Directory query |
| 72 | `randlist` | — | Random list generator |
| 73 | `realloc_concat_libs` | — | Library reallocation |
| 74 | `reduce_pixel` | — | Image pixel reduction |
| 75 | `sendmail` | 260 | Email notification |
| 76 | `seplist` | — | Separated list generator |
| 77 | `splitvar` | — | Variable splitter |
| 78 | `sql_datetime` | — | SQL datetime conversion |
| 79 | `squote` | — | Single-quote wrapper |
| 80 | `stp_batch_submit` | — | Stored process batch submit |
| 81 | `stp_seplist` | — | Stored process sep list |
| 82 | `stp_session` | — | Stored process session |
| 83 | `subset_data` | — | Data subsetting |
| 84 | `symget` | — | Macro variable getter |
| 85 | `time_interval` | — | Time interval calc |
| 86 | `transpose` | — | Dataset transpose |
| 87 | `txt2pdf` | — | Text to PDF |
| 88 | `txt2rtf` | — | Text to RTF |
| 89 | `useridToEmail` | — | User ID to email |
| 90 | `varexist` | — | Variable existence check |
| 91 | `varlist` | — | Variable list retrieval |
| 92 | `varlist2` | — | Variable list (v2) |

---

*Generated by automated SAS codebase analysis. Cross-reference with `uc-data-migration-sas-to-databricks/docs/SAS_TO_DBT_MIGRATION_MAP.md` for construct-level mapping details.*
