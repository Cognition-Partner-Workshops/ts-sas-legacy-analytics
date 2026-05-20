# SAS Legacy Analytics — Comprehensive Migration Assessment

> **Repo:** `ts-sas-legacy-analytics`
> **Assessment Date:** 2026-05-20
> **Target Platform:** dbt + Databricks (see `uc-data-migration-sas-to-databricks`)
> **SAS Version:** SAS 9.4 M7 on RHEL 7

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Artifact Inventory](#2-artifact-inventory)
3. [Environment Configuration (autoexec.sas)](#3-environment-configuration)
4. [Program-Level Analysis](#4-program-level-analysis)
5. [Data Lineage Diagram](#5-data-lineage-diagram)
6. [Macro Dependency Graph](#6-macro-dependency-graph)
7. [Dataset Usage Matrix](#7-dataset-usage-matrix)
8. [Format Catalog Inventory](#8-format-catalog-inventory)
9. [Batch Orchestration & Dependency Chain](#9-batch-orchestration--dependency-chain)
10. [Production Volumes & Execution Times](#10-production-volumes--execution-times)
11. [Complexity Scores](#11-complexity-scores)
12. [Risk Areas](#12-risk-areas)
13. [Recommended Migration Sequence](#13-recommended-migration-sequence)

---

## 1. Executive Summary

This SAS estate supports **daily and monthly banking and insurance analytics** for a financial institution. It comprises **7 domain programs**, **2 batch orchestrators**, **2 format catalogs**, and a **92-macro utility library**. The system reads from **Oracle DW** and **Teradata**, processes through SAS file-based staging layers, and produces curated analytical datasets and regulatory reports.

### Key Statistics

| Metric | Value |
|---|---|
| Domain Programs | 7 (4 Banking, 2 Insurance, 1 Reports) |
| Batch Orchestrators | 2 (daily banking, daily insurance) |
| Format Catalog Files | 2 (banking: 8 formats, insurance: 4 formats) |
| Macro Library | 92 files (6 directly referenced by programs) |
| LIBNAME Assignments | 12 SAS + 2 RDBMS (Oracle, Teradata) |
| External DB Connections | Oracle DW (`FINPROD.DW_BANKING`), Teradata (`tdprod.internal.corp/ANALYTICS`) |
| Scheduler | Control-M (6 job definitions) |
| Daily Data Volume | ~2.3M transactions, ~847K customer accounts |
| Cumulative Dataset | ~67M transaction records (CURATED.DAILY_TRANSACTIONS) |
| Total Estimated LOC | ~1,600 lines of SAS domain code |

---

## 2. Artifact Inventory

### 2.1 Configuration

| File | Purpose |
|---|---|
| `Config/autoexec.sas` (118 lines) | Global library assignments, DB connections, macro variables, system options, autocall paths |

### 2.2 Programs

| File | Lines | Domain | Schedule |
|---|---|---|---|
| `Programs/Banking/load_customer_accounts.sas` | 216 | Banking | Daily 06:00 (BANK_DAILY_01) |
| `Programs/Banking/daily_transaction_processing.sas` | 246 | Banking | Daily 07:30 (BANK_DAILY_02) |
| `Programs/Banking/credit_risk_scoring.sas` | 270 | Banking | Weekly Sun 02:00 (BANK_WEEKLY_01) |
| `Programs/Banking/monthly_regulatory_reporting.sas` | 199 | Banking | Monthly 3rd biz day (BANK_MONTHLY_01) |
| `Programs/Insurance/claims_processing.sas` | 238 | Insurance | Daily 08:00 (INS_DAILY_01) |
| `Programs/Insurance/policy_valuation.sas` | 206 | Insurance | Monthly 5th biz day (INS_MONTHLY_01) |
| `Programs/Reports/customer_profitability.sas` | 176 | Reporting | Monthly 10th biz day (BANK_MONTHLY_03) |

### 2.3 Batch Orchestrators

| File | Lines | Schedule |
|---|---|---|
| `BatchJobs/run_daily_banking.sas` | 161 | Daily 05:45 (BANK_MASTER) |
| `BatchJobs/run_daily_insurance.sas` | 133 | Daily 07:00 (INS_MASTER) |

### 2.4 Format Catalogs

| File | Lines | Formats Defined |
|---|---|---|
| `Formats/banking_formats.sas` | 131 | 8: `$ACCTTYPE`, `$ACCTSTAT`, `RISKRATE`, `$TXNCAT`, `DELQBKT`, `BALRANGE`, `$REGION`, `$CUSTSEG`, `$LNPURP` |
| `Formats/insurance_formats.sas` | 85 | 4: `$POLTYPE`, `$CLMSTAT`, `$RISKCAT`, `$COVTYPE`, `LOSSRANGE` |

### 2.5 Macro Library

92 macros in `Macro/`. **6 are directly `%include`'d** by domain programs:

| Macro | Used By | Purpose |
|---|---|---|
| `parmv.sas` | All 7 programs | Parameter validation (returns `&parmerr`) |
| `nobs.sas` | All 7 programs | Return observation count from dataset descriptor |
| `lock.sas` | 2 programs (txn processing, credit risk) | Dataset locking for concurrent access |
| `sendmail.sas` | 2 programs (claims, load_customer) + batch jobs | SMTP email notifications |
| `export_xlsx.sas` | 2 programs (regulatory, profitability) | Excel export via PROC EXPORT DBMS=XLSX |
| `export_dbms.sas` | (called by export_xlsx) | Generic DBMS export wrapper |

### 2.6 Logs

| File | Program | Date |
|---|---|---|
| `Logs/load_customer_accounts_20240115.log` | load_customer_accounts | 2024-01-15 |
| `Logs/daily_transaction_processing_20240115.log` | daily_transaction_processing | 2024-01-15 |

### 2.7 Other Assets

| Directory | Contents | Migration Relevance |
|---|---|---|
| `AMO/` | Excel workbooks, PowerPoint (SNUG 2013) | None — historical presentation assets |
| `EGProjects/` | SAS Enterprise Guide project (SCD2 template) | Low — template only, may inform SCD patterns |
| `Presentations/` | SNUG Q4 2016 materials | None |
| `Programs/Parent-Child-Index.sas` | Standalone utility | Low — not part of production pipelines |

---

## 3. Environment Configuration

### 3.1 LIBNAME Assignments (autoexec.sas)

```
┌─────────────────────────────────────────────────────────────────┐
│  SAS File-Based Libraries                                       │
├──────────────┬──────────────────────────┬───────────────────────┤
│ LIBNAME      │ Path                     │ Access                │
├──────────────┼──────────────────────────┼───────────────────────┤
│ RAW          │ /data/sas/raw            │ Read-only             │
│ RAW_BANK     │ /data/sas/raw/banking    │ Read-only             │
│ RAW_INS      │ /data/sas/raw/insurance  │ Read-only             │
│ STAGING      │ /data/sas/staging        │ Read-write            │
│ STG_BANK     │ /data/sas/staging/banking│ Read-write            │
│ STG_INS      │ /data/sas/staging/insurance│ Read-write          │
│ CURATED      │ /data/sas/curated        │ Read-write            │
│ REPORTS      │ /data/sas/reports        │ Read-write            │
│ ARCHIVE      │ /data/sas/archive        │ Read-write            │
│ BANKING      │ /data/sas/formats/banking│ Format catalog        │
│ INSURANCE    │ /data/sas/formats/insurance│ Format catalog       │
│ COMMON       │ /data/sas/formats/common │ Format catalog        │
├──────────────┴──────────────────────────┴───────────────────────┤
│  RDBMS Connections                                              │
├──────────────┬──────────────────────────┬───────────────────────┤
│ ORA_DW       │ Oracle: FINPROD/DW_BANKING│ Read-only, readbuff=5000│
│ TERA_DW      │ Teradata: tdprod/ANALYTICS│ Read-only, bulkload=yes│
└──────────────┴──────────────────────────┴───────────────────────┘
```

### 3.2 dbt/Databricks Mapping

| SAS LIBNAME | Layer | dbt Target Schema | Unity Catalog Mapping |
|---|---|---|---|
| `RAW` / `RAW_BANK` / `RAW_INS` | Landing | `raw` | `catalog.raw.*` (external tables) |
| `STAGING` / `STG_BANK` / `STG_INS` | Staging | `staging` | `catalog.staging.*` |
| `CURATED` | Intermediate | `intermediate` | `catalog.intermediate.*` |
| `REPORTS` | Marts | `marts` | `catalog.marts.*` |
| `ARCHIVE` | Archive | `archive` | `catalog.archive.*` |
| `ORA_DW` | Source (Oracle) | — | Databricks Lakehouse Federation or ingestion |
| `TERA_DW` | Source (Teradata) | — | Databricks Lakehouse Federation or ingestion |
| `BANKING` / `INSURANCE` | Formats | — | dbt macros or seed tables |

### 3.3 Global Macro Variables

| Variable | Value / Expression | dbt Equivalent |
|---|---|---|
| `&ENVIRONMENT` | `PROD` | `target.name` in `profiles.yml` |
| `&BASE_PATH` | `/data/sas` | N/A (Databricks storage) |
| `&LOG_PATH` | `/data/sas/logs` | Databricks job run logs |
| `&REPORT_PATH` | `/data/sas/reports/output` | DBFS or cloud storage |
| `&CURR_DT` | `%sysfunc(today(), date9.)` | `{{ run_started_at }}` or `current_date()` |
| `&CURR_YM` / `&PREV_YM` | Current/prior month | dbt `{{ var('report_month') }}` |
| `&EMAIL_DL` / `&EMAIL_ONCALL` | Distribution lists | Databricks alerting / Slack integration |
| `&MAX_OBS_WARN` | 10,000,000 | dbt test: `dbt_utils.recency` or row count check |
| `&ABORT_ON_ERR` | `Y` | dbt `on-run-end` hooks, `--fail-fast` flag |

### 3.4 System Options Migration Notes

| SAS Option | Purpose | dbt/Databricks Equivalent |
|---|---|---|
| `compress=yes` | Dataset compression | Delta Lake default compression (Snappy/ZSTD) |
| `fmtsearch=(BANKING INSURANCE COMMON)` | Format search path | dbt macro resolution order |
| `validvarname=v7` | Enforce 7-level names | Column naming conventions in `dbt_project.yml` |
| `nofmterr` | Don't error on missing formats | N/A — all logic inline in SQL |
| `mautosource` / `sasautos=` | Autocall macro paths | dbt `macro-paths` in `dbt_project.yml` |
| `yearcutoff=1920` | 2-digit year window | Explicit date parsing in Spark SQL |

---

## 4. Program-Level Analysis

### 4.1 load_customer_accounts.sas

| Attribute | Detail |
|---|---|
| **Purpose** | Daily customer account snapshot extraction, enrichment, and quality checks |
| **Data Sources** | `ORA_DW.CUST_ACCOUNTS`, `ORA_DW.CUST_DEMOGRAPHICS`, `RAW_BANK.DAILY_RATES` |
| **Outputs** | `STG_BANK.CUST_ACCOUNTS_DAILY`, `STG_BANK.ACCT_EXCEPTIONS` |
| **Macros Used** | `%parmv`, `%nobs`, `%lock`, `%sendmail` |
| **SAS Constructs** | PROC SQL (Oracle pass-through join), DATA step (business rules, conditional outputs), PROC MEANS (summary stats), PROC DATASETS, macro conditionals (`%if/%then`), `catx()`, `intck()`, multiple FORMAT references |
| **Formats Applied** | `$ACCTTYPE.`, `$ACCTSTAT.`, `RISKRATE.`, `$CUSTSEG.`, `$REGION.` |
| **Key Logic** | Derives: `ACCT_AGE_MONTHS`, `DAYS_INACTIVE`, `UTILIZATION_PCT`, `DORMANCY_FLAG`, `HIGH_BALANCE_FLAG`. Exception detection: negative balances, high utilization (>95%), missing risk ratings. Conditional email alerting when exceptions > 100. |
| **Complexity** | **Medium** |

### 4.2 daily_transaction_processing.sas

| Attribute | Detail |
|---|---|
| **Purpose** | Ingest daily transaction feed, validate, classify, compute running balances, detect anomalies |
| **Data Sources** | `RAW_BANK.TXN_FEED_YYYYMMDD` (dynamic name), `STG_BANK.CUST_ACCOUNTS_DAILY`, `CURATED.DAILY_TRANSACTIONS` (90-day lookback for stats) |
| **Outputs** | `CURATED.DAILY_TRANSACTIONS` (append), `CURATED.TXN_ANOMALIES` (append), `CURATED.RUNNING_BALANCES` |
| **Macros Used** | `%parmv`, `%nobs`, `%lock` |
| **SAS Constructs** | DATA step validation (multiple reject rules), PROC SQL (enrichment join, anomaly stats, Z-score), DATA step with **RETAIN** (running balance), **BY-group** processing (`first.ACCOUNT_ID`), PROC APPEND (incremental load), dynamic dataset naming (`%sysfunc`), `%lock` for concurrent access |
| **Formats Applied** | (Inherits from STG_BANK.CUST_ACCOUNTS_DAILY) |
| **Key Logic** | 6-step pipeline: feed validation → enrichment join → running balance (RETAIN) → Z-score anomaly detection (>3σ, overdraft, large withdrawal, orphan) → PROC APPEND to curated → persist running balances. Dynamic dataset name from date. |
| **Complexity** | **High** |

### 4.3 credit_risk_scoring.sas

| Attribute | Detail |
|---|---|
| **Purpose** | Apply approved credit risk scorecard (PD/LGD/EAD), update risk ratings, produce risk migration matrix |
| **Data Sources** | `STG_BANK.CUST_ACCOUNTS_DAILY`, `ORA_DW.BUREAU_SCORES`, `ORA_DW.PAYMENT_HISTORY`, `ORA_DW.COLLATERAL` |
| **Outputs** | `CURATED.RISK_SCORES` (append), `CURATED.RISK_MIGRATION` (append), `REPORTS.RISK_SUMMARY` |
| **Macros Used** | `%parmv`, `%nobs`, `%lock` |
| **SAS Constructs** | PROC SQL (multi-table join with correlated subquery for latest bureau score), DATA step (WOE binning, logistic regression scoring, LGD/EAD estimation), PROC APPEND, PROC MEANS, arithmetic PD calculation (`1/(1+exp(-LOG_ODDS))`), risk rating assignment |
| **Formats Applied** | (Inherits from upstream) |
| **Key Logic** | WOE (Weight of Evidence) binning for 5 features (FICO, utilization, DPD, age, LTV) → logistic score → PD/LGD/EAD → expected loss → risk rating 1-7 → migration matrix (UPGRADE/DOWNGRADE/STABLE/NEW). Hard-coded model coefficients (Model ID: CRM-2023-Q4-v2). |
| **Complexity** | **Very High** |

### 4.4 monthly_regulatory_reporting.sas

| Attribute | Detail |
|---|---|
| **Purpose** | Basel III regulatory reporting: RWA, capital adequacy, delinquency aging, loan loss provision coverage |
| **Data Sources** | `STG_BANK.CUST_ACCOUNTS_DAILY`, `CURATED.DAILY_TRANSACTIONS`, `ORA_DW.LOAN_DETAILS`, `ORA_DW.COLLATERAL` |
| **Outputs** | `REPORTS.MONTHLY_RWA`, `REPORTS.CAPITAL_ADEQUACY`, `REPORTS.DELINQUENCY_AGING`, `REPORTS.LLP_COVERAGE`, Excel: `REG_REPORT_YYYYMM.xlsx` |
| **Macros Used** | `%parmv`, `%nobs`, `%export_xlsx` |
| **SAS Constructs** | PROC SQL (4 complex queries with CASE-based risk weights, delinquency bucketing, NPL coverage), `calculated` keyword, multiple GROUP BY with computed columns, `%export_xlsx` (3 worksheets to single file) |
| **Formats Applied** | (Inherits from upstream) |
| **Key Logic** | Basel III standardized risk weights by account type and LTV → RWA aggregation → CET1/Tier1/Total capital ratios → pass/fail against minimums (4.5%/6%/8%) → delinquency aging buckets (30/60/90/120/180+) → LLP coverage ratios → multi-sheet Excel export. |
| **Complexity** | **High** |

### 4.5 claims_processing.sas

| Attribute | Detail |
|---|---|
| **Purpose** | Daily claims intake, validation against policies, fraud screening, auto-adjudication, manual review routing |
| **Data Sources** | `RAW_INS.CLAIMS_FEED_YYYYMMDD` (dynamic), `RAW_INS.POLICIES`, `TERA_DW.FRAUD_INDICATORS` |
| **Outputs** | `STG_INS.CLAIMS_REGISTER` (append), `STG_INS.CLAIMS_REVIEW_QUEUE` (append), `STG_INS.FRAUD_ALERTS` (append) |
| **Macros Used** | `%parmv`, `%nobs`, `%sendmail` |
| **SAS Constructs** | DATA step with **hash object** (`declare hash h_pol`) for policy lookup, PROC SQL (Teradata join for fraud scoring), DATA step (multi-rule auto-adjudication), PROC APPEND (3 targets), `%sendmail` (SIU fraud alerts), dynamic dataset naming |
| **Formats Applied** | `$CLMSTAT.` |
| **Key Logic** | Hash object loads active policies → validate policy existence + date coverage + amount limits → Teradata fraud score lookup → tri-level fraud risk (HIGH/MEDIUM/LOW) → auto-adjudication rules (deny high-risk, approve low-risk small/standard claims, route remainder to manual review) → SIU email alerts for high-risk claims. |
| **Complexity** | **Very High** |

### 4.6 policy_valuation.sas

| Attribute | Detail |
|---|---|
| **Purpose** | Monthly policy book valuation: in-force metrics, loss ratios, IBNR reserves, premium adequacy |
| **Data Sources** | `RAW_INS.POLICIES`, `RAW_INS.CLAIMS`, `RAW_INS.PREMIUMS`, `TERA_DW.ACTUARIAL_TABLES` |
| **Outputs** | `STG_INS.POLICY_VALUATION`, `REPORTS.LOSS_RATIO_SUMMARY`, `REPORTS.RESERVE_ADEQUACY` |
| **Macros Used** | `%parmv`, `%nobs` |
| **SAS Constructs** | PROC SQL (3 independent queries: in-force extract, claims experience, premium collections), DATA step MERGE (3-way by POLICY_ID), PROC MEANS, actuarial calculations, macro conditionals for LOB filtering |
| **Formats Applied** | `$POLTYPE.`, `$RISKCAT.` |
| **Key Logic** | Earned premium pro-rata calculation → 12-month claims window → premium collections → 3-way merge → loss ratio, combined ratio (loss + 30% expense load), IBNR estimate (15% of earned - paid), total reserve = open case + IBNR, premium adequacy flag. |
| **Complexity** | **High** |

### 4.7 customer_profitability.sas

| Attribute | Detail |
|---|---|
| **Purpose** | Customer-level P&L: interest income, fee income, ECL, operating cost allocation → segment and branch summaries |
| **Data Sources** | `STG_BANK.CUST_ACCOUNTS_DAILY`, `CURATED.DAILY_TRANSACTIONS`, `CURATED.RISK_SCORES`, `ORA_DW.COST_OF_FUNDS` |
| **Outputs** | `REPORTS.CUSTOMER_PNL`, `REPORTS.SEGMENT_PROFITABILITY`, `REPORTS.BRANCH_PROFITABILITY`, Excel: `PROFITABILITY_YYYYMM.xlsx` |
| **Macros Used** | `%parmv`, `%nobs`, `%export_xlsx` |
| **SAS Constructs** | PROC SQL (3 queries: interest income, fee income, ECL), DATA step MERGE (3-way by CUSTOMER_ID), PROC MEANS (2 summaries: by segment, by branch), `%export_xlsx` |
| **Formats Applied** | (Inherits from upstream) |
| **Key Logic** | Lending income vs deposit cost → NIM → fee income from transactions → ECL from risk scores → operating cost allocation ($15/account/month) → net profit → ROA (annualized) → profitability tier assignment → segment and branch roll-ups → Excel export. |
| **Complexity** | **Medium-High** |

---

## 5. Data Lineage Diagram

```
                    ┌─────────────────────────────────────────────────────────────────┐
                    │                    EXTERNAL SOURCES                              │
                    │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐     │
                    │  │  Oracle DW   │  │  Teradata DW  │  │  Flat File Feeds    │     │
                    │  │  (ORA_DW)    │  │  (TERA_DW)    │  │  (RAW_BANK/RAW_INS)│     │
                    │  └──────┬──────┘  └───────┬───────┘  └──────────┬──────────┘     │
                    └─────────┼─────────────────┼──────────────────────┼────────────────┘
                              │                 │                      │
          ┌───────────────────┼─────────────────┼──────────────────────┤
          │                   │                 │                      │
          ▼                   ▼                 ▼                      ▼
 ┌─────────────────┐  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐
 │ ORA_DW.         │  │ ORA_DW.     │  │ TERA_DW.     │  │ RAW_BANK.            │
 │ CUST_ACCOUNTS   │  │ BUREAU_     │  │ FRAUD_       │  │ TXN_FEED_YYYYMMDD    │
 │ CUST_DEMOGRAPHICS│ │ SCORES      │  │ INDICATORS   │  │ DAILY_RATES          │
 │ PAYMENT_HISTORY │  │ LOAN_       │  │ ACTUARIAL_   │  ├──────────────────────┤
 │ COLLATERAL      │  │ DETAILS     │  │ TABLES       │  │ RAW_INS.             │
 │ COST_OF_FUNDS   │  │             │  │              │  │ CLAIMS_FEED_YYYYMMDD │
 └────────┬────────┘  └──────┬──────┘  └──────┬───────┘  │ POLICIES, CLAIMS     │
          │                  │                │           │ PREMIUMS             │
          │                  │                │           └──────────┬───────────┘
          │                  │                │                      │
    ══════╪══════════════════╪════════════════╪══════════════════════╪═══════════
    S T A G I N G   L A Y E R                                        
          │                  │                │                      │
          ▼                  │                │                      ▼
 ┌──────────────────┐        │                │            ┌────────────────────┐
 │ STG_BANK.        │        │                │            │ STG_INS.           │
 │ CUST_ACCOUNTS_   │◄───────┼────────────────┼────────────│ CLAIMS_REGISTER    │
 │ DAILY            │        │                │            │ CLAIMS_REVIEW_QUEUE│
 │ ACCT_EXCEPTIONS  │        │                │            │ FRAUD_ALERTS       │
 └────────┬─────────┘        │                │            │ POLICY_VALUATION   │
          │                  │                │            └────────┬───────────┘
    ══════╪══════════════════╪════════════════╪════════════════════╪═══════════
    C U R A T E D   L A Y E R                                       
          │                  │                │                      │
          ▼                  ▼                │                      │
 ┌──────────────────┐  ┌──────────────┐       │                      │
 │ CURATED.         │  │ CURATED.     │       │                      │
 │ DAILY_TRANSACTIONS│ │ RISK_SCORES  │       │                      │
 │ TXN_ANOMALIES   │  │ RISK_        │       │                      │
 │ RUNNING_BALANCES │  │ MIGRATION    │       │                      │
 └────────┬─────────┘  └──────┬───────┘       │                      │
          │                   │               │                      │
    ══════╪═══════════════════╪═══════════════╪══════════════════════╪═══════════
    R E P O R T S / M A R T S   L A Y E R                            
          │                   │               │                      │
          ▼                   ▼               │                      ▼
 ┌──────────────────────────────────┐         │            ┌────────────────────┐
 │ REPORTS.                         │         │            │ REPORTS.            │
 │ CUSTOMER_PNL                     │         │            │ LOSS_RATIO_SUMMARY │
 │ SEGMENT_PROFITABILITY            │         │            │ RESERVE_ADEQUACY   │
 │ BRANCH_PROFITABILITY             │         │            └────────────────────┘
 │ MONTHLY_RWA                      │         │
 │ CAPITAL_ADEQUACY                 │         │
 │ DELINQUENCY_AGING                │         │
 │ LLP_COVERAGE                     │         │
 │ RISK_SUMMARY                     │         │
 ├──────────────────────────────────┤         │
 │ Excel Exports:                   │         │
 │  REG_REPORT_YYYYMM.xlsx         │         │
 │  PROFITABILITY_YYYYMM.xlsx      │         │
 └──────────────────────────────────┘         │
                                              │
 ┌──────────────────────────────────┐         │
 │ ARCHIVE.BATCH_HISTORY            │◄────────┘
 └──────────────────────────────────┘
```

---

## 6. Macro Dependency Graph

### 6.1 Program → Macro Dependencies

```
BatchJobs/run_daily_banking.sas
  ├── %include autoexec.sas
  ├── %sendmail (email notifications)
  └── %include (child programs 1-4):
      │
      ├── [1] load_customer_accounts.sas
      │   ├── %parmv (parameter validation)
      │   ├── %nobs (row counts)
      │   ├── %lock (dataset locking)
      │   └── %sendmail (exception alerting)
      │
      ├── [2] daily_transaction_processing.sas
      │   ├── %parmv
      │   ├── %nobs
      │   └── %lock
      │
      ├── [3] credit_risk_scoring.sas
      │   ├── %parmv
      │   ├── %nobs
      │   └── %lock
      │
      └── [4] monthly_regulatory_reporting.sas
          ├── %parmv
          ├── %nobs
          └── %export_xlsx → %export_dbms

BatchJobs/run_daily_insurance.sas
  ├── %include autoexec.sas
  ├── %sendmail
  └── %include (child programs 1-2):
      │
      ├── [1] claims_processing.sas
      │   ├── %parmv
      │   ├── %nobs
      │   └── %sendmail
      │
      └── [2] policy_valuation.sas
          ├── %parmv
          └── %nobs

Programs/Reports/customer_profitability.sas
    ├── %parmv
    ├── %nobs
    └── %export_xlsx → %export_dbms
```

### 6.2 Macro → Macro Internal Dependencies

```
%parmv ──── (standalone, no dependencies)
%nobs ───── %parmv
%lock ───── %parmv, %get_data_attr, %handle
%sendmail ─ %parmv, %seplist
%export_xlsx ── %export_dbms, %parmv
%export_dbms ── %parmv
%hash_define ── %parmv, %seplist (used indirectly in claims_processing via inline hash)
%hash_lookup ── (companion to %hash_define)
```

### 6.3 Remaining Macro Library (77 files not directly referenced)

These are general-purpose SAS utilities. Most are **not needed for migration** but should be catalogued:

**Data Manipulation:** `attrib`, `check_if_empty`, `compare`, `create_format`, `get_dups`, `guess_pk`, `subset_data`, `transpose`, `varexist`, `varlist`, `varlist2`

**String/List:** `count_words`, `dedup_mstring`, `dedup_string`, `seplist`, `splitvar`, `squote`, `format_text`, `justify`

**Date/Time:** `age`, `create_datetime_range`, `date_impute`, `sql_datetime`, `time_interval`

**I/O & Export:** `export`, `export_csv`, `export_dlm`, `export_rldx`, `export_sas`, `export_spss`, `export_stata`, `export_tab`, `export_saphari`, `excel2sas`

**Hash:** `hash_define`, `hash_lookup`, `hash_split_dataset`

**Numeric:** `align_decimals`, `IsNum`, `IsNumD`, `IsNumM`, `max_decimals`

**System/Environment:** `batch_submit`, `bench`, `create_directory`, `delete_file`, `dirlist`, `dump_mvars`, `empty`, `execpath`, `execute_macro`, `get_data_attr`, `get_lib_attr`, `get_parameters`, `get_permutations`, `getpassword`, `kill`, `libname_attr_sqlsvr`, `libname_sqlsvr`, `logparse`, `log2pdf`, `loop`, `loop_control`, `marker`, `nobs`, `optload`, `optsave`, `optval`, `pagexofy`, `randlist`, `realloc_concat_libs`, `reduce_pixel`, `stp_batch_submit`, `stp_seplist`, `stp_session`, `symget`, `txt2pdf`, `txt2rtf`, `useridToEmail`, `queryActiveDirectory`

**Orchestration:** `RunAll`, `RunAll_ControlTable`, `lock`, `handle`

---

## 7. Dataset Usage Matrix

### 7.1 Reads (R) and Writes (W)

| Dataset | load_cust | daily_txn | credit_risk | monthly_reg | claims | policy_val | cust_profit |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **ORA_DW.CUST_ACCOUNTS** | R | | | | | | |
| **ORA_DW.CUST_DEMOGRAPHICS** | R | | | | | | |
| **ORA_DW.BUREAU_SCORES** | | | R | | | | |
| **ORA_DW.PAYMENT_HISTORY** | | | R | | | | |
| **ORA_DW.COLLATERAL** | | | R | R | | | |
| **ORA_DW.LOAN_DETAILS** | | | | R | | | |
| **ORA_DW.COST_OF_FUNDS** | | | | | | | R |
| **TERA_DW.FRAUD_INDICATORS** | | | | | R | | |
| **TERA_DW.ACTUARIAL_TABLES** | | | | | | R | |
| **RAW_BANK.TXN_FEED_YYYYMMDD** | | R | | | | | |
| **RAW_BANK.DAILY_RATES** | R | | | | | | |
| **RAW_INS.CLAIMS_FEED_YYYYMMDD** | | | | | R | | |
| **RAW_INS.POLICIES** | | | | | R | R | |
| **RAW_INS.CLAIMS** | | | | | | R | |
| **RAW_INS.PREMIUMS** | | | | | | R | |
| **STG_BANK.CUST_ACCOUNTS_DAILY** | W | R | R | R | | | R |
| **STG_BANK.ACCT_EXCEPTIONS** | W | | | | | | |
| **STG_INS.CLAIMS_REGISTER** | | | | | W | | |
| **STG_INS.CLAIMS_REVIEW_QUEUE** | | | | | W | | |
| **STG_INS.FRAUD_ALERTS** | | | | | W | | |
| **STG_INS.POLICY_VALUATION** | | | | | | W | |
| **CURATED.DAILY_TRANSACTIONS** | | W(append) | | R | | | R |
| **CURATED.TXN_ANOMALIES** | | W(append) | | | | | |
| **CURATED.RUNNING_BALANCES** | | W | | | | | |
| **CURATED.RISK_SCORES** | | | W(append) | | | | R |
| **CURATED.RISK_MIGRATION** | | | W(append) | | | | |
| **REPORTS.RISK_SUMMARY** | | | W | | | | |
| **REPORTS.MONTHLY_RWA** | | | | W | | | |
| **REPORTS.CAPITAL_ADEQUACY** | | | | W | | | |
| **REPORTS.DELINQUENCY_AGING** | | | | W | | | |
| **REPORTS.LLP_COVERAGE** | | | | W | | | |
| **REPORTS.LOSS_RATIO_SUMMARY** | | | | | | W | |
| **REPORTS.RESERVE_ADEQUACY** | | | | | | W | |
| **REPORTS.CUSTOMER_PNL** | | | | | | | W |
| **REPORTS.SEGMENT_PROFITABILITY** | | | | | | | W |
| **REPORTS.BRANCH_PROFITABILITY** | | | | | | | W |
| **ARCHIVE.BATCH_HISTORY** | | | | | | | |

### 7.2 Cross-Pipeline Data Dependencies

- `STG_BANK.CUST_ACCOUNTS_DAILY` is the **keystone dataset** — written by `load_customer_accounts`, read by 4 downstream programs
- `CURATED.DAILY_TRANSACTIONS` accumulates over time (~67M rows) — append model, read by downstream reporting
- `CURATED.RISK_SCORES` — append model, read by `customer_profitability`

---

## 8. Format Catalog Inventory

### 8.1 Banking Formats → dbt Migration

| SAS Format | Type | Values | dbt Target |
|---|---|---|---|
| `$ACCTTYPE` | Character | 11 codes (CHK, SAV, MMA, CD, IRA, LOC, MTG, AUTO, PERS, CC, HELC) | Seed table `ref_account_types` or macro `account_type_label()` |
| `$ACCTSTAT` | Character | 8 codes (A, C, D, F, R, S, P, W) | Seed table `ref_account_statuses` |
| `RISKRATE` | Numeric | 7 levels (1-7) | Seed table `ref_risk_ratings` or inline CASE |
| `$TXNCAT` | Character | 10 codes (DEP, WDR, TRF, PMT, FEE, INT, ADJ, REV, CHG, REF) | Seed table `ref_transaction_categories` |
| `DELQBKT` | Numeric range | 7 buckets (Current → 180+) | dbt macro `delinquency_bucket()` (CASE expression) |
| `BALRANGE` | Numeric range | 8 ranges (Negative → $500K+) | dbt macro `balance_range()` (CASE expression) |
| `$REGION` | Character | 7 codes (NE, SE, MW, SW, W, NW, HQ) | Seed table `ref_regions` |
| `$CUSTSEG` | Character | 6 codes (RET, PREM, PB, SMB, COMM, CORP) | Seed table `ref_customer_segments` |
| `$LNPURP` | Character | 8 codes (PURCH, REFI, CASHOUT, CONST, RENO, CONSOL, EDUC, MEDIC) | Seed table `ref_loan_purposes` |

### 8.2 Insurance Formats → dbt Migration

| SAS Format | Type | Values | dbt Target |
|---|---|---|---|
| `$POLTYPE` | Character | 13 codes (WL, TL, UL, VL, AUTO, HOME, RENT, UMBR, HLTH, DNTL, VIS, DISAB, LTCI) | Seed table `ref_policy_types` |
| `$CLMSTAT` | Character | 12 codes (NEW, OPEN, INV, ADJ, PEND, APPR, DENY, PAID, CLOS, REOP, SUSP, LITI) | Seed table `ref_claim_statuses` |
| `$RISKCAT` | Character | 5 codes (STD, PREF, SPRM, SUB, DEC) | Seed table `ref_risk_categories` |
| `$COVTYPE` | Character | 9 codes (COMP, COLL, LIAB, PIP, UMBI, UMPD, MED, TOW, RENT) | Seed table `ref_coverage_types` |
| `LOSSRANGE` | Numeric range | 7 ranges (Recovery → $500K+) | dbt macro `loss_range()` |

---

## 9. Batch Orchestration & Dependency Chain

### 9.1 Daily Banking Pipeline (BANK_MASTER — 05:45)

```
Control-M: BANK_MASTER (05:45 daily)
│
└── run_daily_banking.sas
    │
    ├── Step 1: load_customer_accounts.sas    (BANK_DAILY_01, 06:00)
    │   └── Outputs: STG_BANK.CUST_ACCOUNTS_DAILY, STG_BANK.ACCT_EXCEPTIONS
    │
    ├── Step 2: daily_transaction_processing.sas (BANK_DAILY_02, 07:30)
    │   ├── Depends: Step 1 (reads STG_BANK.CUST_ACCOUNTS_DAILY)
    │   └── Outputs: CURATED.DAILY_TRANSACTIONS, CURATED.TXN_ANOMALIES, CURATED.RUNNING_BALANCES
    │
    ├── Step 3: credit_risk_scoring.sas        (BANK_WEEKLY_01, Sun 02:00)
    │   ├── Depends: Step 1 (reads STG_BANK.CUST_ACCOUNTS_DAILY)
    │   └── Outputs: CURATED.RISK_SCORES, CURATED.RISK_MIGRATION, REPORTS.RISK_SUMMARY
    │
    └── Step 4: monthly_regulatory_reporting.sas (BANK_MONTHLY_01)
        ├── Depends: Steps 1-2 (reads STG_BANK + CURATED)
        └── Outputs: REPORTS.{MONTHLY_RWA, CAPITAL_ADEQUACY, DELINQUENCY_AGING, LLP_COVERAGE}
                     + REG_REPORT_YYYYMM.xlsx
```

> **Note:** Steps 3 & 4 have different standalone schedules (weekly/monthly) but are also included in the daily master. This allows the master to support ad-hoc full re-runs. In production, the Control-M schedule gates determine actual execution.

### 9.2 Daily Insurance Pipeline (INS_MASTER — 07:00)

```
Control-M: INS_MASTER (07:00 daily)
│
└── run_daily_insurance.sas
    │
    ├── Step 1: claims_processing.sas          (INS_DAILY_01, 08:00)
    │   └── Outputs: STG_INS.{CLAIMS_REGISTER, CLAIMS_REVIEW_QUEUE, FRAUD_ALERTS}
    │
    └── Step 2: policy_valuation.sas           (INS_MONTHLY_01)
        ├── Depends: Step 1 (reads RAW_INS tables, not Step 1 outputs directly)
        └── Outputs: STG_INS.POLICY_VALUATION, REPORTS.{LOSS_RATIO_SUMMARY, RESERVE_ADEQUACY}
```

### 9.3 Cross-Pipeline Dependencies (Monthly)

```
customer_profitability.sas (BANK_MONTHLY_03, 10th biz day)
├── Depends: STG_BANK.CUST_ACCOUNTS_DAILY  ← from daily banking Step 1
├── Depends: CURATED.DAILY_TRANSACTIONS     ← from daily banking Step 2
├── Depends: CURATED.RISK_SCORES            ← from banking Step 3
└── Depends: ORA_DW.COST_OF_FUNDS           ← external Oracle
```

### 9.4 Orchestration Features

| Feature | SAS Implementation | dbt/Databricks Equivalent |
|---|---|---|
| Sequential step execution | `%run_step` macro with `%include` | `dbt run --select +model_name` (DAG-based) |
| Error handling & abort | `ABORT_ON_ERR=Y`, `SYSCC` checking | `--fail-fast` flag, `on-run-end` hooks |
| Restart from step N | `restart_from=` parameter | `dbt retry` or tag-based selection |
| Batch ID tracking | `BATCH_CONTROL` dataset → `ARCHIVE.BATCH_HISTORY` | dbt artifacts (`run_results.json`), Databricks job run metadata |
| Email notifications | `%sendmail` macro (SMTP) | Databricks Notifications, Slack/PagerDuty integrations |
| Execution timing | `%sysfunc(datetime())` tracking | dbt run timing in `run_results.json` |

---

## 10. Production Volumes & Execution Times

### 10.1 load_customer_accounts (2024-01-15)

| Metric | Value |
|---|---|
| Source records (ACCT_RAW) | **847,293** rows × 22 columns |
| Output (CUST_ACCOUNTS_DAILY) | 847,293 rows × 30 columns |
| Exceptions detected | 1,247 |
| Oracle extract (PROC SQL) | 2 min 14 sec real / 1 min 49 sec CPU |
| DATA step (business rules) | 32 sec real / 28 sec CPU |
| PROC MEANS (summary) | 8 sec real / 7 sec CPU |
| **Total Duration** | **2 min 56 sec** |

### 10.2 daily_transaction_processing (2024-01-15)

| Metric | Value |
|---|---|
| Feed records (TXN_FEED) | **2,341,567** rows × 18 columns |
| Validated transactions | 2,338,912 (99.89% pass rate) |
| Rejected transactions | 2,655 (0.11%) |
| Enriched records | 2,338,912 rows × 25 columns |
| Statistical base (90-day) | 423,891 accounts |
| Anomalies detected | 3,421 |
| Cumulative dataset size | **67,234,891** rows (CURATED.DAILY_TRANSACTIONS) |
| Feed validation (DATA step) | 1 min 12 sec real / 59 sec CPU |
| Enrichment (PROC SQL join) | 3 min 45 sec real / 2 min 57 sec CPU |
| PROC APPEND | 45 sec real / 35 sec CPU |
| Running balance persist | 53 sec real / 41 sec CPU |
| **Total Duration** | **6 min 49 sec** |

### 10.3 Volume Growth Projections

| Dataset | Current Size | Est. Daily Growth | 1-Year Projection |
|---|---|---|---|
| CURATED.DAILY_TRANSACTIONS | 67.2M rows | ~2.3M/day | ~907M rows |
| STG_BANK.CUST_ACCOUNTS_DAILY | 847K rows | Full refresh | 847K (snapshot) |
| STG_INS.CLAIMS_REGISTER | Unknown | Append | Depends on claims volume |
| CURATED.RISK_SCORES | Unknown | ~847K/week | ~44M rows/year |

---

## 11. Complexity Scores

| Program | Complexity | Score (1-5) | Key Complexity Drivers |
|---|---|---|---|
| `load_customer_accounts` | **Medium** | 2.5 | Oracle join, business rule DATA step, conditional email alerts |
| `daily_transaction_processing` | **High** | 4.0 | RETAIN running balance, Z-score anomaly detection, PROC APPEND concurrency, dynamic dataset names |
| `credit_risk_scoring` | **Very High** | 4.5 | WOE binning, logistic regression, PD/LGD/EAD models, risk migration matrix, hard-coded coefficients |
| `monthly_regulatory_reporting` | **High** | 3.5 | Basel III risk weights, complex PROC SQL with `calculated` keyword, multi-sheet Excel export |
| `claims_processing` | **Very High** | 4.5 | Hash object lookup, Teradata fraud scoring, multi-rule auto-adjudication, SIU alerting |
| `policy_valuation` | **High** | 3.5 | Actuarial calcs (IBNR, loss ratio, combined ratio), 3-way MERGE, earned premium pro-rata |
| `customer_profitability` | **Medium-High** | 3.0 | Multi-source P&L assembly, 3-way MERGE, profitability tiering, segment rollups |
| `run_daily_banking` | **Medium** | 2.5 | Orchestration with error handling, restart capability, control table tracking |
| `run_daily_insurance` | **Medium** | 2.0 | Simpler orchestration (2 steps) |

### Complexity Rating Criteria

| Score | Rating | Description |
|---|---|---|
| 1.0-1.5 | Low | Simple extracts, basic transformations, no complex SAS constructs |
| 2.0-2.5 | Medium | PROC SQL joins, standard DATA step logic, format application |
| 3.0-3.5 | High | Multi-step pipelines, complex business logic, PROC MEANS aggregations, merges |
| 4.0-4.5 | Very High | RETAIN/running balance, hash objects, statistical models, regulatory calculations |
| 5.0 | Critical | Machine learning models, complex array processing, SAS/IML, ODS output |

---

## 12. Risk Areas

### 12.1 High-Risk Migration Items

| Risk | Severity | Programs Affected | Mitigation |
|---|---|---|---|
| **RETAIN / Running Balance** | 🔴 High | `daily_transaction_processing` | Convert to Spark SQL `SUM() OVER (PARTITION BY ... ORDER BY ...)` window function. Requires careful ordering semantics. |
| **Hash Object Lookup** | 🔴 High | `claims_processing` | Convert to broadcast join in Spark or dbt `ref()` join. Validate cardinality assumptions. |
| **WOE Binning + Logistic Scoring** | 🔴 High | `credit_risk_scoring` | Migrate coefficients to dbt macro or config YAML. PD formula `1/(1+exp(-x))` maps to Spark `1/(1+exp(-x))`. Must preserve exact numeric precision. |
| **Dynamic Dataset Names** | 🟡 Medium | `daily_transaction_processing`, `claims_processing` | Replace `TXN_FEED_YYYYMMDD` pattern with partitioned Delta table or `WHERE date_col = ...` filter. |
| **PROC APPEND (Incremental Load)** | 🟡 Medium | 4 programs | Convert to dbt incremental model with `merge` strategy on natural keys. |
| **Multi-Dataset MERGE** | 🟡 Medium | `policy_valuation`, `customer_profitability` | Convert to SQL LEFT JOINs. Verify one-to-one merge assumptions (no unexpected duplicates). |
| **SAS Date Literals** | 🟡 Medium | All programs | `"15JAN2024"d` → `DATE '2024-01-15'`. Standardize date handling. |
| **Macro Conditional Logic** | 🟡 Medium | All programs | `%if &region ne ALL %then` → dbt Jinja: `{% if var('region') != 'ALL' %}`. |
| **Excel Export** | 🟡 Medium | `monthly_regulatory_reporting`, `customer_profitability` | Replace `%export_xlsx` with Databricks notebook export or DBFS file write + downstream BI tool. |
| **Dataset Locking (%lock)** | 🟡 Medium | `daily_transaction_processing`, `credit_risk_scoring` | Not needed in Databricks — Delta Lake provides ACID transactions natively. |
| **Email Alerting (%sendmail)** | 🟢 Low | `claims_processing`, `load_customer_accounts`, batch jobs | Replace with Databricks job email notifications or Slack webhooks via dbt `on-run-end`. |
| **PROC MEANS → Summary Stats** | 🟢 Low | `load_customer_accounts`, `credit_risk_scoring`, `policy_valuation`, `customer_profitability` | Direct translation to `GROUP BY` with aggregate functions in dbt SQL models. |
| **Format Application** | 🟢 Low | All programs | Seed tables + join, or dbt macros returning CASE expressions. |

### 12.2 Data Validation Risks

| Risk | Detail |
|---|---|
| **Numeric precision** | SAS uses 8-byte floating point. Spark SQL uses DOUBLE or DECIMAL. Financial calculations (PD, LGD, EAD, loss ratios) require parity testing with `DECIMAL(18,8)` or similar. |
| **Date handling** | SAS dates are integer days since 1960-01-01. Spark uses `DATE` type (days since epoch). All date arithmetic (`intck`, `intnx`) must be validated. |
| **Missing value semantics** | SAS `.` (numeric missing) behaves differently in comparisons and arithmetic vs SQL `NULL`. Every `coalesce()` and null-handling pattern must be reviewed. |
| **Sort order** | SAS `BY` processing depends on pre-sorted data. Spark SQL `ORDER BY` in window functions must match exactly. |
| **Character padding** | SAS fixed-length character variables may have trailing spaces. Spark STRING type does not. Affects joins and comparisons. |

### 12.3 External Dependency Risks

| Dependency | Risk | Mitigation |
|---|---|---|
| **Oracle DW (7 tables)** | Connection method changes | Use Databricks Lakehouse Federation or scheduled ingestion via ADF/Fivetran |
| **Teradata DW (2 tables)** | Connection method changes | Use Databricks Lakehouse Federation or Teradata connector |
| **Control-M Scheduler** | Orchestration replacement | Databricks Workflows or Apache Airflow |
| **SMTP Email** | Notification mechanism | Databricks Alerts, Slack integration, or PagerDuty |
| **File-based SAS datasets** | Storage format change | Delta Lake tables (Parquet-based, ACID transactions) |
| **SAS Format Catalogs** | Proprietary binary format | dbt seed CSVs + join-based lookups |

---

## 13. Recommended Migration Sequence

### Phase 0: Foundation (Week 1-2)

**Objective:** Establish dbt project scaffolding and reference data.

| Step | Task | Deliverable |
|---|---|---|
| 0.1 | Set up dbt project with Databricks profile | `dbt_project.yml`, `profiles.yml` |
| 0.2 | Create Unity Catalog schemas: `raw`, `staging`, `intermediate`, `marts`, `archive` | Schema DDL |
| 0.3 | Migrate all format catalogs → dbt seed CSVs | `seeds/ref_account_types.csv`, etc. (13 seed files) |
| 0.4 | Create dbt macros for range-based formats | `macros/delinquency_bucket.sql`, `macros/balance_range.sql`, `macros/loss_range.sql` |
| 0.5 | Migrate `%parmv` validation patterns → dbt schema tests | `schema.yml` with `accepted_values`, `not_null`, `relationships` |
| 0.6 | Set up source ingestion for Oracle DW / Teradata tables | `models/staging/sources.yml` |

### Phase 1: Staging Layer (Week 3-4)

**Objective:** Migrate data ingestion and basic transformations.

| Step | Program | dbt Model(s) | Priority |
|---|---|---|---|
| 1.1 | `load_customer_accounts.sas` | `stg_cust_accounts_daily.sql`, `stg_acct_exceptions.sql` | **P1 — Critical path** (4 downstream dependents) |
| 1.2 | Source tables materialization | `stg_oracle_*`, `stg_teradata_*` | **P1** |

**Key translations:**
- Oracle PROC SQL → dbt source ref + SQL model
- Business rule DATA step → CASE expressions in SQL
- `intck('month', ...)` → `DATEDIFF(MONTH, ...)`
- Format application → JOIN to seed table or macro call
- `%nobs` validation → dbt `dbt_utils.at_least_one` test

### Phase 2: Transaction Processing (Week 5-7)

**Objective:** Migrate the most complex daily pipeline.

| Step | Program | dbt Model(s) | Priority |
|---|---|---|---|
| 2.1 | `daily_transaction_processing.sas` — validation | `stg_txn_validated.sql`, `stg_txn_rejected.sql` | **P1** |
| 2.2 | `daily_transaction_processing.sas` — enrichment | `int_txn_enriched.sql` | **P1** |
| 2.3 | `daily_transaction_processing.sas` — running balance | `int_txn_running_balance.sql` (window function) | **P1 — Highest risk** |
| 2.4 | `daily_transaction_processing.sas` — anomaly detection | `int_txn_anomalies.sql` | **P1** |
| 2.5 | `daily_transaction_processing.sas` — curated append | `daily_transactions.sql` (incremental) | **P1** |

**Key translations:**
- `RETAIN RUNNING_BALANCE` → `SUM(signed_amount) OVER (PARTITION BY account_id ORDER BY txn_date, txn_id ROWS UNBOUNDED PRECEDING)`
- Dynamic dataset name → partition filter or incremental materialization
- `%lock` → not needed (Delta ACID)
- `PROC APPEND` → dbt incremental model with `merge` or `append` strategy

### Phase 3: Insurance Pipeline (Week 7-9)

**Objective:** Migrate claims processing with hash object translation.

| Step | Program | dbt Model(s) | Priority |
|---|---|---|---|
| 3.1 | `claims_processing.sas` — validation | `stg_claims_validated.sql` | **P2** |
| 3.2 | `claims_processing.sas` — fraud screening | `int_claims_fraud_check.sql` | **P2** |
| 3.3 | `claims_processing.sas` — adjudication | `int_claims_adjudicated.sql`, `int_claims_review_queue.sql`, `int_fraud_alerts.sql` | **P2** |
| 3.4 | `policy_valuation.sas` | `int_policy_valuation.sql`, `marts_loss_ratio_summary.sql` | **P2** |

**Key translations:**
- Hash object (`declare hash h_pol`) → SQL INNER/LEFT JOIN
- Teradata fraud join → source ingestion + dbt join
- Auto-adjudication rules → CASE/WHEN cascade
- IBNR estimate → SQL expression: `GREATEST(0, earned_premium * 0.15 - COALESCE(total_paid, 0))`

### Phase 4: Risk & Regulatory (Week 9-12)

**Objective:** Migrate scorecard model and regulatory reporting.

| Step | Program | dbt Model(s) | Priority |
|---|---|---|---|
| 4.1 | `credit_risk_scoring.sas` — feature assembly | `int_risk_score_input.sql` | **P2** |
| 4.2 | `credit_risk_scoring.sas` — WOE + scoring | `int_risk_scored.sql` + `macros/woe_binning.sql` | **P2 — High complexity** |
| 4.3 | `credit_risk_scoring.sas` — migration matrix | `int_risk_migration.sql` | **P2** |
| 4.4 | `monthly_regulatory_reporting.sas` | `marts_monthly_rwa.sql`, `marts_capital_adequacy.sql`, `marts_delinquency_aging.sql`, `marts_llp_coverage.sql` | **P2** |

**Key translations:**
- WOE binning → dbt macro generating CASE expressions per feature
- `PD = 1 / (1 + exp(-LOG_ODDS))` → `1.0 / (1.0 + EXP(-log_odds))` in Spark SQL
- Risk weights → dbt macro or config variable
- `%export_xlsx` → downstream BI tool (e.g., Power BI connecting to marts)

### Phase 5: Reporting & Profitability (Week 12-14)

**Objective:** Migrate reporting marts and profitability model.

| Step | Program | dbt Model(s) | Priority |
|---|---|---|---|
| 5.1 | `customer_profitability.sas` | `marts_customer_pnl.sql`, `marts_segment_profitability.sql`, `marts_branch_profitability.sql` | **P3** |
| 5.2 | Excel exports | Replace with BI tool connections to marts | **P3** |

### Phase 6: Orchestration & Validation (Week 14-16)

| Step | Task | Priority |
|---|---|---|
| 6.1 | Configure Databricks Workflows to replicate Control-M schedule | **P1** |
| 6.2 | Implement alerting (Slack/email) for anomaly counts, failures | **P2** |
| 6.3 | Build validation framework: SAS vs dbt row counts, aggregates, sample comparisons | **P1** |
| 6.4 | Parallel run period (SAS + dbt) with daily reconciliation | **P1** |
| 6.5 | Decommission SAS jobs and redirect consumers | **P3** |

### Migration Effort Summary

| Phase | Programs | Estimated dbt Models | Effort (weeks) | Risk |
|---|---|---|---|---|
| 0 — Foundation | — | Seeds (13), Macros (3) | 2 | Low |
| 1 — Staging | 1 | 3 | 2 | Low-Medium |
| 2 — Transactions | 1 | 5 | 3 | **High** |
| 3 — Insurance | 2 | 6 | 3 | High |
| 4 — Risk & Regulatory | 2 | 7 | 4 | **Very High** |
| 5 — Reporting | 1 | 3 | 2 | Medium |
| 6 — Orchestration | 2 batch jobs | — | 2 | Medium |
| **Total** | **9** | **~37 models + 13 seeds + 6 macros** | **~16 weeks** | |

---

## Appendix A: SAS Construct → dbt/Spark SQL Translation Quick Reference

| SAS Construct | Usage Count | dbt/Spark SQL Equivalent |
|---|---|---|
| `PROC SQL` | 14 instances | Native SQL model |
| `DATA step` (basic) | 12 instances | SQL `SELECT ... CASE ... FROM` |
| `DATA step` + `RETAIN` | 1 instance | Window function `SUM() OVER (... ROWS UNBOUNDED PRECEDING)` |
| `DATA step` + Hash Object | 1 instance | `LEFT JOIN` (with broadcast hint for small tables) |
| `DATA step MERGE` | 3 instances | SQL `LEFT JOIN` on merge key |
| `PROC MEANS` | 5 instances | `GROUP BY` + aggregate functions |
| `PROC APPEND` | 6 instances | dbt incremental model (`merge` or `append` strategy) |
| `PROC FORMAT` | 2 catalogs | dbt seed CSVs or Jinja macros |
| `PROC DATASETS` | 7 instances | N/A (dbt manages table lifecycle) |
| `PROC PRINT` | 2 instances | N/A (replaced by BI/notebook output) |
| `%include` | 9 instances | dbt `ref()` / `source()` DAG |
| `%let` / `%sysfunc` | ~30 instances | dbt `{{ var() }}` / Jinja expressions |
| `%if/%then/%do` | ~10 instances | Jinja `{% if %}` blocks |
| `%macro/%mend` | 9 macros | dbt macros (`{% macro %}`) |
| `intck()` / `intnx()` | ~12 instances | `DATEDIFF()` / `DATE_ADD()` / `ADD_MONTHS()` |
| `catx()` | ~8 instances | `CONCAT_WS()` |
| `coalesce()` | ~5 instances | `COALESCE()` (same) |
| `put()` with format | ~10 instances | `CAST()` + `FORMAT_NUMBER()` or join to ref table |

## Appendix B: Related Repositories

| Repository | Relationship |
|---|---|
| `uc-data-migration-sas-to-databricks` | **Target** — dbt project structure, staging/intermediate/mart models, macro examples for SAS format migration |
| `uc-data-migration-sas-to-snowflake` | **Reference** — Snowflake-targeted validation toolkit |
| `platform-engineering-shared-services` | **Infrastructure** — PostgreSQL banking demo DB (may serve as test data source) |
