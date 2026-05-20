# Gap Analysis: SAS Estate vs. Existing dbt Target

Comparison of the full SAS estate against the current state of `uc-data-migration-sas-to-databricks`.

---

## Existing dbt Models in Target Repo

### Staging Layer (2 models)

| Model | SAS Source | Coverage |
|-------|-----------|----------|
| `stg_cust_accounts.sql` | `load_customer_accounts.sas` Step 1 | Partial — needs derived fields, exception routing |
| `stg_daily_transactions.sql` | `daily_transaction_processing.sas` Step 1 | Partial — needs validation/rejection logic |

### Intermediate Layer (1 model)

| Model | SAS Source | Coverage |
|-------|-----------|----------|
| `int_account_metrics.sql` | `load_customer_accounts.sas` Step 2 | Partial — verify business rule derivations |

### Marts Layer (3 models)

| Model | SAS Source | Coverage |
|-------|-----------|----------|
| `mart_risk_scores.sql` | `credit_risk_scoring.sas` | Partial — needs WOE binning, PD/LGD/EAD |
| `mart_daily_transactions.sql` | `daily_transaction_processing.sas` Step 5 | Partial — verify incremental append logic |
| `mart_transaction_anomalies.sql` | `daily_transaction_processing.sas` Step 4 | Partial — verify Z-score and anomaly types |

### Macros (4 macros)

| Macro | SAS Format | Coverage |
|-------|-----------|----------|
| `format_account_type.sql` | `$ACCTTYPE` | Needs verification against 11 values |
| `format_account_status.sql` | `$ACCTSTAT` | Needs verification against 8 values |
| `format_customer_segment.sql` | `$CUSTSEG` | Needs verification against 6 values |
| `format_txn_category.sql` | `$TXNCAT` | Needs verification against 10 values |

---

## Gap Summary

### Models Not Yet Created

| # | dbt Model Needed | SAS Source | Priority |
|---|-----------------|-----------|----------|
| 1 | `stg_claims_feed` | `claims_processing.sas` Step 1 | P1 |
| 2 | `stg_policies_inforce` | `policy_valuation.sas` Step 1 | P1 |
| 3 | `stg_premiums` | `policy_valuation.sas` Step 3 | P1 |
| 4 | `int_account_exceptions` | `load_customer_accounts.sas` Step 3 | P0 |
| 5 | `int_txn_enriched` | `daily_transaction_processing.sas` Step 2 | P0 |
| 6 | `int_running_balances` | `daily_transaction_processing.sas` Step 3 | P0 |
| 7 | `int_risk_features` | `credit_risk_scoring.sas` Step 1 | P0 |
| 8 | `int_claims_validated` | `claims_processing.sas` Steps 1-2 | P1 |
| 9 | `int_claims_fraud_scored` | `claims_processing.sas` Step 2 | P1 |
| 10 | `int_policy_experience` | `policy_valuation.sas` Steps 2-3 | P1 |
| 11 | `int_customer_revenue` | `customer_profitability.sas` Steps 1-3 | P1 |
| 12 | `mart_risk_migration` | `credit_risk_scoring.sas` Step 3 | P0 |
| 13 | `mart_risk_summary` | `credit_risk_scoring.sas` Step 5 | P0 |
| 14 | `mart_claims_adjudicated` | `claims_processing.sas` Step 3 | P1 |
| 15 | `mart_fraud_alerts` | `claims_processing.sas` Step 4 | P1 |
| 16 | `mart_policy_valuation` | `policy_valuation.sas` Step 4 | P1 |
| 17 | `mart_loss_ratio_summary` | `policy_valuation.sas` Step 5 | P1 |
| 18 | `mart_monthly_rwa` | `monthly_regulatory_reporting.sas` Step 1 | P1 |
| 19 | `mart_delinquency_aging` | `monthly_regulatory_reporting.sas` Step 2 | P1 |
| 20 | `mart_llp_coverage` | `monthly_regulatory_reporting.sas` Step 3 | P1 |
| 21 | `mart_capital_adequacy` | `monthly_regulatory_reporting.sas` Step 5 | P1 |
| 22 | `mart_customer_pnl` | `customer_profitability.sas` Step 4 | P1 |
| 23 | `mart_segment_profitability` | `customer_profitability.sas` Step 5 | P1 |
| 24 | `mart_reserve_adequacy` | `policy_valuation.sas` (reserve output) | P2 |

### Macros Not Yet Created

| # | dbt Macro Needed | SAS Format | Type |
|---|-----------------|-----------|------|
| 1 | `format_risk_rating` | `RISKRATE` | Numeric (7 values) |
| 2 | `format_delinquency_bucket` | `DELQBKT` | Numeric range (7 buckets) |
| 3 | `format_balance_range` | `BALRANGE` | Numeric range (8 buckets) |
| 4 | `format_region` | `$REGION` | Character (7 values) |
| 5 | `format_loan_purpose` | `$LNPURP` | Character (8 values) |
| 6 | `format_policy_type` | `$POLTYPE` | Character (13 values) |
| 7 | `format_claim_status` | `$CLMSTAT` | Character (12 values) |
| 8 | `format_risk_category` | `$RISKCAT` | Character (5 values) |
| 9 | `format_coverage_type` | `$COVTYPE` | Character (9 values) |
| 10 | `format_loss_range` | `LOSSRANGE` | Numeric range (7 buckets) |

### Infrastructure Not Yet Created

| # | Component | Purpose |
|---|-----------|---------|
| 1 | Unity Catalog foreign catalog — Oracle | Replace `ORA_DW` LIBNAME |
| 2 | Unity Catalog foreign catalog — Teradata | Replace `TERA_DW` LIBNAME |
| 3 | Auto Loader configuration — transactions | Replace `RAW_BANK.TXN_FEED_*` |
| 4 | Auto Loader configuration — claims | Replace `RAW_INS.CLAIMS_FEED_*` |
| 5 | Databricks Secrets — Oracle credentials | Replace `&ora_uid`/`&ora_pwd` |
| 6 | Databricks Secrets — Teradata credentials | Replace `&tera_uid`/`&tera_pwd` |
| 7 | Databricks Workflow — Banking daily | Replace `run_daily_banking.sas` |
| 8 | Databricks Workflow — Insurance daily | Replace `run_daily_insurance.sas` |
| 9 | Databricks Workflow — Monthly reporting | Replace monthly Control-M jobs |
| 10 | Export notebooks (Python) | Replace `%export_xlsx` for regulatory + profitability |
| 11 | Alerting configuration | Replace `%sendmail` for ops + SIU |

### Source YAML Files Needed

| # | File | Sources |
|---|------|---------|
| 1 | `models/staging/_staging_sources.yml` | **Exists** — needs insurance sources added |
| 2 | `models/staging/_insurance_sources.yml` | Policies, claims, premiums, fraud indicators |

### Schema/Test YAML Files Needed

| # | File | Purpose |
|---|------|---------|
| 1 | `models/staging/schema.yml` | Column tests, freshness, descriptions |
| 2 | `models/intermediate/schema.yml` | Not-null tests, relationship tests |
| 3 | `models/marts/schema.yml` | Accepted values, uniqueness tests |

---

## Coverage Matrix

| SAS Program | % Covered in dbt | Missing Components |
|-------------|:----------------:|-------------------|
| `load_customer_accounts` | ~40% | Exception routing, derived fields verification, summary stats |
| `daily_transaction_processing` | ~30% | Validation/rejection, enrichment join, running balance, full anomaly detection |
| `credit_risk_scoring` | ~20% | Feature assembly, WOE binning, PD/LGD/EAD, risk migration, risk summary |
| `monthly_regulatory_reporting` | 0% | All components |
| `claims_processing` | 0% | All components |
| `policy_valuation` | 0% | All components |
| `customer_profitability` | 0% | All components |
| `Batch orchestration` | 0% | Workflows, alerting, restart logic |
| **Overall Estate** | **~15%** | |
