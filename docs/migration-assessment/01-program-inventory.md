# SAS Program Inventory

Detailed catalog of every SAS program in the estate with classification, dependencies, and migration notes.

---

## Business Programs

### Banking Domain

#### 1. `Programs/Banking/load_customer_accounts.sas`
| Attribute | Detail |
|-----------|--------|
| **Purpose** | Daily customer account snapshot from Oracle DW |
| **Lines of Code** | 216 |
| **Schedule** | Daily 06:00 — Control-M `BANK_DAILY_01` |
| **Batch Step** | `run_daily_banking` Step 1 |
| **Inputs** | `ORA_DW.CUST_ACCOUNTS`, `ORA_DW.CUST_DEMOGRAPHICS`, `RAW_BANK.DAILY_RATES` |
| **Outputs** | `STG_BANK.CUST_ACCOUNTS_DAILY`, `STG_BANK.ACCT_EXCEPTIONS` |
| **SAS Constructs** | PROC SQL (Oracle pass-through join), DATA step (business rules, derived fields), PROC MEANS (summary stats), `%parmv`, `%nobs`, `%lock`, `%sendmail`, PROC DATASETS |
| **Formats Used** | `$ACCTTYPE`, `$ACCTSTAT`, `RISKRATE`, `$CUSTSEG`, `$REGION` |
| **Business Logic** | Account age, days inactive, utilization ratio, dormancy flag, high-balance flag, exception detection (negative balance, high utilization, missing risk rating) |
| **Macro Parameters** | `run_date=`, `region=` (filterable by region code) |
| **Error Handling** | `%GOTO EXIT` on zero records, email on >100 exceptions |
| **Production Volume** | 847,293 accounts/day, 1,247 exceptions (per 2024-01-15 log) |
| **Runtime** | ~2m55s |
| **Migration Complexity** | **Low-Medium** — Straightforward SQL extract + DATA step derivations map cleanly to dbt SQL |
| **dbt Coverage** | `stg_cust_accounts` exists (partial) |

#### 2. `Programs/Banking/daily_transaction_processing.sas`
| Attribute | Detail |
|-----------|--------|
| **Purpose** | Transaction feed ingest, validation, enrichment, running balance, anomaly detection |
| **Lines of Code** | 246 |
| **Schedule** | Daily 07:30 — Control-M `BANK_DAILY_02` |
| **Batch Step** | `run_daily_banking` Step 2 |
| **Depends On** | `load_customer_accounts.sas` (Step 1 output) |
| **Inputs** | `RAW_BANK.TXN_FEED_YYYYMMDD` (daily flat file), `STG_BANK.CUST_ACCOUNTS_DAILY`, `CURATED.DAILY_TRANSACTIONS` (90-day lookback) |
| **Outputs** | `CURATED.DAILY_TRANSACTIONS`, `CURATED.TXN_ANOMALIES`, `CURATED.RUNNING_BALANCES` |
| **SAS Constructs** | DATA step (validation, rejection routing), PROC SQL (enrichment join, anomaly stats), `RETAIN` + `BY` group (running balance), `PROC APPEND` with `%lock`, Z-score anomaly detection |
| **Formats Used** | `$TXNCAT` (implicit via enrichment) |
| **Business Logic** | 5 validation rules (missing fields, amount threshold, valid type, future-date), transaction enrichment via account join, running balance via RETAIN, Z-score anomaly detection (>3σ), overdraft detection, large withdrawal flag, orphan account detection |
| **Macro Parameters** | `txn_date=` |
| **Error Handling** | `%GOTO ABORT` on missing feed dataset |
| **Production Volume** | 2.3M transactions/day, 2,655 rejected, 3,421 anomalies (per log) |
| **Runtime** | ~6m48s |
| **Migration Complexity** | **High** — RETAIN-based running balance requires Spark window functions; PROC APPEND with locking maps to Delta Lake MERGE; Z-score anomaly detection needs careful SQL translation |
| **dbt Coverage** | `stg_daily_transactions`, `mart_daily_transactions`, `mart_transaction_anomalies` exist (partial) |

#### 3. `Programs/Banking/credit_risk_scoring.sas`
| Attribute | Detail |
|-----------|--------|
| **Purpose** | Apply approved credit risk scorecard (PD/LGD/EAD), update risk ratings, produce migration matrix |
| **Lines of Code** | 270 |
| **Schedule** | Weekly Sunday 02:00 — Control-M `BANK_WEEKLY_01` |
| **Batch Step** | `run_daily_banking` Step 3 |
| **Inputs** | `STG_BANK.CUST_ACCOUNTS_DAILY`, `ORA_DW.BUREAU_SCORES`, `ORA_DW.PAYMENT_HISTORY`, `ORA_DW.COLLATERAL` |
| **Outputs** | `CURATED.RISK_SCORES`, `CURATED.RISK_MIGRATION`, `REPORTS.RISK_SUMMARY` |
| **SAS Constructs** | PROC SQL (4-way join with correlated subquery for latest bureau score), DATA step (WOE binning, logistic regression scoring, PD/LGD/EAD estimation), `PROC APPEND` with `%lock`, `PROC MEANS` (risk summary) |
| **Formats Used** | None directly (implicit via account data) |
| **Business Logic** | Weight-of-Evidence (WOE) binning for 5 features (FICO, utilization, payment history, account age, LTV), logistic regression with hardcoded coefficients (Model `CRM-2023-Q4-v2`), PD calculation, LGD estimation by product type, EAD with credit conversion factor, expected loss = PD × LGD × EAD, risk rating assignment (1-7 scale), risk migration matrix (upgrade/downgrade/stable/new) |
| **Macro Parameters** | `score_date=`, `model_id=` |
| **Production Volume** | Not in logs (weekly job) |
| **Migration Complexity** | **High** — WOE binning logic and model coefficients must be ported exactly for regulatory parity. Risk migration matrix requires careful window function design |
| **dbt Coverage** | `mart_risk_scores` exists (partial) |

#### 4. `Programs/Banking/monthly_regulatory_reporting.sas`
| Attribute | Detail |
|-----------|--------|
| **Purpose** | Basel III regulatory aggregations: RWA, capital adequacy, delinquency aging, LLP coverage, Excel export |
| **Lines of Code** | 199 |
| **Schedule** | Monthly 3rd business day — Control-M `BANK_MONTHLY_01` |
| **Batch Step** | `run_daily_banking` Step 4 |
| **Inputs** | `STG_BANK.CUST_ACCOUNTS_DAILY`, `ORA_DW.LOAN_DETAILS`, `ORA_DW.COLLATERAL`, `CURATED.DAILY_TRANSACTIONS` |
| **Outputs** | `REPORTS.MONTHLY_RWA`, `REPORTS.CAPITAL_ADEQUACY`, `REPORTS.DELINQUENCY_AGING`, `REPORTS.LLP_COVERAGE`, Excel file (`REG_REPORT_YYYYMM.xlsx`) |
| **SAS Constructs** | PROC SQL (RWA with Basel risk weights, delinquency bucketing, LLP coverage, capital ratios), `%export_xlsx` (3 sheets) |
| **Business Logic** | Basel III standardized risk weights by product/LTV, delinquency aging buckets (Current through 180+), loan loss provision coverage ratios, capital adequacy ratios (CET1, Tier 1, Total Capital) with pass/fail against minimums (4.5%/6%/8%), NPL coverage |
| **Macro Parameters** | `report_month=` |
| **Migration Complexity** | **Medium** — Pure SQL aggregation maps well to dbt; Excel export requires Databricks notebook or Python openpyxl |
| **dbt Coverage** | None |

### Insurance Domain

#### 5. `Programs/Insurance/claims_processing.sas`
| Attribute | Detail |
|-----------|--------|
| **Purpose** | Claims intake, policy validation, fraud screening, auto-adjudication |
| **Lines of Code** | 238 |
| **Schedule** | Daily 08:00 — Control-M `INS_DAILY_01` |
| **Batch Step** | `run_daily_insurance` Step 1 |
| **Inputs** | `RAW_INS.CLAIMS_FEED_YYYYMMDD`, `RAW_INS.POLICIES`, `TERA_DW.FRAUD_INDICATORS` |
| **Outputs** | `STG_INS.CLAIMS_REGISTER`, `STG_INS.CLAIMS_REVIEW_QUEUE`, `STG_INS.FRAUD_ALERTS` |
| **SAS Constructs** | `declare hash` (policy lookup), DATA step (validation, auto-adjudication rules), PROC SQL (fraud screening join to Teradata), `PROC APPEND`, `%sendmail` (SIU fraud alerts) |
| **Formats Used** | `$POLTYPE`, `$CLMSTAT`, `$RISKCAT`, `$COVTYPE` |
| **Business Logic** | Hash-based policy lookup for existence/active check, loss date within policy period validation, claim amount vs sum insured check, fraud scoring (HIGH/MEDIUM/LOW tiers), auto-adjudication rules (deny if high fraud risk, auto-approve if low risk + small claim + qualifying product, auto-approve if within 25% of sum insured), deductible application, manual review routing, SIU alert generation |
| **Macro Parameters** | `proc_date=` |
| **Error Handling** | `%GOTO ABORT` on missing feed, email on fraud alerts |
| **Migration Complexity** | **High** — Hash object must become broadcast join; auto-adjudication decision tree needs careful SQL CASE WHEN nesting; fraud screening depends on Teradata connection |
| **dbt Coverage** | None |

#### 6. `Programs/Insurance/policy_valuation.sas`
| Attribute | Detail |
|-----------|--------|
| **Purpose** | Monthly policy book valuation: premiums, loss ratios, IBNR reserves |
| **Lines of Code** | 206 |
| **Schedule** | Monthly 5th business day — Control-M `INS_MONTHLY_01` |
| **Batch Step** | `run_daily_insurance` Step 2 |
| **Inputs** | `RAW_INS.POLICIES`, `RAW_INS.CLAIMS`, `RAW_INS.PREMIUMS`, `TERA_DW.ACTUARIAL_TABLES` |
| **Outputs** | `STG_INS.POLICY_VALUATION`, `REPORTS.LOSS_RATIO_SUMMARY`, `REPORTS.RESERVE_ADEQUACY` |
| **SAS Constructs** | PROC SQL (in-force extraction, claims experience, premium collections), DATA step `MERGE` (3-way merge by POLICY_ID), PROC MEANS (loss ratio summary) |
| **Formats Used** | `$POLTYPE`, `$RISKCAT` |
| **Business Logic** | In-force policy extraction with earned premium pro-rata calculation, 12-month claims experience window, premium collection tracking, loss ratio = incurred/earned, combined ratio = loss ratio + 30% expense load, IBNR estimate = 15% of earned − paid, total reserve = open case reserves + IBNR, premium adequacy flag, renewal due flag |
| **Macro Parameters** | `val_date=`, `lob=` (filterable by line of business) |
| **Migration Complexity** | **Medium** — Three-way merge maps to SQL JOINs; IBNR and loss ratio are straightforward calculations; Teradata actuarial table connection needs replanning |
| **dbt Coverage** | None |

### Reporting Domain

#### 7. `Programs/Reports/customer_profitability.sas`
| Attribute | Detail |
|-----------|--------|
| **Purpose** | Customer P&L: interest income, fee income, ECL, operating cost, profitability tiers |
| **Lines of Code** | 176 |
| **Schedule** | Monthly 10th business day — Control-M `BANK_MONTHLY_03` |
| **Inputs** | `STG_BANK.CUST_ACCOUNTS_DAILY`, `CURATED.DAILY_TRANSACTIONS`, `CURATED.RISK_SCORES`, `ORA_DW.COST_OF_FUNDS` |
| **Outputs** | `REPORTS.CUSTOMER_PNL`, `REPORTS.SEGMENT_PROFITABILITY`, `REPORTS.BRANCH_PROFITABILITY`, Excel file (`PROFITABILITY_YYYYMM.xlsx`) |
| **SAS Constructs** | PROC SQL (interest income, fee income, ECL aggregation), DATA step `MERGE` (P&L assembly), PROC MEANS (segment/branch summaries), `%export_xlsx` |
| **Business Logic** | Lending income vs deposit cost, net interest income, fee income from transactions, expected credit loss allocation, operating cost ($15/account/month), ROA calculation, profitability tier assignment (Highly Profitable/Profitable/Marginal/Unprofitable) |
| **Macro Parameters** | `report_month=` |
| **Migration Complexity** | **Medium** — Pure SQL aggregation and merge logic; Excel export needs Databricks/Python alternative |
| **dbt Coverage** | None |

### Utility

#### 8. `Programs/Parent-Child-Index.sas`
| Attribute | Detail |
|-----------|--------|
| **Purpose** | Hierarchical account rollup using recursive key lookups and dimensional modeling |
| **Lines of Code** | 286 |
| **Schedule** | Ad-hoc |
| **SAS Constructs** | DATA step with `SET key=` (recursive index lookup), `PROC SUMMARY`, `PROC CONTENTS`, `PROC SQL` (dynamic code generation), `%seplist` macro, array processing, snowflake schema dimensional model |
| **Migration Complexity** | **Medium** — Recursive hierarchy traversal maps to Databricks recursive CTEs or Python UDFs |
| **dbt Coverage** | None |

---

## Batch Orchestrators

| File | Pipeline | Steps | Schedule | Error Handling |
|------|----------|-------|----------|----------------|
| `BatchJobs/run_daily_banking.sas` | Banking | 4 (load → txn → risk → regulatory) | Daily 05:45 | Control table tracking, `ABORT_ON_ERR`, `%sendmail`, restart support |
| `BatchJobs/run_daily_insurance.sas` | Insurance | 2 (claims → valuation) | Daily 07:00 | Control table tracking, `ABORT_ON_ERR`, `%sendmail`, restart support |

---

## Configuration

| File | Purpose |
|------|---------|
| `Config/autoexec.sas` | 14 LIBNAME assignments, Oracle/Teradata connections, 12 global macro variables, system options, autocall paths |

---

## Format Catalogs

| File | Formats | Domain |
|------|---------|--------|
| `Formats/banking_formats.sas` | 9 formats: `$ACCTTYPE`, `$ACCTSTAT`, `RISKRATE`, `$TXNCAT`, `DELQBKT`, `BALRANGE`, `$REGION`, `$CUSTSEG`, `$LNPURP` | Banking |
| `Formats/insurance_formats.sas` | 5 formats: `$POLTYPE`, `$CLMSTAT`, `$RISKCAT`, `$COVTYPE`, `LOSSRANGE` | Insurance |
