# SAS to dbt/Databricks Migration Plan

> **Scope**: All SAS programs in `ts-sas-legacy-analytics` (Programs/Banking/, Programs/Insurance/, Programs/Reports/)
> **Target**: dbt project on Databricks with Unity Catalog — [`uc-data-migration-sas-to-databricks/dbt_project/`](https://github.com/Cognition-Partner-Workshops/uc-data-migration-sas-to-databricks)
> **Reference**: [`docs/SAS_TO_DBT_MIGRATION_MAP.md`](https://github.com/Cognition-Partner-Workshops/uc-data-migration-sas-to-databricks/blob/main/docs/SAS_TO_DBT_MIGRATION_MAP.md)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [SAS Estate Inventory](#2-sas-estate-inventory)
3. [Program-by-Program Migration Plan](#3-program-by-program-migration-plan)
   - 3.1 [load_customer_accounts.sas](#31-load_customer_accountssas)
   - 3.2 [daily_transaction_processing.sas](#32-daily_transaction_processingsas)
   - 3.3 [credit_risk_scoring.sas](#33-credit_risk_scoringsas)
   - 3.4 [monthly_regulatory_reporting.sas](#34-monthly_regulatory_reportingsas)
   - 3.5 [claims_processing.sas](#35-claims_processingsas)
   - 3.6 [policy_valuation.sas](#36-policy_valuationsas)
   - 3.7 [customer_profitability.sas](#37-customer_profitabilitysas)
4. [Supporting Asset Migration](#4-supporting-asset-migration)
   - 4.1 [autoexec.sas → Unity Catalog + dbt sources](#41-autoexecsas--unity-catalog--dbt-sources)
   - 4.2 [PROC FORMAT catalogs → dbt macros](#42-proc-format-catalogs--dbt-macros)
   - 4.3 [Macro library (92 macros) → dbt Jinja macros / Python](#43-macro-library-92-macros--dbt-jinja-macros--python)
   - 4.4 [Batch orchestrators → Databricks Workflows](#44-batch-orchestrators--databricks-workflows)
5. [Construct Translation Reference](#5-construct-translation-reference)
6. [dbt DAG (Target Dependency Graph)](#6-dbt-dag-target-dependency-graph)
7. [Effort and Risk Summary](#7-effort-and-risk-summary)
8. [Validation Strategy](#8-validation-strategy)
9. [Recommended Migration Sequence](#9-recommended-migration-sequence)

---

## 1. Executive Summary

This migration plan covers **7 SAS programs**, **2 batch orchestrators**, **2 PROC FORMAT catalogs**, **1 autoexec configuration**, and a **92-macro utility library**. The target architecture is a dbt project running on Databricks with Unity Catalog, as defined in `uc-data-migration-sas-to-databricks/dbt_project/`.

The reference dbt project already contains completed migrations for 3 of the 7 programs (load_customer_accounts, daily_transaction_processing, credit_risk_scoring). The remaining 4 programs (monthly_regulatory_reporting, claims_processing, policy_valuation, customer_profitability) are planned but not yet implemented.

**Total estimated effort**: 22–32 person-days
**Highest risk items**: Credit risk scoring model (regulatory validation), Claims processing hash objects, Batch orchestration conversion

---

## 2. SAS Estate Inventory

### Programs

| # | SAS Program | Domain | LOC | Schedule | Control-M Job |
|---|-------------|--------|-----|----------|--------------|
| 1 | `Programs/Banking/load_customer_accounts.sas` | Banking | 216 | Daily 06:00 | BANK_DAILY_01 |
| 2 | `Programs/Banking/daily_transaction_processing.sas` | Banking | 246 | Daily 07:30 | BANK_DAILY_02 |
| 3 | `Programs/Banking/credit_risk_scoring.sas` | Banking | 270 | Weekly Sun 02:00 | BANK_WEEKLY_01 |
| 4 | `Programs/Banking/monthly_regulatory_reporting.sas` | Banking | 199 | Monthly 3rd biz day | BANK_MONTHLY_01 |
| 5 | `Programs/Insurance/claims_processing.sas` | Insurance | 238 | Daily 08:00 | INS_DAILY_01 |
| 6 | `Programs/Insurance/policy_valuation.sas` | Insurance | 206 | Monthly 5th biz day | INS_MONTHLY_01 |
| 7 | `Programs/Reports/customer_profitability.sas` | Reports | 176 | Monthly 10th biz day | BANK_MONTHLY_03 |

### Supporting Assets

| Asset | File | Purpose |
|-------|------|---------|
| Global config | `Config/autoexec.sas` | LIBNAMEs, macro vars, DB connections, system options |
| Banking formats | `Formats/banking_formats.sas` | 8 PROC FORMATs: $ACCTTYPE, $ACCTSTAT, RISKRATE, $TXNCAT, DELQBKT, BALRANGE, $REGION, $CUSTSEG |
| Insurance formats | `Formats/insurance_formats.sas` | 5 PROC FORMATs: $POLTYPE, $CLMSTAT, $RISKCAT, $COVTYPE, LOSSRANGE |
| Banking batch | `BatchJobs/run_daily_banking.sas` | 4-step orchestrator with error handling, restart logic |
| Insurance batch | `BatchJobs/run_daily_insurance.sas` | 2-step orchestrator with error handling, restart logic |
| Macro library | `Macro/*.sas` (92 files) | parmv, nobs, lock, sendmail, export_xlsx, logparse, etc. |

### External Dependencies

| Source | SAS LIBNAME | Tables Used | Databricks Target |
|--------|-------------|-------------|-------------------|
| Oracle DW | `ORA_DW` | CUST_ACCOUNTS, CUST_DEMOGRAPHICS, BUREAU_SCORES, PAYMENT_HISTORY, COLLATERAL, LOAN_DETAILS, COST_OF_FUNDS | `banking_analytics.raw.*` (Unity Catalog external tables) |
| Teradata Analytics | `TERA_DW` | ACTUARIAL_TABLES, FRAUD_INDICATORS | `banking_analytics.raw.*` (Unity Catalog external tables) |
| File-based feeds | `RAW_BANK`, `RAW_INS` | TXN_FEED_*, CLAIMS_FEED_*, POLICIES, PREMIUMS, CLAIMS | `banking_analytics.raw.*` (Auto Loader or COPY INTO) |

---

## 3. Program-by-Program Migration Plan

### 3.1 load_customer_accounts.sas

**Source**: `Programs/Banking/load_customer_accounts.sas` (216 lines)
**Schedule**: Daily 06:00 via Control-M BANK_DAILY_01
**Migration status**: Migrated — `stg_cust_accounts.sql` + `int_account_metrics.sql` exist in reference dbt project

#### Inputs → Outputs

| SAS Input | SAS Output |
|-----------|------------|
| `ORA_DW.CUST_ACCOUNTS` | `STG_BANK.CUST_ACCOUNTS_DAILY` |
| `ORA_DW.CUST_DEMOGRAPHICS` | `WORK.ACCT_EXCEPTIONS` → `STG_BANK.ACCT_EXCEPTIONS` |
| `RAW_BANK.DAILY_RATES` | `WORK.ACCT_SUMMARY` |

#### dbt Model Mapping

| dbt Layer | dbt Model | Replaces |
|-----------|-----------|----------|
| **staging** | `stg_cust_accounts.sql` | Step 1: PROC SQL extract + join from Oracle DW |
| **intermediate** | `int_account_metrics.sql` | Step 2: DATA step business rules + derived metrics |
| (new) **intermediate** | `int_account_exceptions.sql` | Step 3: Exception routing (NEG_BAL, HIGH_UTIL, NO_RISK) |

#### SAS Constructs Requiring Translation

| SAS Construct | Location | dbt/Databricks Equivalent | Reference |
|---------------|----------|---------------------------|-----------|
| `PROC SQL` with Oracle join | Step 1 | dbt staging model with `source()` | Migration Map §1 |
| `%include` macro imports (parmv, nobs, lock) | Header | dbt macro system (not needed for basic utility) | Migration Map §8 |
| `%parmv` parameter validation | Line 19-20 | dbt `vars` with default values | Migration Map §8 |
| `%nobs` row count checks | Line 71 | dbt `run_query` or post-hook log | — |
| `%goto EXIT` flow control | Line 76 | dbt `on-run-end` hooks | — |
| DATA step IF/THEN logic | Step 2 | SQL `CASE` expressions | Migration Map §3 |
| `FORMAT $ACCTTYPE.` etc. | Step 2 | `{{ format_account_type() }}` macro | Migration Map §2 |
| `intck('month', ...)` | Line 100 | `months_between()` | Migration Map §3 |
| `PROC MEANS NWAY` summary | Step 4 | SQL `GROUP BY` aggregation | Migration Map §3 |
| `%sendmail` notification | Step 3 | Databricks alert or PagerDuty webhook | Migration Map §7 |
| `PROC APPEND` to exceptions | Step 3 | dbt incremental model | Migration Map §6 |

#### Effort & Risk

| Metric | Value |
|--------|-------|
| **Effort** | 2–3 days (mostly done — validate against reference) |
| **Risk** | Low |
| **Notes** | Reference dbt models exist. Remaining work: exception routing model, PROC MEANS summary model, email notification equivalent. |

---

### 3.2 daily_transaction_processing.sas

**Source**: `Programs/Banking/daily_transaction_processing.sas` (246 lines)
**Schedule**: Daily 07:30 via Control-M BANK_DAILY_02
**Depends on**: load_customer_accounts.sas (BANK_DAILY_01)
**Migration status**: Migrated — `stg_daily_transactions.sql`, `mart_daily_transactions.sql`, `mart_transaction_anomalies.sql` exist

#### Inputs → Outputs

| SAS Input | SAS Output |
|-----------|------------|
| `RAW_BANK.TXN_FEED_YYYYMMDD` (dynamic name) | `CURATED.DAILY_TRANSACTIONS` |
| `STG_BANK.CUST_ACCOUNTS_DAILY` | `CURATED.TXN_ANOMALIES` |
| `CURATED.DAILY_TRANSACTIONS` (history for stats) | `CURATED.RUNNING_BALANCES` |

#### dbt Model Mapping

| dbt Layer | dbt Model | Replaces |
|-----------|-----------|----------|
| **staging** | `stg_daily_transactions.sql` | Step 1: DATA step feed validation + rejected record routing |
| **marts** | `mart_daily_transactions.sql` (incremental) | Step 2-3: PROC SQL enrichment + RETAIN running balance + PROC APPEND |
| **marts** | `mart_transaction_anomalies.sql` | Step 4: Z-score anomaly detection |

#### SAS Constructs Requiring Translation

| SAS Construct | Location | dbt/Databricks Equivalent | Reference |
|---------------|----------|---------------------------|-----------|
| Dynamic dataset name `TXN_FEED_&date` | Line 25 | Single source table in Unity Catalog (partitioned by date) or Auto Loader | — |
| `%sysfunc(exist(RAW_BANK.&txn_ds))` | Line 36 | dbt `source` freshness test | — |
| DATA step validation with `output`/`return` | Step 1 | SQL `CASE` for rejection_reason + `WHERE` filter | Migration Map §3 |
| `PROC SQL` enrichment join | Step 2 | dbt `ref()` join | Migration Map §1 |
| **`RETAIN RUNNING_BALANCE`** + BY-group | Step 3 | **Window function `SUM() OVER (PARTITION BY ... ORDER BY ... ROWS UNBOUNDED PRECEDING)`** | Migration Map §4 |
| `first.ACCOUNT_ID` / `last.ACCOUNT_ID` | Step 3 | Window function boundary check | Migration Map §4 |
| `PROC SQL` 90-day rolling stats | Step 4 | SQL `GROUP BY` with date filter | Migration Map §3 |
| Z-score anomaly classification | Step 4 | SQL `CASE` with computed z-score | Migration Map §3 |
| `%lock` + `PROC APPEND` | Step 5 | dbt `incremental` materialization with `merge` strategy | Migration Map §6 |

#### Effort & Risk

| Metric | Value |
|--------|-------|
| **Effort** | 3–4 days (mostly done — validate against reference) |
| **Risk** | Medium |
| **Notes** | RETAIN → window function is a high-fidelity translation. Dynamic dataset naming requires architectural decision: flatten to single table with date partition vs. daily external tables. Reference models exist but the running balance edge cases (multi-txn per account per day) need careful validation. |

---

### 3.3 credit_risk_scoring.sas

**Source**: `Programs/Banking/credit_risk_scoring.sas` (270 lines)
**Schedule**: Weekly Sunday 02:00 via Control-M BANK_WEEKLY_01
**Migration status**: Migrated — `mart_risk_scores.sql` exists

#### Inputs → Outputs

| SAS Input | SAS Output |
|-----------|------------|
| `STG_BANK.CUST_ACCOUNTS_DAILY` | `CURATED.RISK_SCORES` |
| `ORA_DW.BUREAU_SCORES` | `CURATED.RISK_MIGRATION` |
| `ORA_DW.PAYMENT_HISTORY` | `REPORTS.RISK_SUMMARY` |
| `ORA_DW.COLLATERAL` | |

#### dbt Model Mapping

| dbt Layer | dbt Model | Replaces |
|-----------|-----------|----------|
| **marts** | `mart_risk_scores.sql` | Steps 1-2: Feature assembly + WOE scorecard + PD/LGD/EAD |
| (new) **marts** | `mart_risk_migration.sql` | Step 3: Risk rating migration matrix |
| (new) **marts** | `mart_risk_summary.sql` | Step 5: PROC MEANS aggregation by account type × risk rating |

#### SAS Constructs Requiring Translation

| SAS Construct | Location | dbt/Databricks Equivalent | Reference |
|---------------|----------|---------------------------|-----------|
| `PROC SQL` with correlated subquery (latest bureau score) | Step 1 | SQL window function `ROW_NUMBER()` or correlated subquery | — |
| **WOE scorecard** (nested IF/THEN) | Step 2 | **Nested SQL `CASE` expressions** (5 WOE variables) | Migration Map §3 |
| **Logistic PD: `1/(1+exp(-LOG_ODDS))`** | Line 157 | **Databricks SQL `exp()` function** | Migration Map §3 |
| LGD estimation (IF/THEN per product) | Lines 161-168 | SQL `CASE` | Migration Map §3 |
| EAD estimation (credit conversion factor) | Lines 172-175 | SQL `CASE` | Migration Map §3 |
| Risk rating assignment (PD bands) | Lines 183-189 | SQL `CASE` | Migration Map §3 |
| `PROC MEANS NWAY` by class | Step 5 | SQL `GROUP BY` | — |
| `%lock` + `PROC APPEND` | Step 4 | dbt incremental model or `MERGE INTO` | Migration Map §6 |

#### Effort & Risk

| Metric | Value |
|--------|-------|
| **Effort** | 4–5 days (model exists, but requires regulatory validation) |
| **Risk** | **High** |
| **Notes** | This is a **Basel III regulatory model**. The WOE coefficients, PD formula, LGD/EAD logic, and risk rating bands must produce **bit-identical** results to the SAS output. Requires model validation team sign-off. The correlated subquery for latest bureau score is a subtle correctness risk. Risk migration matrix is not yet migrated. |

---

### 3.4 monthly_regulatory_reporting.sas

**Source**: `Programs/Banking/monthly_regulatory_reporting.sas` (199 lines)
**Schedule**: Monthly 3rd business day via Control-M BANK_MONTHLY_01
**Migration status**: **Planned** — not yet implemented in dbt project

#### Inputs → Outputs

| SAS Input | SAS Output |
|-----------|------------|
| `STG_BANK.CUST_ACCOUNTS_DAILY` | `REPORTS.MONTHLY_RWA` |
| `ORA_DW.LOAN_DETAILS` | `REPORTS.DELINQUENCY_AGING` |
| | `REPORTS.LLP_COVERAGE` |
| | `REPORTS.CAPITAL_ADEQUACY` |
| | Excel: `REG_REPORT_YYYYMM.xlsx` (3 sheets) |

#### dbt Model Mapping

| dbt Layer | dbt Model | Replaces |
|-----------|-----------|----------|
| **marts** | `mart_regulatory_rwa.sql` | Step 1: RWA by account type with Basel III risk weights |
| **marts** | `mart_delinquency_aging.sql` | Step 2: 30/60/90/120/180+ delinquency buckets |
| **marts** | `mart_llp_coverage.sql` | Step 3: Loan loss provision coverage ratios |
| **marts** | `mart_capital_adequacy.sql` | Step 5: CET1/Tier1/Total capital ratios + pass/fail |
| (external) | Databricks notebook or Python | Step 4: `%export_xlsx` Excel generation |

#### SAS Constructs Requiring Translation

| SAS Construct | Location | dbt/Databricks Equivalent | Reference |
|---------------|----------|---------------------------|-----------|
| `PROC SQL` with `calculated` keyword | Steps 1-3 | dbt SQL CTEs (no `calculated` in standard SQL) | — |
| Basel III risk weight CASE logic | Step 1 | SQL `CASE` with LTV-dependent weights | Migration Map §3 |
| Delinquency bucket CASE | Step 2 | SQL `CASE` with `BETWEEN` ranges | Migration Map §3 |
| `PROC SQL` aggregation with `GROUP BY` ordinals | Steps 1-3 | SQL `GROUP BY` with column names | — |
| **`%export_xlsx` (PROC EXPORT to Excel)** | Step 4 | **Databricks notebook with `openpyxl` or Databricks SQL dashboard** | Migration Map §7 |
| Capital adequacy hardcoded GL values | Step 5 | dbt `var` or seed table for capital figures | — |
| Macro variable date arithmetic | Lines 27-29 | dbt `vars` with Jinja date logic | Migration Map §8 |

#### Effort & Risk

| Metric | Value |
|--------|-------|
| **Effort** | 3–4 days |
| **Risk** | **Medium-High** |
| **Notes** | Four separate output datasets map to four dbt models. The `calculated` keyword requires CTE refactoring. Excel export is out of dbt scope — requires a Databricks notebook or post-run Python step. Capital adequacy uses hardcoded values that should become configurable dbt vars. Regulatory nature means all outputs require exact validation. |

---

### 3.5 claims_processing.sas

**Source**: `Programs/Insurance/claims_processing.sas` (238 lines)
**Schedule**: Daily 08:00 via Control-M INS_DAILY_01
**Migration status**: **Planned** — not yet implemented in dbt project

#### Inputs → Outputs

| SAS Input | SAS Output |
|-----------|------------|
| `RAW_INS.CLAIMS_FEED_YYYYMMDD` (dynamic) | `STG_INS.CLAIMS_REGISTER` |
| `RAW_INS.POLICIES` | `STG_INS.CLAIMS_REVIEW_QUEUE` |
| `TERA_DW.FRAUD_INDICATORS` | `STG_INS.FRAUD_ALERTS` |

#### dbt Model Mapping

| dbt Layer | dbt Model | Replaces |
|-----------|-----------|----------|
| **staging** | `stg_claims_feed.sql` | Step 1: Feed ingestion + validation |
| **staging** | `stg_policies.sql` | Policies source staging |
| **intermediate** | `int_claims_fraud_screening.sql` | Step 2: Fraud score lookup + risk classification |
| **intermediate** | `int_claims_adjudication.sql` | Step 3: Auto-adjudication rules (approve/deny/manual) |
| **marts** | `mart_claims_register.sql` (incremental) | Step 4: Combined claims register |
| **marts** | `mart_fraud_alerts.sql` | Fraud alerts for SIU |

#### SAS Constructs Requiring Translation

| SAS Construct | Location | dbt/Databricks Equivalent | Reference |
|---------------|----------|---------------------------|-----------|
| **`declare hash h_pol`** (hash object lookup) | Step 1, lines 47-52 | **`/*+ BROADCAST(p) */` join hint** on policies table | Migration Map §5 |
| `h_pol.find()` rc check | Line 57-63 | `LEFT JOIN` with `WHERE` filter for unmatched | Migration Map §5 |
| DATA step multi-output (`CLAIMS_VALID` / `CLAIMS_INVALID`) | Step 1 | SQL `CASE` creating a validation_status column + `WHERE` filter | Migration Map §3 |
| IF/THEN/ELSE adjudication rules with `return` | Step 3 | SQL `CASE WHEN` with priority ordering | Migration Map §3 |
| `PROC APPEND` to claims register | Step 4 | dbt `incremental` model with `merge` | Migration Map §6 |
| `%sendmail` fraud alert notification | Step 4 | Databricks alert / webhook | — |
| `catx()` / `ifc()` string functions | Throughout | `CONCAT_WS()` / `CASE` | — |

#### Effort & Risk

| Metric | Value |
|--------|-------|
| **Effort** | 4–5 days |
| **Risk** | **High** |
| **Notes** | The **hash object** pattern is the most complex SAS construct in this estate. It performs an in-memory key lookup against the active policies table during the DATA step. The dbt equivalent is a broadcast join, but the conditional logic (policy period validation, claimed amount vs. sum insured) must be carefully sequenced. The multi-path routing (valid/invalid/auto-approve/manual/fraud) requires careful CASE expression design to preserve the priority order of the SAS IF/THEN/RETURN pattern. |

---

### 3.6 policy_valuation.sas

**Source**: `Programs/Insurance/policy_valuation.sas` (206 lines)
**Schedule**: Monthly 5th business day via Control-M INS_MONTHLY_01
**Migration status**: **Planned** — not yet implemented in dbt project

#### Inputs → Outputs

| SAS Input | SAS Output |
|-----------|------------|
| `RAW_INS.POLICIES` | `STG_INS.POLICY_VALUATION` |
| `RAW_INS.CLAIMS` | `REPORTS.LOSS_RATIO_SUMMARY` |
| `RAW_INS.PREMIUMS` | `REPORTS.RESERVE_ADEQUACY` |
| `TERA_DW.ACTUARIAL_TABLES` | |

#### dbt Model Mapping

| dbt Layer | dbt Model | Replaces |
|-----------|-----------|----------|
| **staging** | `stg_policies.sql` | Source staging for policies (shared with claims) |
| **staging** | `stg_premiums.sql` | Source staging for premium collections |
| **intermediate** | `int_claims_experience.sql` | Step 2: 12-month claims aggregation per policy |
| **intermediate** | `int_policy_valuation.sql` | Step 4: MERGE + valuation metric calculations |
| **marts** | `mart_loss_ratios.sql` | Step 5: PROC MEANS loss ratio summary by LOB |

#### SAS Constructs Requiring Translation

| SAS Construct | Location | dbt/Databricks Equivalent | Reference |
|---------------|----------|---------------------------|-----------|
| **`MERGE BY POLICY_ID`** (3-way merge) | Step 4 | **SQL multi-table `LEFT JOIN`** on policy_id | Migration Map §6 |
| `if a;` (keep only in-force) | Line 129 | Inner join or `WHERE` filter | — |
| `intck('month', ...)` date math | Steps 1, 2 | `months_between()` | — |
| `intnx('month', ..., -12)` date offset | Step 2 | `ADD_MONTHS(current_date(), -12)` | — |
| Earned premium pro-rata calculation | Step 1, lines 57-60 | SQL date math with `LEAST()`/`GREATEST()` | — |
| IBNR estimate formula | Line 155 | SQL `GREATEST(0, earned * 0.15 - paid)` | — |
| `FORMAT $POLTYPE.` / `$RISKCAT.` | Step 4 | New dbt macros: `format_policy_type()`, `format_risk_category()` | Migration Map §2 |
| `PROC MEANS NWAY` by POLICY_TYPE | Step 5 | SQL `GROUP BY` + calculated ratios | — |
| Conditional macro `%if &lob ne ALL` | Line 66-68 | dbt Jinja `{% if var('lob') != 'ALL' %}` | Migration Map §8 |

#### Effort & Risk

| Metric | Value |
|--------|-------|
| **Effort** | 3–4 days |
| **Risk** | **Medium** |
| **Notes** | The 3-way `MERGE BY` is straightforward as a multi-join in SQL. The earned premium calculation involves complex SAS date math (`intck`/`intnx` with alignment) that must be carefully translated to Databricks `months_between`/`ADD_MONTHS`. Two new format macros needed ($POLTYPE, $RISKCAT). IBNR and combined ratio calculations are actuarial — require SME validation. |

---

### 3.7 customer_profitability.sas

**Source**: `Programs/Reports/customer_profitability.sas` (176 lines)
**Schedule**: Monthly 10th business day via Control-M BANK_MONTHLY_03
**Migration status**: **Planned** — not yet implemented in dbt project

#### Inputs → Outputs

| SAS Input | SAS Output |
|-----------|------------|
| `STG_BANK.CUST_ACCOUNTS_DAILY` | `REPORTS.CUSTOMER_PNL` |
| `CURATED.DAILY_TRANSACTIONS` | `REPORTS.SEGMENT_PROFITABILITY` |
| `CURATED.RISK_SCORES` | `REPORTS.BRANCH_PROFITABILITY` |
| `ORA_DW.COST_OF_FUNDS` | Excel: `PROFITABILITY_YYYYMM.xlsx` |

#### dbt Model Mapping

| dbt Layer | dbt Model | Replaces |
|-----------|-----------|----------|
| **intermediate** | `int_interest_income.sql` | Step 1: Interest income / deposit cost by customer |
| **intermediate** | `int_fee_income.sql` | Step 2: Fee income from transactions |
| **intermediate** | `int_expected_credit_loss.sql` | Step 3: ECL from risk scores |
| **marts** | `mart_customer_pnl.sql` | Step 4: Multi-source merge → P&L assembly |
| **marts** | `mart_segment_profitability.sql` | Step 5: PROC MEANS by customer segment |
| **marts** | `mart_branch_profitability.sql` | Step 5: PROC MEANS by branch + region |

#### SAS Constructs Requiring Translation

| SAS Construct | Location | dbt/Databricks Equivalent | Reference |
|---------------|----------|---------------------------|-----------|
| **Multi-source `MERGE BY CUSTOMER_ID`** (3-way) | Step 4 | **Multi-`ref()` `LEFT JOIN`** | Migration Map §6 |
| `PROC SQL` with `calculated` keyword | Steps 1-3 | CTE-based approach | — |
| Correlated subquery (latest risk score) | Step 3 | Window function `ROW_NUMBER()` or `QUALIFY` | — |
| `PROC MEANS NWAY` × 2 (segment + branch) | Step 5 | Two SQL `GROUP BY` models | — |
| P&L assembly: revenue - cost - ECL | Step 4 | SQL arithmetic | — |
| `%export_xlsx` Excel export | Step 5 | Databricks notebook or Python post-hook | Migration Map §7 |
| Profitability tier assignment (IF/THEN) | Lines 128-132 | SQL `CASE` | Migration Map §3 |
| ROA annualization calculation | Lines 121-124 | SQL `CASE WHEN ... THEN (net_profit * 12) / total_relationship` | — |

#### Effort & Risk

| Metric | Value |
|--------|-------|
| **Effort** | 3–4 days |
| **Risk** | **Medium** |
| **Notes** | This is the highest fan-in model — it references outputs from load_customer_accounts, daily_transaction_processing, and credit_risk_scoring. All upstream models must be migrated and validated first. The 3-way merge maps cleanly to multi-ref joins. The P&L formula is simple arithmetic. Excel export requires the same Databricks notebook approach as regulatory reporting. |

---

## 4. Supporting Asset Migration

### 4.1 autoexec.sas → Unity Catalog + dbt sources

| SAS Component | dbt/Databricks Equivalent | Implementation |
|---------------|---------------------------|----------------|
| `LIBNAME ORA_DW oracle ...` | Unity Catalog external tables | `_staging_sources.yml` → `banking_raw` source |
| `LIBNAME TERA_DW teradata ...` | Unity Catalog external tables | `_staging_sources.yml` → `insurance_raw` source |
| `LIBNAME RAW_BANK "/data/sas/raw/banking"` | Unity Catalog managed tables | Auto Loader / COPY INTO |
| `LIBNAME STG_BANK "/data/sas/staging/banking"` | dbt `staging` schema | `+schema: staging` in dbt_project.yml |
| `LIBNAME CURATED "/data/sas/curated"` | dbt `marts` schema | `+schema: marts` in dbt_project.yml |
| `LIBNAME REPORTS "/data/sas/reports"` | dbt `marts` schema | `+schema: marts` in dbt_project.yml |
| `%let CURR_DT = ...` | `vars.curr_dt` | dbt_project.yml `run_started_at` |
| `%let PREV_YM = ...` | `vars.prev_ym` | dbt_project.yml Jinja date math |
| `%let EMAIL_DL = ...` | Databricks alert destination | Workflow notification config |
| `options fmtsearch=(BANKING INSURANCE)` | dbt macro auto-loading | Macros in `macros/` auto-available |
| `options compress=yes` | Delta Lake default compression | Built into Delta format |

### 4.2 PROC FORMAT catalogs → dbt macros

#### Banking Formats (`Formats/banking_formats.sas`)

| SAS Format | Status | dbt Macro | File |
|------------|--------|-----------|------|
| `$ACCTTYPE` | Migrated | `format_account_type()` | `macros/format_account_type.sql` |
| `$ACCTSTAT` | Migrated | `format_account_status()` | `macros/format_account_status.sql` |
| `$CUSTSEG` | Migrated | `format_customer_segment()` | `macros/format_customer_segment.sql` |
| `$TXNCAT` | Migrated | `format_txn_category()` | `macros/format_txn_category.sql` |
| `RISKRATE` | **To create** | `format_risk_rating()` | `macros/format_risk_rating.sql` |
| `DELQBKT` | **To create** | `format_delinquency_bucket()` | `macros/format_delinquency_bucket.sql` |
| `BALRANGE` | **To create** | `format_balance_range()` | `macros/format_balance_range.sql` |
| `$REGION` | **To create** | `format_region()` | `macros/format_region.sql` |
| `$LNPURP` | **To create** | `format_loan_purpose()` | `macros/format_loan_purpose.sql` |

#### Insurance Formats (`Formats/insurance_formats.sas`)

| SAS Format | Status | dbt Macro | File |
|------------|--------|-----------|------|
| `$POLTYPE` | **To create** | `format_policy_type()` | `macros/format_policy_type.sql` |
| `$CLMSTAT` | **To create** | `format_claim_status()` | `macros/format_claim_status.sql` |
| `$RISKCAT` | **To create** | `format_risk_category()` | `macros/format_risk_category.sql` |
| `$COVTYPE` | **To create** | `format_coverage_type()` | `macros/format_coverage_type.sql` |
| `LOSSRANGE` | **To create** | `format_loss_range()` | `macros/format_loss_range.sql` |

**Note**: Numeric range formats (DELQBKT, BALRANGE, LOSSRANGE) require `CASE WHEN ... BETWEEN ...` rather than simple `CASE column WHEN ...` patterns.

### 4.3 Macro library (92 macros) → dbt Jinja macros / Python

Most of the 92 SAS macros in `Macro/` are **SAS-platform utilities** that have no direct dbt equivalent because dbt handles these concerns differently:

| SAS Macro Category | Examples | dbt Equivalent | Action |
|-------------------|----------|----------------|--------|
| Parameter validation | `parmv.sas` | dbt `vars` with defaults | Not needed — dbt handles natively |
| Row counting | `nobs.sas` | `dbt_utils.get_query_results_as_dict` or `run_query` | Migrate if needed for logging |
| Dataset locking | `lock.sas` | Delta Lake transactions | Not needed — Delta handles concurrency |
| Email notifications | `sendmail.sas` | Databricks alerts / PagerDuty | Implement as Workflow notification |
| Excel export | `export_xlsx.sas` | Python `openpyxl` in Databricks notebook | Migrate as post-run notebook |
| Log parsing | `logparse.sas` | Databricks job logs API | Not needed — Databricks provides native logging |
| SAS dataset utilities | `check_if_empty.sas`, `seplist.sas`, `handle.sas` | dbt macros / Jinja | Migrate on demand |
| Format utilities | `fmtdesc.sas` | dbt macros | Already covered by format macros |

**Recommendation**: Migrate only the macros that are actively called by the 7 target programs. Based on analysis, only **5 macros** are directly referenced: `parmv`, `nobs`, `lock`, `sendmail`, `export_xlsx`.

### 4.4 Batch orchestrators → Databricks Workflows

#### Banking Batch (`BatchJobs/run_daily_banking.sas`)

| SAS Step | Program | dbt Task | Depends On |
|----------|---------|----------|------------|
| 1 | `load_customer_accounts.sas` | `dbt run --select stg_cust_accounts int_account_metrics` | — |
| 2 | `daily_transaction_processing.sas` | `dbt run --select stg_daily_transactions mart_daily_transactions mart_transaction_anomalies` | Task 1 |
| 3 | `credit_risk_scoring.sas` | `dbt run --select mart_risk_scores` | Task 1 |
| 4 | `monthly_regulatory_reporting.sas` | `dbt run --select mart_regulatory_rwa mart_delinquency_aging mart_llp_coverage mart_capital_adequacy` | Task 1 |

**Databricks Workflow JSON**:
```json
{
  "name": "daily_banking_pipeline",
  "schedule": { "quartz_cron_expression": "0 0 6 * * ?", "timezone_id": "America/New_York" },
  "tasks": [
    { "task_key": "staging_and_intermediate",
      "dbt_task": { "commands": ["dbt run --select tag:staging tag:intermediate"] } },
    { "task_key": "marts",
      "depends_on": [{ "task_key": "staging_and_intermediate" }],
      "dbt_task": { "commands": ["dbt run --select tag:marts"] } },
    { "task_key": "validation",
      "depends_on": [{ "task_key": "marts" }],
      "dbt_task": { "commands": ["dbt test"] } }
  ],
  "email_notifications": { "on_failure": ["oncall-data@corp.internal"] }
}
```

**Key orchestration features to preserve**:
- `restart_from` parameter → Databricks Workflow "Repair Run" feature
- `ABORT_ON_ERR` → Task dependency `on_failure` behavior
- `%sendmail` notifications → Workflow email notifications
- Batch control table logging → Databricks job run history API

#### Insurance Batch (`BatchJobs/run_daily_insurance.sas`)

| SAS Step | Program | dbt Task | Depends On |
|----------|---------|----------|------------|
| 1 | `claims_processing.sas` | `dbt run --select stg_claims_feed int_claims_fraud_screening int_claims_adjudication mart_claims_register mart_fraud_alerts` | — |
| 2 | `policy_valuation.sas` | `dbt run --select stg_policies stg_premiums int_claims_experience int_policy_valuation mart_loss_ratios` | — |

**Note**: In SAS, steps 1 and 2 run sequentially. In dbt, they share no dependencies and can run in **parallel**, reducing total pipeline execution time.

---

## 5. Construct Translation Reference

This table summarizes every SAS construct found across all 7 programs and maps it to its dbt/Databricks equivalent. See `docs/SAS_TO_DBT_MIGRATION_MAP.md` in the reference project for detailed examples of each pattern.

| # | SAS Construct | Programs Using It | dbt/Databricks Equivalent | Complexity |
|---|---------------|-------------------|---------------------------|------------|
| 1 | `PROC SQL` with joins | All 7 | dbt SQL models with `ref()` / `source()` | Low |
| 2 | `DATA` step IF/THEN/ELSE | All 7 | SQL `CASE WHEN` expressions | Low |
| 3 | `PROC FORMAT` | All 7 (via `FORMAT` stmt) | dbt Jinja macros returning `CASE` | Low |
| 4 | `%MACRO` / `%MEND` | All 7 | dbt Jinja macros | Low |
| 5 | `%include` chains | All 7 + batch | dbt `ref()` DAG | Low |
| 6 | Macro variables (`&var`) | All 7 | dbt `var()` / `env_var()` | Low |
| 7 | `PROC MEANS NWAY` | 1, 3, 6, 7 | SQL `GROUP BY` with aggregations | Low |
| 8 | `PROC APPEND` with `%lock` | 2, 3, 5 | dbt `incremental` materialization (merge) | Medium |
| 9 | **`RETAIN` + BY-group** | 2 | **Window function `SUM() OVER (... ROWS UNBOUNDED PRECEDING)`** | Medium |
| 10 | **`declare hash` object** | 5 | **`/*+ BROADCAST */` join hint** | Medium |
| 11 | `MERGE BY` (multi-dataset) | 6, 7 | Multi-table `LEFT JOIN` on key | Medium |
| 12 | `%goto` / `%return` flow | 1, 2, 5, batch | dbt error handling hooks / Workflow retry | Medium |
| 13 | SAS date functions (`intck`, `intnx`) | 1, 4, 6 | `months_between()`, `ADD_MONTHS()`, `DATEDIFF()` | Medium |
| 14 | `PROC SQL` with `calculated` | 4, 7 | CTE-based rewrite (no `calculated` in standard SQL) | Medium |
| 15 | `%sendmail` notifications | 1, 5, batch | Databricks Alerts / PagerDuty / email notification | Medium |
| 16 | **WOE scorecard (nested IF)** | 3 | **Nested `CASE` with 5 WOE variables + `exp()` PD** | High |
| 17 | **`%export_xlsx`** | 4, 7 | **Databricks notebook / Python `openpyxl`** | High |
| 18 | **Batch orchestration** (run_step, restart, abort) | batch jobs | **Databricks Workflows** (JSON/YAML definition) | High |

---

## 6. dbt DAG (Target Dependency Graph)

```
BANKING PIPELINE
════════════════

source(banking_raw.cust_accounts)     ─┐
source(banking_raw.cust_demographics)  ─┤
                                        ├→ stg_cust_accounts
                                        │       │
                                        │       └→ int_account_metrics
                                        │               │
                                        │               ├→ mart_daily_transactions (incremental)
                                        │               │       │
                                        │               │       └→ mart_transaction_anomalies
                                        │               │
                                        │               ├→ mart_risk_scores
                                        │               │       │
                                        │               │       ├→ mart_risk_migration
                                        │               │       └→ mart_risk_summary
                                        │               │
                                        │               ├→ mart_regulatory_rwa
                                        │               ├→ mart_delinquency_aging
                                        │               ├→ mart_llp_coverage
                                        │               └→ mart_capital_adequacy
                                        │
source(banking_raw.daily_transactions) ─→ stg_daily_transactions ──→ mart_daily_transactions
source(banking_raw.bureau_scores)      ─→ mart_risk_scores
source(banking_raw.payment_history)    ─→ mart_risk_scores
source(banking_raw.collateral)         ─→ mart_risk_scores
source(banking_raw.loan_details)       ─→ mart_regulatory_rwa, mart_llp_coverage


INSURANCE PIPELINE
══════════════════

source(insurance_raw.claims)           ─┐
source(insurance_raw.fraud_indicators) ─┤
                                        ├→ stg_claims_feed
                                        │       │
                                        │       └→ int_claims_fraud_screening
                                        │               │
                                        │               └→ int_claims_adjudication
                                        │                       │
                                        │                       ├→ mart_claims_register (incremental)
                                        │                       └→ mart_fraud_alerts
                                        │
source(insurance_raw.policies)         ─→ stg_policies ──┬→ int_claims_adjudication (BROADCAST join)
                                                         └→ int_policy_valuation
                                                                 │
source(insurance_raw.premiums)         ─→ stg_premiums ──→ int_policy_valuation
                                                                 │
source(insurance_raw.claims)           ─→ int_claims_experience ─┘
                                                                 │
                                                                 └→ mart_loss_ratios


CROSS-DOMAIN (Customer Profitability)
═════════════════════════════════════

int_account_metrics ─────────────────┐
mart_daily_transactions ─────────────┤
mart_risk_scores ────────────────────┤
source(banking_raw.cost_of_funds) ───┤
                                     ├→ int_interest_income  ─┐
                                     ├→ int_fee_income        ├→ mart_customer_pnl
                                     └→ int_expected_credit_loss ┘     │
                                                                       ├→ mart_segment_profitability
                                                                       └→ mart_branch_profitability
```

---

## 7. Effort and Risk Summary

### By Program

| Program | dbt Models | Effort (days) | Risk | Migration Status |
|---------|------------|---------------|------|------------------|
| load_customer_accounts.sas | 2 (+1 new) | 2–3 | Low | Mostly migrated |
| daily_transaction_processing.sas | 3 | 3–4 | Medium | Mostly migrated |
| credit_risk_scoring.sas | 1 (+2 new) | 4–5 | **High** | Partially migrated |
| monthly_regulatory_reporting.sas | 4 | 3–4 | **Medium-High** | Not started |
| claims_processing.sas | 4–6 | 4–5 | **High** | Not started |
| policy_valuation.sas | 3–5 | 3–4 | Medium | Not started |
| customer_profitability.sas | 3–6 | 3–4 | Medium | Not started |

### By Work Category

| Category | Items | Effort (days) | Notes |
|----------|-------|---------------|-------|
| New dbt SQL models | ~18 models | 12–18 | Core migration work |
| New dbt macros (PROC FORMAT) | 10 macros | 1–2 | Mechanical translation |
| Databricks Workflows | 2 pipelines | 2–3 | Replace Control-M + batch SAS |
| Excel export notebooks | 2 notebooks | 1–2 | Replace %export_xlsx |
| Validation & UAT | All models | 5–7 | Row counts, checksums, sample records |
| **Total** | | **22–32 days** | |

### Risk Matrix

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Credit risk model produces different PD values | Regulatory failure | Medium | Bit-identical validation; parallel run period |
| Hash object → broadcast join changes row ordering | Incorrect claim adjudication | Low | Explicit ORDER BY + deterministic tie-breaking |
| SAS date math ≠ Databricks date math (edge cases) | Incorrect period boundaries | Medium | Unit tests on date boundary conditions (leap year, month-end) |
| RETAIN running balance off-by-one | Incorrect balances/anomalies | Low | Validate window function with known test data |
| Excel export formatting differences | Regulator rejects report | Low | Template-based notebook with frozen formatting |
| Dynamic dataset names (TXN_FEED_*) | Data ingestion gaps | Medium | Move to single partitioned table via Auto Loader |

---

## 8. Validation Strategy

For each migrated model, follow the validation approach from `docs/SAS_TO_DBT_MIGRATION_MAP.md`:

1. **Row count parity**: `SELECT COUNT(*)` in dbt must match SAS `%nobs()` from production logs
2. **Column-level checksums**: `SUM(amount)`, `COUNT(DISTINCT id)` must match between SAS and dbt outputs
3. **Sample record comparison**: 100 random records compared field-by-field
4. **Business rule validation**: Exception counts (anomalies, rejections, fraud alerts) match SAS volumes
5. **Parallel run**: Run SAS and dbt pipelines simultaneously for 30 days; compare outputs daily

### Critical Validation Points

| Model | Validation Focus |
|-------|-----------------|
| `mart_risk_scores` | PD values match to 8 decimal places; risk rating distribution identical |
| `mart_daily_transactions` | Running balance matches SAS RETAIN output for every transaction |
| `mart_claims_register` | Adjudication result (APPR/DENY/PEND) matches for every claim |
| `mart_regulatory_rwa` | RWA totals match to the cent; capital ratios match to 2 decimal places |
| `mart_loss_ratios` | Loss ratio and combined ratio match; IBNR estimates match |

---

## 9. Recommended Migration Sequence

The migration should follow the dbt DAG dependency order, starting with the programs that have existing reference models.

### Wave 1 — Validate Existing Migrations (Week 1–2)

| Step | Action | Blocking? |
|------|--------|-----------|
| 1.1 | Validate `stg_cust_accounts` + `int_account_metrics` against SAS load_customer_accounts output | No |
| 1.2 | Validate `stg_daily_transactions` + `mart_daily_transactions` + `mart_transaction_anomalies` | No |
| 1.3 | Validate `mart_risk_scores` against SAS credit_risk_scoring output | Yes — regulatory |
| 1.4 | Add missing exception model `int_account_exceptions` | No |
| 1.5 | Add missing `mart_risk_migration` + `mart_risk_summary` | No |

### Wave 2 — New Banking Models (Week 3–4)

| Step | Action | Depends On |
|------|--------|------------|
| 2.1 | Create format macros: risk_rating, delinquency_bucket, balance_range, region, loan_purpose | — |
| 2.2 | Create `mart_regulatory_rwa` | Wave 1 (int_account_metrics) |
| 2.3 | Create `mart_delinquency_aging` | Wave 1 |
| 2.4 | Create `mart_llp_coverage` | Wave 1 |
| 2.5 | Create `mart_capital_adequacy` | 2.2 |
| 2.6 | Create regulatory Excel export notebook | 2.2–2.4 |

### Wave 3 — Insurance Models (Week 4–5)

| Step | Action | Depends On |
|------|--------|------------|
| 3.1 | Create format macros: policy_type, claim_status, risk_category, coverage_type, loss_range | — |
| 3.2 | Create `stg_claims_feed` + `stg_policies` + `stg_premiums` | — |
| 3.3 | Create `int_claims_fraud_screening` (broadcast join) | 3.2 |
| 3.4 | Create `int_claims_adjudication` | 3.3 |
| 3.5 | Create `mart_claims_register` (incremental) + `mart_fraud_alerts` | 3.4 |
| 3.6 | Create `int_claims_experience` + `int_policy_valuation` + `mart_loss_ratios` | 3.2 |

### Wave 4 — Cross-Domain + Orchestration (Week 5–6)

| Step | Action | Depends On |
|------|--------|------------|
| 4.1 | Create `int_interest_income`, `int_fee_income`, `int_expected_credit_loss` | Waves 1–2 |
| 4.2 | Create `mart_customer_pnl` | 4.1 |
| 4.3 | Create `mart_segment_profitability` + `mart_branch_profitability` | 4.2 |
| 4.4 | Create profitability Excel export notebook | 4.3 |
| 4.5 | Create Databricks Workflows (banking + insurance) | All models |
| 4.6 | Decommission Control-M jobs | 4.5 validated |

### Wave 5 — Validation & Cutover (Week 6–8)

| Step | Action |
|------|--------|
| 5.1 | 30-day parallel run: SAS + dbt side-by-side |
| 5.2 | Daily reconciliation of row counts + checksums |
| 5.3 | Regulatory model sign-off (credit risk + RWA) |
| 5.4 | UAT with business stakeholders |
| 5.5 | Cutover: disable SAS batch; enable Databricks Workflows as primary |
| 5.6 | Decommission SAS LIBNAMEs and Oracle/Teradata connections |
