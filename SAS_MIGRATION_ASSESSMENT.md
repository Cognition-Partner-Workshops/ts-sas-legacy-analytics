# SAS Legacy Analytics — Migration Assessment

> **Repository:** `ts-sas-legacy-analytics`
> **Assessment Date:** 2026-05-20
> **SAS Version:** SAS 9.4 M7 on Linux (RHEL 7)
> **Scope:** Full codebase — Config, Programs (Banking / Insurance / Reports), Macros, Formats, BatchJobs, Logs

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Artifact Inventory](#2-artifact-inventory)
3. [Library & Connection Map](#3-library--connection-map)
4. [Program-Level Analysis](#4-program-level-analysis)
   - 4.1 [Banking Programs](#41-banking-programs)
   - 4.2 [Insurance Programs](#42-insurance-programs)
   - 4.3 [Reports Programs](#43-reports-programs)
5. [Data Lineage Diagram](#5-data-lineage-diagram)
6. [Macro Dependency Graph](#6-macro-dependency-graph)
7. [Dataset Usage Matrix](#7-dataset-usage-matrix)
8. [Custom Formats Inventory](#8-custom-formats-inventory)
9. [Batch Orchestration & Dependency Chain](#9-batch-orchestration--dependency-chain)
10. [Production Volumes & Execution Times](#10-production-volumes--execution-times)
11. [Complexity Scores](#11-complexity-scores)
12. [Risk Areas](#12-risk-areas)
13. [Recommended Migration Sequence](#13-recommended-migration-sequence)

---

## 1. Executive Summary

This SAS estate comprises **7 core programs**, **2 batch orchestrators**, **2 format catalogs**, and **92 reusable macros** supporting a dual-domain analytics platform for **Banking** and **Insurance**. The codebase connects to **Oracle DW** and **Teradata** for source data, processes flat-file feeds, and produces curated datasets and Excel regulatory reports.

**Key Statistics:**

| Metric | Value |
|--------|-------|
| Core SAS programs | 7 |
| Batch orchestrators | 2 |
| Macro library files | 92 |
| Custom format catalogs | 2 (Banking: 9 formats, Insurance: 5 formats) |
| LIBNAME assignments | 12 (8 file-based, 2 Oracle, 1 Teradata, 3 format catalogs) |
| Database connections | 2 (Oracle `ORA_DW`, Teradata `TERA_DW`) |
| Production row volumes | ~847K accounts/day, ~2.3M transactions/day, 67M+ cumulative |
| Daily batch runtime | ~10 min (banking), est. ~5 min (insurance) |
| SAS construct coverage | DATA steps, PROC SQL, PROC MEANS, PROC FREQ, PROC APPEND, PROC FORMAT, PROC EXPORT, PROC DATASETS, hash objects, RETAIN/BY-group, %MACRO/%INCLUDE, %GOTO error handling, macro variable resolution |

**Migration Target Recommendation:** dbt (SQL models + Jinja macros) on Databricks / Snowflake, with Python for non-SQL logic (hash lookups, scorecard model, email notifications).

---

## 2. Artifact Inventory

### 2.1 Configuration

| File | Purpose | Lines |
|------|---------|-------|
| `Config/autoexec.sas` | Global environment: LIBNAMEs, DB connections, macro vars, system options | 118 |

### 2.2 Programs

| File | Domain | Lines | Schedule |
|------|--------|-------|----------|
| `Programs/Banking/load_customer_accounts.sas` | Banking | 216 | Daily 06:00 |
| `Programs/Banking/daily_transaction_processing.sas` | Banking | 246 | Daily 07:30 |
| `Programs/Banking/credit_risk_scoring.sas` | Banking | 270 | Weekly Sun 02:00 |
| `Programs/Banking/monthly_regulatory_reporting.sas` | Banking | 199 | Monthly 3rd biz day |
| `Programs/Insurance/claims_processing.sas` | Insurance | 238 | Daily 08:00 |
| `Programs/Insurance/policy_valuation.sas` | Insurance | 206 | Monthly 5th biz day |
| `Programs/Reports/customer_profitability.sas` | Reports | 176 | Monthly 10th biz day |

### 2.3 Batch Orchestrators

| File | Domain | Lines | Schedule |
|------|--------|-------|----------|
| `BatchJobs/run_daily_banking.sas` | Banking | 161 | Daily 05:45 |
| `BatchJobs/run_daily_insurance.sas` | Insurance | 133 | Daily 07:00 |

### 2.4 Format Catalogs

| File | Domain | Formats Defined | Lines |
|------|--------|-----------------|-------|
| `Formats/banking_formats.sas` | Banking | 9 (`$ACCTTYPE`, `$ACCTSTAT`, `RISKRATE`, `$TXNCAT`, `DELQBKT`, `BALRANGE`, `$REGION`, `$CUSTSEG`, `$LNPURP`) | 131 |
| `Formats/insurance_formats.sas` | Insurance | 5 (`$POLTYPE`, `$CLMSTAT`, `$RISKCAT`, `$COVTYPE`, `LOSSRANGE`) | 85 |

### 2.5 Macro Library (92 files)

| Category | Count | Key Macros |
|----------|-------|------------|
| Parameter validation | 1 | `parmv.sas` |
| Dataset utilities | 8 | `nobs.sas`, `lock.sas`, `check_if_empty.sas`, `empty.sas`, `get_data_attr.sas`, `get_dups.sas`, `guess_pk.sas`, `subset_data.sas` |
| Hash object helpers | 3 | `hash_define.sas`, `hash_lookup.sas`, `hash_split_dataset.sas` |
| Export/import | 11 | `export_xlsx.sas`, `export_csv.sas`, `export_dbms.sas`, `export_dlm.sas`, `export_tab.sas`, `export_sas.sas`, `export_spss.sas`, `export_stata.sas`, `export_rldx.sas`, `export_saphari.sas`, `excel2sas.sas` |
| String/list processing | 8 | `seplist.sas`, `squote.sas`, `count_words.sas`, `dedup_string.sas`, `dedup_mstring.sas`, `splitvar.sas`, `justify.sas`, `format_text.sas` |
| Variable/attribute helpers | 5 | `varexist.sas`, `varlist.sas`, `varlist2.sas`, `attrib.sas`, `get_lib_attr.sas` |
| Date/time utilities | 4 | `age.sas`, `date_impute.sas`, `create_datetime_range.sas`, `time_interval.sas`, `sql_datetime.sas` |
| Notification/email | 1 | `sendmail.sas` |
| Logging/diagnostics | 4 | `logparse.sas`, `log2pdf.sas`, `dump_mvars.sas`, `marker.sas` |
| Execution control | 6 | `RunAll.sas`, `RunAll_ControlTable.sas`, `batch_submit.sas`, `stp_batch_submit.sas`, `loop.sas`, `loop_control.sas` |
| Format utilities | 3 | `fmtexist.sas`, `fmtlist.sas`, `create_format.sas` |
| Numeric checks | 3 | `IsNum.sas`, `IsNumD.sas`, `IsNumM.sas` |
| File/directory ops | 3 | `create_directory.sas`, `delete_file.sas`, `dirlist.sas` |
| Other utilities | 22 | `compare.sas`, `transpose.sas`, `align_decimals.sas`, `max_decimals.sas`, `bench.sas`, `execpath.sas`, `execute_macro.sas`, `get_parameters.sas`, `get_permutations.sas`, `getpassword.sas`, `handle.sas`, `kill.sas`, `libname_sqlsvr.sas`, `libname_attr_sqlsvr.sas`, `optload.sas`, `optsave.sas`, `optval.sas`, `pagexofy.sas`, `queryActiveDirectory.sas`, `randlist.sas`, `realloc_concat_libs.sas`, `reduce_pixel.sas`, `stp_seplist.sas`, `stp_session.sas`, `symget.sas`, `txt2pdf.sas`, `txt2rtf.sas`, `useridToEmail.sas`, `@TEMPLATE.sas`, `CreateTableOrView.sas` |

### 2.6 Log Files

| File | Program | Date |
|------|---------|------|
| `Logs/load_customer_accounts_20240115.log` | load_customer_accounts | 2024-01-15 |
| `Logs/daily_transaction_processing_20240115.log` | daily_transaction_processing | 2024-01-15 |

### 2.7 Other Assets

| Directory | Contents |
|-----------|----------|
| `EGProjects/` | Enterprise Guide project (SCD2 Processing template, `.egp`) |
| `AMO/` | Deployment package (`.spk`), SNUG 2013 materials |
| `Presentations/` | SNUG Q4 2016 tips and tricks (`.egp`, `.docx`) |

---

## 3. Library & Connection Map

### 3.1 File-Based Libraries

| LIBNAME | Physical Path | Access | Usage |
|---------|---------------|--------|-------|
| `RAW` | `/data/sas/raw` | readonly | Raw data landing zone |
| `RAW_BANK` | `/data/sas/raw/banking` | readonly | Banking feed files |
| `RAW_INS` | `/data/sas/raw/insurance` | readonly | Insurance feed files |
| `STAGING` | `/data/sas/staging` | read/write | Intermediate processing |
| `STG_BANK` | `/data/sas/staging/banking` | read/write | Banking staging |
| `STG_INS` | `/data/sas/staging/insurance` | read/write | Insurance staging |
| `CURATED` | `/data/sas/curated` | read/write | Production analytics |
| `REPORTS` | `/data/sas/reports` | read/write | Report output datasets |
| `ARCHIVE` | `/data/sas/archive` | read/write | Historical batch logs |

### 3.2 Format Libraries

| LIBNAME | Physical Path | Target Catalog |
|---------|---------------|----------------|
| `BANKING` | `/data/sas/formats/banking` | `BANKING.FORMATS` |
| `INSURANCE` | `/data/sas/formats/insurance` | `INSURANCE.FORMATS` |
| `COMMON` | `/data/sas/formats/common` | `COMMON.FORMATS` |

### 3.3 Database Connections

| LIBNAME | Engine | Server/Path | Schema/Database | Auth | Options |
|---------|--------|-------------|-----------------|------|---------|
| `ORA_DW` | Oracle (SAS/ACCESS) | `FINPROD` | `DW_BANKING` | `&ora_uid` / `&ora_pwd` | `readbuff=5000`, `insertbuff=2000`, readonly |
| `TERA_DW` | Teradata (SAS/ACCESS) | `tdprod.internal.corp` | `ANALYTICS` | `&tera_uid` / `&tera_pwd` | `bulkload=yes`, readonly |

### 3.4 Global Macro Variables

| Variable | Value/Expression | Purpose |
|----------|------------------|---------|
| `ENVIRONMENT` | `PROD` | Environment identifier |
| `BASE_PATH` | `/data/sas` | Root data path |
| `LOG_PATH` | `/data/sas/logs` | Log output directory |
| `REPORT_PATH` | `/data/sas/reports/output` | Report file output |
| `ARCHIVE_PATH` | `/data/sas/archive` | Archive directory |
| `CURR_DT` | `%sysfunc(today(), date9.)` | Current run date |
| `CURR_YM` | `%sysfunc(today(), yymmn6.)` | Current year-month |
| `PREV_YM` | `intnx(month, today(), -1)` | Previous month |
| `FY_START` | `intnx(year, today(), 0, B)` | Fiscal year start |
| `EMAIL_DL` | `sas-ops@corp.internal` | Distribution list |
| `EMAIL_ONCALL` | `oncall-data@corp.internal` | On-call alerts |
| `MAX_OBS_WARN` | `10000000` | Row count warning threshold |
| `ABORT_ON_ERR` | `Y` | Batch abort on error flag |

---

## 4. Program-Level Analysis

### 4.1 Banking Programs

#### 4.1.1 `load_customer_accounts.sas` — Daily Customer Account Snapshot

| Attribute | Detail |
|-----------|--------|
| **Schedule** | Daily 06:00 (Control-M `BANK_DAILY_01`) |
| **Inputs (read)** | `ORA_DW.CUST_ACCOUNTS`, `ORA_DW.CUST_DEMOGRAPHICS`, `RAW_BANK.DAILY_RATES` |
| **Outputs (write)** | `STG_BANK.CUST_ACCOUNTS_DAILY`, `STG_BANK.ACCT_EXCEPTIONS` |
| **Macros used** | `%parmv`, `%nobs`, `%lock`, `%sendmail` |
| **SAS constructs** | PROC SQL (multi-table join from Oracle), DATA step (business rules, conditional output), PROC MEANS (summary statistics), PROC SQL INSERT, PROC DATASETS, `%GOTO` error handling, conditional `%INCLUDE`, macro variable resolution (`&run_date`, `&region`), custom formats (`$ACCTTYPE.`, `$ACCTSTAT.`, `RISKRATE.`, `$CUSTSEG.`, `$REGION.`) |
| **Key logic** | Oracle DW extract → business rule validation (negative balances, high utilization, missing risk rating) → exception routing → summary statistics → email alerts for critical exceptions |
| **Derived columns** | `ACCT_AGE_MONTHS`, `DAYS_INACTIVE`, `UTILIZATION_PCT`, `DORMANCY_FLAG`, `HIGH_BALANCE_FLAG`, `SNAPSHOT_DATE`, `LOAD_TIMESTAMP` |

#### 4.1.2 `daily_transaction_processing.sas` — Transaction ETL Pipeline

| Attribute | Detail |
|-----------|--------|
| **Schedule** | Daily 07:30 (Control-M `BANK_DAILY_02`) |
| **Depends on** | `load_customer_accounts.sas` (Step 1 in batch) |
| **Inputs (read)** | `RAW_BANK.TXN_FEED_YYYYMMDD` (dynamic name), `STG_BANK.CUST_ACCOUNTS_DAILY`, `CURATED.DAILY_TRANSACTIONS` (90-day lookback) |
| **Outputs (write)** | `CURATED.DAILY_TRANSACTIONS` (append), `CURATED.TXN_ANOMALIES` (append), `CURATED.RUNNING_BALANCES` (overwrite) |
| **Macros used** | `%parmv`, `%nobs`, `%lock` |
| **SAS constructs** | DATA step (input validation with `RETURN`), PROC SQL (enrichment join, anomaly stats), DATA step with **RETAIN** and **BY-group** processing (running balance), PROC APPEND with **dataset locking**, PROC DATASETS, `%GOTO` error handling, dynamic dataset naming (`%sysfunc(putn())`), `%sysfunc(exist())` check |
| **Key logic** | Feed validation (reject missing fields, out-of-range amounts, invalid types, future dates) → enrichment join to account data → running balance via RETAIN → anomaly detection (z-score > 3, overdraft, large withdrawal, orphan account) → curated layer append with locking |
| **Anomaly types** | `HIGH_AMOUNT`, `OVERDRAFT`, `LARGE_WITHDRAWAL`, `ORPHAN_ACCOUNT` |

#### 4.1.3 `credit_risk_scoring.sas` — Credit Risk Model Execution (Basel III)

| Attribute | Detail |
|-----------|--------|
| **Schedule** | Weekly Sunday 02:00 (Control-M `BANK_WEEKLY_01`) |
| **Inputs (read)** | `STG_BANK.CUST_ACCOUNTS_DAILY`, `ORA_DW.BUREAU_SCORES`, `ORA_DW.PAYMENT_HISTORY`, `ORA_DW.COLLATERAL` |
| **Outputs (write)** | `CURATED.RISK_SCORES` (append), `CURATED.RISK_MIGRATION` (append), `REPORTS.RISK_SUMMARY` |
| **Macros used** | `%parmv`, `%nobs`, `%lock` |
| **SAS constructs** | PROC SQL (4-table join with correlated subquery for latest bureau score), DATA step (WOE binning, logistic regression scoring, PD/LGD/EAD calculation), PROC SQL (risk migration matrix), PROC APPEND with locking, PROC MEANS (risk summary), PROC DATASETS |
| **Key logic** | Feature assembly from 4 sources → WOE (Weight of Evidence) binning for FICO, utilization, payment history, account age, LTV → logistic regression log-odds → PD calculation → LGD/EAD estimation → expected loss → risk rating assignment (1-7 scale) → migration matrix (upgrade/downgrade/stable/new) |
| **Model coefficients** | Hardcoded from validated model `CRM-2023-Q4-v2` — intercept: -3.2145, weights: FICO(0.412), UTIL(0.198), DPD(0.289), AGE(0.067), LTV(0.134) |

#### 4.1.4 `monthly_regulatory_reporting.sas` — Basel III / Call Report

| Attribute | Detail |
|-----------|--------|
| **Schedule** | Monthly 3rd business day (Control-M `BANK_MONTHLY_01`) |
| **Inputs (read)** | `STG_BANK.CUST_ACCOUNTS_DAILY`, `ORA_DW.LOAN_DETAILS`, `ORA_DW.COLLATERAL`, `REPORTS.MONTHLY_RWA` (self-reference for capital adequacy) |
| **Outputs (write)** | `REPORTS.MONTHLY_RWA`, `REPORTS.DELINQUENCY_AGING`, `REPORTS.LLP_COVERAGE`, `REPORTS.CAPITAL_ADEQUACY`, `/data/sas/reports/output/REG_REPORT_YYYYMM.xlsx` |
| **Macros used** | `%parmv`, `%nobs`, `%export_xlsx` |
| **SAS constructs** | PROC SQL (risk-weighted asset calculation with CASE expressions, delinquency bucketing, loan loss provision coverage, capital adequacy ratios), `%export_xlsx` (multi-sheet Excel output), `calculated` column references |
| **Key logic** | Basel III standardized risk weights by account type/LTV → RWA aggregation → delinquency aging (current/1-29/30-59/60-89/90-119/120-179/180+) → LLP coverage and NPL ratios → capital adequacy (CET1/Tier1/Total Capital vs. minimums 4.5%/6%/8%) → Excel export for regulators |

### 4.2 Insurance Programs

#### 4.2.1 `claims_processing.sas` — Daily Claims Intake and Processing

| Attribute | Detail |
|-----------|--------|
| **Schedule** | Daily 08:00 (Control-M `INS_DAILY_01`) |
| **Inputs (read)** | `RAW_INS.CLAIMS_FEED_YYYYMMDD` (dynamic name), `RAW_INS.POLICIES`, `TERA_DW.FRAUD_INDICATORS` |
| **Outputs (write)** | `STG_INS.CLAIMS_REGISTER` (append), `STG_INS.CLAIMS_REVIEW_QUEUE` (append), `STG_INS.FRAUD_ALERTS` (append) |
| **Macros used** | `%parmv`, `%nobs`, `%sendmail` |
| **SAS constructs** | DATA step with **hash object** (`declare hash h_pol`) for policy lookup, PROC SQL (fraud screening join to Teradata), DATA step (auto-adjudication rule engine), PROC APPEND, `%sysfunc(exist())`, `%GOTO` error handling, custom formats (`$CLMSTAT.`) |
| **Key logic** | Feed validation via hash lookup (policy exists, active, loss date in policy period, claimed ≤ sum insured) → fraud screening from Teradata (score ≥ 80 = HIGH, ≥ 50 = MEDIUM) → auto-adjudication rules (auto-approve small low-risk; auto-deny high fraud risk; manual review for medium risk/large claims) → claims register update → SIU email alerts |
| **Hash object detail** | Loaded from `RAW_INS.POLICIES(where=(STATUS='ACTIVE'))` with keys `POLICY_ID`, data fields: `POLICY_TYPE`, `EFFECTIVE_DATE`, `EXPIRATION_DATE`, `SUM_INSURED`, `DEDUCTIBLE` |

#### 4.2.2 `policy_valuation.sas` — Monthly Policy Book Valuation

| Attribute | Detail |
|-----------|--------|
| **Schedule** | Monthly 5th business day (Control-M `INS_MONTHLY_01`) |
| **Inputs (read)** | `RAW_INS.POLICIES`, `RAW_INS.CLAIMS`, `RAW_INS.PREMIUMS`, `TERA_DW.ACTUARIAL_TABLES` |
| **Outputs (write)** | `STG_INS.POLICY_VALUATION`, `REPORTS.LOSS_RATIO_SUMMARY`, `REPORTS.RESERVE_ADEQUACY` |
| **Macros used** | `%parmv`, `%nobs` |
| **SAS constructs** | PROC SQL (in-force extract, claims experience 12-month window, premium collections), DATA step **MERGE** (3-way by `POLICY_ID`), PROC MEANS (loss ratio summary), DATA step (post-aggregation calculations), custom formats (`$POLTYPE.`, `$RISKCAT.`), `coalesce()`, conditional macro (`%if &lob ne ALL`) |
| **Key logic** | In-force policy extract → claims experience (12-month rolling window: incurred, paid, reserved, denied) → premium collections (YTD) → 3-way merge → loss ratio, combined ratio (loss + 30% expense), premium adequacy, IBNR estimate (15% of earned − paid), total reserve (case + IBNR) → aggregate loss ratio summary by line of business |

### 4.3 Reports Programs

#### 4.3.1 `customer_profitability.sas` — Customer P&L and Profitability

| Attribute | Detail |
|-----------|--------|
| **Schedule** | Monthly 10th business day (Control-M `BANK_MONTHLY_03`) |
| **Inputs (read)** | `STG_BANK.CUST_ACCOUNTS_DAILY`, `CURATED.DAILY_TRANSACTIONS`, `CURATED.RISK_SCORES`, `ORA_DW.COST_OF_FUNDS` |
| **Outputs (write)** | `REPORTS.CUSTOMER_PNL`, `REPORTS.SEGMENT_PROFITABILITY`, `REPORTS.BRANCH_PROFITABILITY`, `/data/sas/reports/output/PROFITABILITY_YYYYMM.xlsx` |
| **Macros used** | `%parmv`, `%nobs`, `%export_xlsx` |
| **SAS constructs** | PROC SQL (interest income, fee income, expected credit loss — each by customer), DATA step MERGE (3-way by `CUSTOMER_ID`), PROC MEANS (segment and branch summaries), `%export_xlsx`, `calculated` column references, `coalesce()` |
| **Key logic** | Interest income (lending income − deposit cost) → fee income from transactions → ECL from risk scores → customer P&L assembly (revenue − operating cost − ECL) → ROA → profitability tiering → segment and branch rollups → Excel export |

---

## 5. Data Lineage Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SOURCES                                    │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────┐     ┌─────────────────────┐     ┌───────────────────┐  │
│  │     Oracle DW        │     │    Teradata DW       │     │   Flat File Feeds │  │
│  │  (ORA_DW / FINPROD)  │     │  (TERA_DW / ANALYTICS│     │   (RAW_BANK,     │  │
│  │                      │     │                      │     │    RAW_INS)       │  │
│  │ • CUST_ACCOUNTS      │     │ • FRAUD_INDICATORS   │     │ • TXN_FEED_*     │  │
│  │ • CUST_DEMOGRAPHICS  │     │ • ACTUARIAL_TABLES   │     │ • CLAIMS_FEED_*  │  │
│  │ • BUREAU_SCORES      │     │                      │     │ • POLICIES       │  │
│  │ • PAYMENT_HISTORY    │     └──────────┬───────────┘     │ • CLAIMS         │  │
│  │ • COLLATERAL         │                │                  │ • PREMIUMS       │  │
│  │ • LOAN_DETAILS       │                │                  │ • DAILY_RATES    │  │
│  │ • COST_OF_FUNDS      │                │                  └────────┬─────────┘  │
│  └──────────┬───────────┘                │                           │            │
└─────────────┼────────────────────────────┼───────────────────────────┼────────────┘
              │                            │                           │
              ▼                            ▼                           ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           STAGING LAYER (STG_BANK / STG_INS)                     │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────────────┐        ┌──────────────────────────────┐        │
│  │ load_customer_accounts.sas   │        │ claims_processing.sas        │        │
│  │ (Daily 06:00)                │        │ (Daily 08:00)                │        │
│  │                              │        │                              │        │
│  │ ORA_DW.CUST_ACCOUNTS ──────►│        │ RAW_INS.CLAIMS_FEED_* ─────►│        │
│  │ ORA_DW.CUST_DEMOGRAPHICS ──►│        │ RAW_INS.POLICIES ──────────►│        │
│  │                              │        │ TERA_DW.FRAUD_INDICATORS ──►│        │
│  │        │                     │        │        │                     │        │
│  │        ▼                     │        │        ▼                     │        │
│  │ STG_BANK.CUST_ACCOUNTS_DAILY│        │ STG_INS.CLAIMS_REGISTER     │        │
│  │ STG_BANK.ACCT_EXCEPTIONS    │        │ STG_INS.CLAIMS_REVIEW_QUEUE │        │
│  └──────────┬───────────────────┘        │ STG_INS.FRAUD_ALERTS       │        │
│             │                            └──────────────────────────────┘        │
│             │                                                                    │
│             ▼                                                                    │
│  ┌──────────────────────────────┐        ┌──────────────────────────────┐        │
│  │ daily_transaction_processing │        │ policy_valuation.sas         │        │
│  │ (Daily 07:30)                │        │ (Monthly 5th biz day)        │        │
│  │                              │        │                              │        │
│  │ RAW_BANK.TXN_FEED_* ───────►│        │ RAW_INS.POLICIES ──────────►│        │
│  │ STG_BANK.CUST_ACCOUNTS_DAILY►│       │ RAW_INS.CLAIMS ────────────►│        │
│  │                              │        │ RAW_INS.PREMIUMS ──────────►│        │
│  │        │                     │        │ TERA_DW.ACTUARIAL_TABLES ──►│        │
│  │        ▼                     │        │        │                     │        │
│  │ CURATED.DAILY_TRANSACTIONS   │        │        ▼                     │        │
│  │ CURATED.TXN_ANOMALIES       │        │ STG_INS.POLICY_VALUATION    │        │
│  │ CURATED.RUNNING_BALANCES     │        │ REPORTS.LOSS_RATIO_SUMMARY  │        │
│  └──────────┬───────────────────┘        │ REPORTS.RESERVE_ADEQUACY    │        │
└─────────────┼────────────────────────────┴──────────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                        CURATED / REPORTING LAYER                                 │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────────────┐        ┌──────────────────────────────┐        │
│  │ credit_risk_scoring.sas      │        │ monthly_regulatory_reporting │        │
│  │ (Weekly Sun 02:00)           │        │ (Monthly 3rd biz day)        │        │
│  │                              │        │                              │        │
│  │ STG_BANK.CUST_ACCOUNTS_DAILY►│       │ STG_BANK.CUST_ACCOUNTS_DAILY►│       │
│  │ ORA_DW.BUREAU_SCORES ───────►│        │ ORA_DW.LOAN_DETAILS ───────►│        │
│  │ ORA_DW.PAYMENT_HISTORY ─────►│        │ ORA_DW.COLLATERAL ─────────►│        │
│  │ ORA_DW.COLLATERAL ──────────►│        │                              │        │
│  │        │                     │        │        │                     │        │
│  │        ▼                     │        │        ▼                     │        │
│  │ CURATED.RISK_SCORES          │        │ REPORTS.MONTHLY_RWA          │        │
│  │ CURATED.RISK_MIGRATION       │        │ REPORTS.DELINQUENCY_AGING    │        │
│  │ REPORTS.RISK_SUMMARY         │        │ REPORTS.LLP_COVERAGE         │        │
│  └──────────┬───────────────────┘        │ REPORTS.CAPITAL_ADEQUACY     │        │
│             │                            │ REG_REPORT_YYYYMM.xlsx       │        │
│             │                            └──────────────────────────────┘        │
│             ▼                                                                    │
│  ┌──────────────────────────────┐                                                │
│  │ customer_profitability.sas   │                                                │
│  │ (Monthly 10th biz day)       │                                                │
│  │                              │                                                │
│  │ STG_BANK.CUST_ACCOUNTS_DAILY►│                                               │
│  │ CURATED.DAILY_TRANSACTIONS ─►│                                                │
│  │ CURATED.RISK_SCORES ────────►│                                                │
│  │ ORA_DW.COST_OF_FUNDS ──────►│                                                │
│  │        │                     │                                                │
│  │        ▼                     │                                                │
│  │ REPORTS.CUSTOMER_PNL         │                                                │
│  │ REPORTS.SEGMENT_PROFITABILITY│                                                │
│  │ REPORTS.BRANCH_PROFITABILITY │                                                │
│  │ PROFITABILITY_YYYYMM.xlsx    │                                                │
│  └──────────────────────────────┘                                                │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Macro Dependency Graph

### 6.1 Macros Directly Referenced by Programs

```
Programs/Banking/load_customer_accounts.sas
  ├── %parmv          (parameter validation)
  ├── %nobs           (observation count)
  ├── %lock           (dataset locking)
  └── %sendmail       (email notification — conditional)

Programs/Banking/daily_transaction_processing.sas
  ├── %parmv
  ├── %nobs
  └── %lock

Programs/Banking/credit_risk_scoring.sas
  ├── %parmv
  ├── %nobs
  └── %lock

Programs/Banking/monthly_regulatory_reporting.sas
  ├── %parmv
  ├── %nobs
  └── %export_xlsx    (Excel export)

Programs/Insurance/claims_processing.sas
  ├── %parmv
  ├── %nobs
  └── %sendmail

Programs/Insurance/policy_valuation.sas
  ├── %parmv
  └── %nobs

Programs/Reports/customer_profitability.sas
  ├── %parmv
  ├── %nobs
  └── %export_xlsx

BatchJobs/run_daily_banking.sas
  └── %sendmail

BatchJobs/run_daily_insurance.sas
  └── %sendmail
```

### 6.2 Macro Internal Dependencies (transitive)

```
%parmv          → (none — leaf macro)
%nobs           → %parmv
%lock           → %parmv, %get_data_attr, %handle
%sendmail       → %parmv, %seplist
%export_xlsx    → %export_dbms, %parmv
%export_dbms    → %parmv
%handle         → %parmv
%get_data_attr  → %parmv
%seplist        → %parmv
%hash_define    → %parmv, %seplist
%hash_lookup    → (generated code from %hash_define)
```

### 6.3 Migration-Critical Macros (6 of 92)

| Macro | Used By | Migration Target |
|-------|---------|------------------|
| `%parmv` | All programs | dbt `{{ config() }}` validation or Python `assert` |
| `%nobs` | All programs | dbt `{{ adapter.get_relation() }}` or `SELECT COUNT(*)` |
| `%lock` | load_customer_accounts, daily_transaction_processing, credit_risk_scoring | Delta Lake / Snowflake native concurrency (not needed) |
| `%sendmail` | load_customer_accounts, claims_processing, batch orchestrators | Databricks alerts, PagerDuty, SNS |
| `%export_xlsx` | monthly_regulatory_reporting, customer_profitability | Databricks notebooks / Python `openpyxl` |
| `%hash_define` / `%hash_lookup` | Not directly `%include`'d but pattern used inline in `claims_processing.sas` | Python dicts / Spark broadcast joins |

---

## 7. Dataset Usage Matrix

### 7.1 Read Matrix (Program × Source Dataset)

| Dataset | load_cust_accts | daily_txn | credit_risk | monthly_reg | claims_proc | policy_val | cust_profit |
|---------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **ORA_DW.CUST_ACCOUNTS** | R | | | | | | |
| **ORA_DW.CUST_DEMOGRAPHICS** | R | | | | | | |
| **ORA_DW.BUREAU_SCORES** | | | R | | | | |
| **ORA_DW.PAYMENT_HISTORY** | | | R | | | | |
| **ORA_DW.COLLATERAL** | | | R | R | | | |
| **ORA_DW.LOAN_DETAILS** | | | | R | | | |
| **ORA_DW.COST_OF_FUNDS** | | | | | | | R |
| **TERA_DW.FRAUD_INDICATORS** | | | | | R | | |
| **TERA_DW.ACTUARIAL_TABLES** | | | | | | R | |
| **RAW_BANK.TXN_FEED_*** | | R | | | | | |
| **RAW_BANK.DAILY_RATES** | R | | | | | | |
| **RAW_INS.CLAIMS_FEED_*** | | | | | R | | |
| **RAW_INS.POLICIES** | | | | | R | R | |
| **RAW_INS.CLAIMS** | | | | | | R | |
| **RAW_INS.PREMIUMS** | | | | | | R | |
| **STG_BANK.CUST_ACCOUNTS_DAILY** | | R | R | R | | | R |
| **CURATED.DAILY_TRANSACTIONS** | | R | | | | | R |
| **CURATED.RISK_SCORES** | | | | | | | R |
| **REPORTS.MONTHLY_RWA** | | | | R | | | |

### 7.2 Write Matrix (Program × Output Dataset)

| Dataset | load_cust_accts | daily_txn | credit_risk | monthly_reg | claims_proc | policy_val | cust_profit |
|---------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **STG_BANK.CUST_ACCOUNTS_DAILY** | W | | | | | | |
| **STG_BANK.ACCT_EXCEPTIONS** | W | | | | | | |
| **CURATED.DAILY_TRANSACTIONS** | | A | | | | | |
| **CURATED.TXN_ANOMALIES** | | A | | | | | |
| **CURATED.RUNNING_BALANCES** | | W | | | | | |
| **CURATED.RISK_SCORES** | | | A | | | | |
| **CURATED.RISK_MIGRATION** | | | A | | | | |
| **REPORTS.RISK_SUMMARY** | | | W | | | | |
| **REPORTS.MONTHLY_RWA** | | | | W | | | |
| **REPORTS.DELINQUENCY_AGING** | | | | W | | | |
| **REPORTS.LLP_COVERAGE** | | | | W | | | |
| **REPORTS.CAPITAL_ADEQUACY** | | | | W | | | |
| **STG_INS.CLAIMS_REGISTER** | | | | | A | | |
| **STG_INS.CLAIMS_REVIEW_QUEUE** | | | | | A | | |
| **STG_INS.FRAUD_ALERTS** | | | | | A | | |
| **STG_INS.POLICY_VALUATION** | | | | | | W | |
| **REPORTS.LOSS_RATIO_SUMMARY** | | | | | | W | |
| **REPORTS.RESERVE_ADEQUACY** | | | | | | W | |
| **REPORTS.CUSTOMER_PNL** | | | | | | | W |
| **REPORTS.SEGMENT_PROFITABILITY** | | | | | | | W |
| **REPORTS.BRANCH_PROFITABILITY** | | | | | | | W |
| **ARCHIVE.BATCH_HISTORY** | | | | | | | |

**Legend:** R = Read, W = Write (overwrite), A = Append

---

## 8. Custom Formats Inventory

### 8.1 Banking Formats (`Formats/banking_formats.sas` → `BANKING.FORMATS`)

| Format Name | Type | Values | Migration Target |
|-------------|------|--------|------------------|
| `$ACCTTYPE` | Character | 11 values (CHK→Checking, SAV→Savings, etc.) | dbt seed table `seed_acct_types` or `CASE WHEN` macro |
| `$ACCTSTAT` | Character | 8 values (A→Active, C→Closed, etc.) | dbt seed table `seed_acct_status` |
| `RISKRATE` | Numeric | 7 values (1→Minimal Risk … 7→Loss Expected) | dbt seed table `seed_risk_ratings` |
| `$TXNCAT` | Character | 10 values (DEP→Deposit, WDR→Withdrawal, etc.) | dbt seed table `seed_txn_categories` |
| `DELQBKT` | Numeric range | 7 ranges (0→Current, 1-29→1-29 Days, etc.) | `CASE WHEN` expression in SQL |
| `BALRANGE` | Numeric range | 8 ranges (negative → $500K+) | `CASE WHEN` expression in SQL |
| `$REGION` | Character | 7 values (NE→Northeast, SE→Southeast, etc.) | dbt seed table `seed_regions` |
| `$CUSTSEG` | Character | 6 values (RET→Retail, PREM→Premium, etc.) | dbt seed table `seed_customer_segments` |
| `$LNPURP` | Character | 8 values (PURCH→Purchase, REFI→Refinance, etc.) | dbt seed table `seed_loan_purposes` |

### 8.2 Insurance Formats (`Formats/insurance_formats.sas` → `INSURANCE.FORMATS`)

| Format Name | Type | Values | Migration Target |
|-------------|------|--------|------------------|
| `$POLTYPE` | Character | 13 values (WL→Whole Life, TL→Term Life, etc.) | dbt seed table `seed_policy_types` |
| `$CLMSTAT` | Character | 12 values (NEW→New, OPEN→Open, etc.) | dbt seed table `seed_claim_status` |
| `$RISKCAT` | Character | 5 values (STD→Standard, PREF→Preferred, etc.) | dbt seed table `seed_risk_categories` |
| `$COVTYPE` | Character | 9 values (COMP→Comprehensive, COLL→Collision, etc.) | dbt seed table `seed_coverage_types` |
| `LOSSRANGE` | Numeric range | 6 ranges (Recovery → $500K+) | `CASE WHEN` expression in SQL |

### 8.3 Migration Strategy for Formats

**Character code lookups** → dbt seed CSV files + `LEFT JOIN` or a reusable dbt macro:
```sql
-- dbt macro: format_lookup.sql
{% macro format_lookup(column, format_name) %}
  COALESCE({{ format_name }}.label, 'Unknown')
{% endmacro %}
```

**Numeric range formats** → `CASE WHEN` expressions, wrapped in dbt macros for reuse:
```sql
-- dbt macro: delinquency_bucket.sql
{% macro delinquency_bucket(days_past_due) %}
  CASE
    WHEN {{ days_past_due }} = 0 THEN 'Current'
    WHEN {{ days_past_due }} BETWEEN 1 AND 29 THEN '1-29 Days'
    ...
  END
{% endmacro %}
```

---

## 9. Batch Orchestration & Dependency Chain

### 9.1 Daily Banking Batch (`run_daily_banking.sas`)

```
Control-M: BANK_MASTER (Daily 05:45)
│
├── Step 1: Load Customer Accounts      → load_customer_accounts.sas
│           (extracts from Oracle DW)
│           Output: STG_BANK.CUST_ACCOUNTS_DAILY
│
├── Step 2: Daily Transaction Processing → daily_transaction_processing.sas
│           (depends on Step 1: reads STG_BANK.CUST_ACCOUNTS_DAILY)
│           Output: CURATED.DAILY_TRANSACTIONS, CURATED.TXN_ANOMALIES
│
├── Step 3: Credit Risk Scoring          → credit_risk_scoring.sas
│           (depends on Step 1: reads STG_BANK.CUST_ACCOUNTS_DAILY)
│           Output: CURATED.RISK_SCORES, CURATED.RISK_MIGRATION
│
└── Step 4: Monthly Regulatory Reporting → monthly_regulatory_reporting.sas
            (depends on Step 1: reads STG_BANK.CUST_ACCOUNTS_DAILY)
            Output: REPORTS.MONTHLY_RWA, REPORTS.DELINQUENCY_AGING, etc.
```

**Error handling:** `ABORT_ON_ERR=Y` — batch halts on first failure. Sends email to `EMAIL_ONCALL` with step number for restart. Supports `restart_from=N` parameter to resume from a failed step. Control table logged to `ARCHIVE.BATCH_HISTORY`.

### 9.2 Daily Insurance Batch (`run_daily_insurance.sas`)

```
Control-M: INS_MASTER (Daily 07:00)
│
├── Step 1: Claims Processing           → claims_processing.sas
│           (reads from Teradata + file feeds)
│           Output: STG_INS.CLAIMS_REGISTER, STG_INS.FRAUD_ALERTS
│
└── Step 2: Policy Valuation            → policy_valuation.sas
            (depends on Step 1 indirectly — reads RAW_INS.CLAIMS)
            Output: STG_INS.POLICY_VALUATION, REPORTS.LOSS_RATIO_SUMMARY
```

### 9.3 Cross-Domain Dependencies

```
customer_profitability.sas (Monthly 10th biz day)
  ├── Depends on: STG_BANK.CUST_ACCOUNTS_DAILY  (from load_customer_accounts)
  ├── Depends on: CURATED.DAILY_TRANSACTIONS     (from daily_transaction_processing)
  └── Depends on: CURATED.RISK_SCORES            (from credit_risk_scoring)
```

### 9.4 Migration Target: Orchestration

| SAS Pattern | Migration Target |
|-------------|------------------|
| Control-M job scheduling | Databricks Workflows / Airflow DAGs |
| `%INCLUDE` chain in batch | dbt `ref()` dependency graph |
| `%run_step` macro with SYSCC check | dbt `on-run-end` hooks / Workflow task dependencies |
| `restart_from=N` parameter | Databricks Workflow retry-from-failed / Airflow task retry |
| `ARCHIVE.BATCH_HISTORY` | Databricks job run history / Airflow task instance logs |
| `%sendmail` notifications | Databricks alerts / PagerDuty / SNS |

---

## 10. Production Volumes & Execution Times

### 10.1 From Log Files (2024-01-15 Production Run)

#### `load_customer_accounts` (Daily)

| Step | Description | Rows | Real Time | CPU Time |
|------|-------------|------|-----------|----------|
| PROC SQL (Oracle extract) | Raw extract with join | 847,293 | 2:14 | 1:49 |
| DATA step (business rules) | Validation + derived cols | 847,293 in → 847,293 + 1,247 exceptions | 0:32 | 0:28 |
| PROC MEANS | Summary statistics | 847,293 → 42 summary rows | 0:08 | 0:07 |
| **Total** | | | **2:56** | **2:24** |

#### `daily_transaction_processing` (Daily)

| Step | Description | Rows | Real Time | CPU Time |
|------|-------------|------|-----------|----------|
| DATA step (validation) | Feed validation | 2,341,567 → 2,338,912 valid + 2,655 rejected | 1:12 | 0:59 |
| PROC SQL (enrichment) | Join to account data | 2,338,912 | 3:45 | 2:57 |
| PROC SQL (anomaly stats) | 90-day statistics | 423,891 accounts | — | — |
| PROC SQL (anomaly detection) | Flag anomalies | 3,421 anomalies | — | — |
| PROC APPEND (curated) | Append to cumulative | 2,338,912 → 67,234,891 cumulative | 0:45 | 0:35 |
| DATA step (running balances) | Running balance persist | 2,338,912 | 0:53 | 0:41 |
| **Total** | | | **6:49** | **5:11** |

### 10.2 Key Volume Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Customer accounts (daily snapshot) | 847,293 | Active accounts across all regions |
| Data quality exceptions | 1,247 | 0.15% exception rate |
| Daily transactions (feed) | 2,341,567 | ~2.3M per day |
| Transaction rejection rate | 2,655 / 2,341,567 | 0.11% |
| Anomalies detected | 3,421 | 0.15% of valid transactions |
| Cumulative transaction store | 67,234,891 | ~29 days × 2.3M (growing daily) |
| Account-level stats (90-day) | 423,891 | Unique accounts with 90-day activity |

### 10.3 Estimated Annual Growth

| Dataset | Daily Growth | Annual Projection |
|---------|-------------|-------------------|
| `CURATED.DAILY_TRANSACTIONS` | ~2.3M rows | ~600M rows/year |
| `CURATED.TXN_ANOMALIES` | ~3.4K rows | ~880K rows/year |
| `CURATED.RISK_SCORES` | ~847K/week | ~44M rows/year |
| `STG_INS.CLAIMS_REGISTER` | Unknown | Depends on claims volume |

---

## 11. Complexity Scores

### 11.1 Scoring Methodology

| Dimension | Weight | Criteria |
|-----------|--------|----------|
| Data sources | 20% | Number of distinct input sources (libs/tables) |
| SAS constructs | 25% | Variety and complexity of SAS features used |
| Business logic | 25% | Domain complexity, calculations, branching |
| Volume/performance | 15% | Row volumes, execution time, locking needs |
| External dependencies | 15% | DB connections, email, file I/O, Excel output |

### 11.2 Program Complexity Ratings

| Program | Data Sources | SAS Constructs | Business Logic | Volume | Ext. Deps | **Overall** | **Rating** |
|---------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `load_customer_accounts.sas` | 3/5 | 3/5 | 3/5 | 4/5 | 3/5 | **3.2** | **Medium** |
| `daily_transaction_processing.sas` | 3/5 | 5/5 | 4/5 | 5/5 | 2/5 | **3.9** | **High** |
| `credit_risk_scoring.sas` | 4/5 | 4/5 | 5/5 | 3/5 | 2/5 | **3.8** | **High** |
| `monthly_regulatory_reporting.sas` | 3/5 | 3/5 | 4/5 | 3/5 | 4/5 | **3.4** | **Medium-High** |
| `claims_processing.sas` | 3/5 | 5/5 | 4/5 | 3/5 | 3/5 | **3.7** | **High** |
| `policy_valuation.sas` | 4/5 | 3/5 | 4/5 | 3/5 | 2/5 | **3.3** | **Medium** |
| `customer_profitability.sas` | 4/5 | 3/5 | 3/5 | 3/5 | 3/5 | **3.2** | **Medium** |
| `run_daily_banking.sas` | 1/5 | 4/5 | 3/5 | 1/5 | 3/5 | **2.5** | **Medium** |
| `run_daily_insurance.sas` | 1/5 | 4/5 | 2/5 | 1/5 | 3/5 | **2.3** | **Low-Medium** |

### 11.3 Complexity Summary

| Rating | Programs | Count |
|--------|----------|-------|
| **High** | `daily_transaction_processing`, `credit_risk_scoring`, `claims_processing` | 3 |
| **Medium-High** | `monthly_regulatory_reporting` | 1 |
| **Medium** | `load_customer_accounts`, `policy_valuation`, `customer_profitability`, `run_daily_banking` | 4 |
| **Low-Medium** | `run_daily_insurance` | 1 |

---

## 12. Risk Areas

### 12.1 High Risk

| # | Risk | Impact | Affected Programs | Mitigation |
|---|------|--------|-------------------|------------|
| R1 | **RETAIN / BY-group running balance** | Core pattern in `daily_transaction_processing.sas` uses row-ordered stateful logic that has no direct SQL equivalent. Running balance depends on row order within `ACCOUNT_ID`. | `daily_transaction_processing` | Use SQL window functions: `SUM() OVER (PARTITION BY account_id ORDER BY transaction_date, transaction_id ROWS UNBOUNDED PRECEDING)`. Requires careful validation of tie-breaking semantics. |
| R2 | **Hash object for policy lookup** | `claims_processing.sas` uses `declare hash` to load active policies into memory for key lookup during claim validation. This is a single-pass in-memory join. | `claims_processing` | Replace with Spark broadcast join or a `LEFT JOIN` in SQL. Validate no row-order dependency in hash lookup. |
| R3 | **Hardcoded scorecard coefficients** | `credit_risk_scoring.sas` contains hardcoded WOE bins and logistic regression coefficients (model `CRM-2023-Q4-v2`). These are embedded in DATA step logic, not externalized. | `credit_risk_scoring` | Externalize coefficients into a configuration table (dbt seed or Delta table). Build a parameterized scoring model in Python/MLflow. |
| R4 | **Dynamic dataset naming** | `TXN_FEED_%sysfunc(putn())` and `CLAIMS_FEED_%sysfunc()` pattern creates dataset names at runtime based on date. | `daily_transaction_processing`, `claims_processing` | Replace with partitioned tables (e.g., `raw_txn_feed` partitioned by `feed_date`) or a staging table with date column. |
| R5 | **PROC APPEND with dataset locking** | Multiple programs use `%lock` + `PROC APPEND` for concurrent-safe incremental loads. This is a SAS-specific concurrency pattern. | `daily_transaction_processing`, `credit_risk_scoring` | Delta Lake `MERGE INTO` or Snowflake `INSERT INTO` — both handle concurrency natively. Locking macros can be retired. |

### 12.2 Medium Risk

| # | Risk | Impact | Affected Programs | Mitigation |
|---|------|--------|-------------------|------------|
| R6 | **Macro variable date arithmetic** | Extensive use of `%sysfunc(intnx())`, `%sysfunc(putn())`, `"&date"d` date literals. Every program uses these patterns. | All programs | Map to dbt Jinja `{{ var('run_date') }}` + SQL `DATEADD()` / `DATE_TRUNC()`. Create a dbt macro library for common date patterns. |
| R7 | **`%GOTO` error handling** | Programs use `%GOTO EXIT` / `%GOTO ABORT` for flow control. Batch orchestrators use `%if &_batch_abort` flag. | All programs, batch orchestrators | dbt `on-run-end` hooks for post-run checks. Databricks Workflows for step-level failure handling. Python `try/except` for non-SQL logic. |
| R8 | **Custom PROC FORMAT catalogs** | 14 custom formats referenced via `fmtsearch=` option. Format application is implicit in DATA steps. | `load_customer_accounts`, `claims_processing`, `policy_valuation`, `monthly_regulatory_reporting` | Migrate to dbt seed tables + JOIN or Jinja macros. Must audit every `format` statement to ensure labels are correctly mapped. |
| R9 | **PROC MEANS aggregations** | Used for summary statistics with `CLASS`, `VAR`, `OUTPUT` syntax. Produces named statistics (N, SUM, MEAN). | `load_customer_accounts`, `credit_risk_scoring`, `policy_valuation`, `customer_profitability` | Direct SQL `GROUP BY` with `COUNT()`, `SUM()`, `AVG()`. Straightforward but each must be validated. |
| R10 | **Email notifications** | `%sendmail` called for critical exceptions, fraud alerts, and batch status. Integrated into operational workflow. | `load_customer_accounts`, `claims_processing`, batch orchestrators | Databricks alerts / PagerDuty / AWS SNS. Requires operational mapping of notification triggers. |

### 12.3 Low Risk

| # | Risk | Impact | Affected Programs | Mitigation |
|---|------|--------|-------------------|------------|
| R11 | **PROC SQL with `calculated`** | SAS-specific syntax allowing reference to computed columns in the same SELECT. | `monthly_regulatory_reporting`, `customer_profitability` | Use CTEs or subqueries in standard SQL. |
| R12 | **PROC DATASETS cleanup** | Used to delete temp WORK datasets at end of each program. | All programs | Not needed — dbt ephemeral models / temp tables auto-cleanup. |
| R13 | **`%sysfunc(exist())` dataset checks** | Runtime existence checks for feed datasets before processing. | `daily_transaction_processing`, `claims_processing` | dbt `source` freshness checks or Databricks Workflow conditional tasks. |

---

## 13. Recommended Migration Sequence

### 13.1 Phased Approach

#### Phase 0: Foundation (Weeks 1–2)

| Task | Details |
|------|---------|
| Set up target platform | Databricks workspace / Snowflake account, Unity Catalog, dbt project |
| Migrate `autoexec.sas` configuration | Create dbt `profiles.yml`, `dbt_project.yml`, environment variables for DB connections |
| Migrate custom formats | Create dbt seed CSVs for all 14 format definitions |
| Create reusable dbt macros | `format_lookup`, `delinquency_bucket`, `balance_range`, parameter validation |
| Set up Oracle/Teradata connectivity | Configure Databricks external tables or Fivetran/Airbyte for Oracle DW and Teradata |

#### Phase 1: Staging Layer — Banking (Weeks 3–4)

| Order | SAS Program | dbt Model(s) | Rationale |
|-------|-------------|---------------|-----------|
| 1.1 | `load_customer_accounts.sas` | `stg_cust_accounts_daily`, `stg_acct_exceptions` | Foundation table — all other banking programs depend on it |
| 1.2 | `daily_transaction_processing.sas` | `stg_txn_validated`, `int_txn_enriched`, `int_txn_running_balance`, `curated_daily_transactions`, `curated_txn_anomalies` | Highest complexity; RETAIN logic needs window functions |

#### Phase 2: Curated Layer — Banking Analytics (Weeks 5–6)

| Order | SAS Program | dbt Model(s) | Rationale |
|-------|-------------|---------------|-----------|
| 2.1 | `credit_risk_scoring.sas` | `int_score_input`, `curated_risk_scores`, `curated_risk_migration`, `rpt_risk_summary` | Scorecard logic → Python UDF or dbt SQL with externalized coefficients |
| 2.2 | `monthly_regulatory_reporting.sas` | `rpt_monthly_rwa`, `rpt_delinquency_aging`, `rpt_llp_coverage`, `rpt_capital_adequacy` | Pure SQL — straightforward PROC SQL → dbt SQL conversion |

#### Phase 3: Insurance Domain (Weeks 7–8)

| Order | SAS Program | dbt Model(s) | Rationale |
|-------|-------------|---------------|-----------|
| 3.1 | `claims_processing.sas` | `stg_claims_validated`, `int_fraud_check`, `int_auto_adjudicated`, `stg_claims_register`, `stg_fraud_alerts` | Hash object → broadcast join; auto-adjudication rules → CASE WHEN |
| 3.2 | `policy_valuation.sas` | `int_inforce_policies`, `int_claims_experience`, `int_premium_collections`, `stg_policy_valuation`, `rpt_loss_ratio_summary` | 3-way MERGE → SQL JOINs; actuarial calculations → SQL expressions |

#### Phase 4: Cross-Domain Reports (Week 9)

| Order | SAS Program | dbt Model(s) | Rationale |
|-------|-------------|---------------|-----------|
| 4.1 | `customer_profitability.sas` | `int_interest_income`, `int_fee_income`, `int_ecl`, `rpt_customer_pnl`, `rpt_segment_profitability`, `rpt_branch_profitability` | Depends on outputs from Phases 1-2; 3-way MERGE → SQL JOINs |

#### Phase 5: Orchestration & Operations (Week 10)

| Task | Details |
|------|---------|
| Batch orchestrators | Replace `run_daily_banking.sas` and `run_daily_insurance.sas` with Databricks Workflows / Airflow DAGs |
| Error handling | Map `%GOTO ABORT` / `ABORT_ON_ERR` patterns to Workflow task dependencies and retry policies |
| Email notifications | Configure Databricks alerts or PagerDuty for exception thresholds |
| Excel exports | Python notebook with `openpyxl` for regulatory report generation |
| Control-M retirement | Decommission Control-M jobs as Databricks Workflows go live |

#### Phase 6: Validation & Cutover (Weeks 11–12)

| Task | Details |
|------|---------|
| Parallel run | Execute SAS and dbt pipelines side-by-side for 2+ weeks |
| Row-count reconciliation | Compare observation counts for all output datasets |
| Value reconciliation | Sample-based comparison of calculated fields (PD, LGD, loss ratios, profitability) |
| Performance benchmarking | Compare execution times against SAS baselines from logs |
| Macro library audit | Verify all 92 macros are either migrated, retired, or documented as unused |
| Cutover | Switch production to new platform, retain SAS read-only for 30-day rollback |

### 13.2 Migration Dependency Graph

```
Phase 0: Foundation
    │
    ├──► Phase 1.1: load_customer_accounts ◄─────────────── (foundation table)
    │         │
    │         ├──► Phase 1.2: daily_transaction_processing
    │         │         │
    │         │         └──► Phase 4.1: customer_profitability
    │         │
    │         ├──► Phase 2.1: credit_risk_scoring
    │         │         │
    │         │         └──► Phase 4.1: customer_profitability
    │         │
    │         └──► Phase 2.2: monthly_regulatory_reporting
    │
    └──► Phase 3.1: claims_processing
              │
              └──► Phase 3.2: policy_valuation
                        │
                        └──► Phase 5: Orchestration
                                  │
                                  └──► Phase 6: Validation & Cutover
```

### 13.3 Estimated Effort

| Phase | Programs | Estimated Effort | Key Challenges |
|-------|----------|------------------|----------------|
| Phase 0 | — | 2 weeks | Platform setup, connectivity |
| Phase 1 | 2 programs | 2 weeks | RETAIN → window functions, feed validation |
| Phase 2 | 2 programs | 2 weeks | Scorecard model externalization |
| Phase 3 | 2 programs | 2 weeks | Hash object → broadcast join |
| Phase 4 | 1 program | 1 week | Cross-domain joins |
| Phase 5 | 2 orchestrators | 1 week | Workflow design, alerting |
| Phase 6 | — | 2 weeks | Parallel run, reconciliation |
| **Total** | **9 programs** | **~12 weeks** | |

---

## Appendix A: SAS Construct → Migration Target Mapping

| SAS Construct | Where Used | Migration Target | Complexity |
|--------------|------------|------------------|------------|
| `DATA` step with business logic | All Programs/ | dbt SQL models or Python transforms | Medium |
| `PROC SQL` with joins, subqueries, CASE | Banking, Insurance, Reports | Databricks SQL / dbt SQL | Low |
| `%MACRO` / `%MEND` with parameters | All programs, 92 Macro/ utilities | dbt Jinja macros, Python functions | Medium |
| `PROC MEANS` / `PROC FREQ` | Reports, regulatory | SQL `GROUP BY` with aggregate functions | Low |
| `PROC APPEND` with locking | Transaction processing, risk scoring | Delta Lake `MERGE` / `INSERT INTO` | Low |
| `PROC FORMAT` (custom formats) | Formats/ directory | dbt seed tables + `CASE` expressions | Low |
| `PROC EXPORT` to Excel | Regulatory reporting, profitability | Python `openpyxl` / Databricks notebooks | Low |
| Hash objects (`declare hash`) | Claims processing | Python dicts / Spark broadcast joins | High |
| `LIBNAME` to Oracle, Teradata | `autoexec.sas` | Databricks external tables / Unity Catalog | Medium |
| `%INCLUDE` chains | Batch orchestrators | dbt `ref()` / Databricks Workflows | Low |
| `RETAIN` / `BY` group processing | Running balances | SQL window functions (`LAG`/`LEAD`/`SUM OVER`) | High |
| Macro variable resolution (`&var`) | Throughout | dbt `{{ var() }}` / Jinja templating | Low |
| Error handling (`%GOTO`, `SYSERR`) | Batch orchestrators | dbt `on-run-end` hooks / Workflows | Medium |
| Email notifications (`%sendmail`) | Exception handling | Databricks alerts / PagerDuty | Low |
| Dynamic dataset naming | Feed processing | Partitioned tables / date-filtered sources | Medium |
| `%sysfunc()` date arithmetic | Throughout | SQL `DATEADD` / `DATE_TRUNC` / dbt macros | Low |
| `calculated` keyword in PROC SQL | Regulatory, profitability | CTEs or subqueries in standard SQL | Low |
| `PROC DATASETS` cleanup | All programs | Not needed (temp tables auto-cleanup) | N/A |

---

## Appendix B: Macro Library — Full Inventory (92 files)

<details>
<summary>Click to expand full macro list</summary>

| # | Macro File | Lines | Purpose | Used By Programs | Migration Priority |
|---|-----------|-------|---------|-----------------|-------------------|
| 1 | `parmv.sas` | 359 | Parameter validation | All programs | High (convert to dbt config validation) |
| 2 | `nobs.sas` | 253 | Observation counter | All programs | High (convert to `COUNT(*)`) |
| 3 | `lock.sas` | 352 | Dataset locking | 3 banking programs | Low (retire — native platform concurrency) |
| 4 | `sendmail.sas` | 260 | Email notifications | 2 programs + 2 orchestrators | Medium (map to alerting service) |
| 5 | `export_xlsx.sas` | 101 | Excel export wrapper | 2 programs | Medium (Python openpyxl) |
| 6 | `export_dbms.sas` | — | Generic DBMS export | Called by export_xlsx | Medium |
| 7 | `hash_define.sas` | 499 | Hash object builder | Pattern used inline | High (Spark broadcast join) |
| 8 | `hash_lookup.sas` | — | Hash lookup executor | Pattern used inline | High |
| 9 | `seplist.sas` | — | Separator-delimited list builder | Called by sendmail | Low |
| 10 | `get_data_attr.sas` | — | Dataset attribute getter | Called by lock | Low |
| 11 | `handle.sas` | — | Lock handle utility | Called by lock | Low (retire) |
| 12 | `logparse.sas` | 655 | Log file parser | Operational utility | Low |
| 13–92 | *(remaining 80 utility macros)* | — | General SAS utilities | Not directly referenced by programs | Low (audit for indirect usage) |

</details>

---

*End of Migration Assessment*
