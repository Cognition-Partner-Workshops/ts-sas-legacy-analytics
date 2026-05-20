# Migration Wave Plan: SAS → Databricks (dbt)

Phased migration plan mapping each SAS program to its target dbt model(s) in the `uc-data-migration-sas-to-databricks` repository.

---

## Wave Overview

```
 Wave 1 (Weeks 1-3)          Wave 2 (Weeks 3-6)         Wave 3 (Weeks 6-9)
 ─────────────────           ─────────────────           ─────────────────
 Formats (seed tables)       Credit risk scoring         Claims processing
 Account staging             Running balance             Policy valuation
 Transaction staging         Anomaly detection           Insurance formats
 Oracle connection setup     Risk migration matrix       Teradata connection
 File feed → Auto Loader     Regulatory validation       Fraud screening

 Wave 4 (Weeks 9-11)         Wave 5 (Weeks 11-13)
 ─────────────────           ─────────────────
 Regulatory reporting        Databricks Workflows
 Customer profitability      Alerting & monitoring
 Excel export replacement    Parallel run validation
 Branch/segment summaries    SAS decommission plan
```

---

## Wave 1: Foundations & Staging (Weeks 1-3)

### Objective
Establish data ingestion layer: format lookups, Oracle connectivity, file feed ingestion, and staging models.

### SAS Source → dbt Target Mapping

| SAS Source | dbt Model | Layer | Status | Notes |
|-----------|-----------|-------|--------|-------|
| `Formats/banking_formats.sas` ($ACCTTYPE) | `macros/format_account_type.sql` | macro | **Exists** | Verify completeness |
| `Formats/banking_formats.sas` ($ACCTSTAT) | `macros/format_account_status.sql` | macro | **Exists** | Verify completeness |
| `Formats/banking_formats.sas` ($CUSTSEG) | `macros/format_customer_segment.sql` | macro | **Exists** | Verify completeness |
| `Formats/banking_formats.sas` ($TXNCAT) | `macros/format_txn_category.sql` | macro | **Exists** | Verify completeness |
| `Formats/banking_formats.sas` (RISKRATE) | `macros/format_risk_rating.sql` | macro | **Create** | 7 numeric values |
| `Formats/banking_formats.sas` (DELQBKT) | `macros/format_delinquency_bucket.sql` | macro | **Create** | Range-based CASE |
| `Formats/banking_formats.sas` (BALRANGE) | `macros/format_balance_range.sql` | macro | **Create** | Range-based CASE |
| `Formats/banking_formats.sas` ($REGION) | `macros/format_region.sql` | macro | **Create** | 7 char values |
| `Formats/banking_formats.sas` ($LNPURP) | `macros/format_loan_purpose.sql` | macro | **Create** | 8 char values |
| `load_customer_accounts.sas` (Step 1: extract) | `models/staging/stg_cust_accounts.sql` | staging | **Exists** | Verify Oracle source config |
| `load_customer_accounts.sas` (Step 2: business rules) | `models/intermediate/int_account_metrics.sql` | intermediate | **Exists** | Add derived fields, exceptions |
| `load_customer_accounts.sas` (Step 3: exceptions) | `models/intermediate/int_account_exceptions.sql` | intermediate | **Create** | Exception detection logic |
| `daily_transaction_processing.sas` (Step 1: validate) | `models/staging/stg_daily_transactions.sql` | staging | **Exists** | Add validation/rejection logic |
| `daily_transaction_processing.sas` (Step 2: enrich) | `models/intermediate/int_txn_enriched.sql` | intermediate | **Create** | Join with account staging |
| File feed ingestion | Databricks Auto Loader config | infra | **Create** | Replace RAW_BANK flat file reads |

### Infrastructure Tasks
- [ ] Configure Unity Catalog foreign catalog for Oracle DW (`FINPROD.DW_BANKING`)
- [ ] Set up Databricks Secrets for Oracle credentials
- [ ] Configure Auto Loader for daily transaction feed files
- [ ] Verify/extend existing dbt macros for format lookups
- [ ] Define staging source YAML with freshness checks

### Acceptance Criteria
- `stg_cust_accounts` produces row counts matching SAS production (~847K)
- `stg_daily_transactions` validates and rejects at expected rates (~0.1%)
- All 9 banking format macros return correct mapped values
- Auto Loader ingests daily transaction CSV/fixed-width files

---

## Wave 2: Risk Analytics & Transaction Intelligence (Weeks 3-6)

### Objective
Port the core analytical logic: running balances, anomaly detection, credit risk scoring, and risk migration tracking.

### SAS Source → dbt Target Mapping

| SAS Source | dbt Model | Layer | Status | Notes |
|-----------|-----------|-------|--------|-------|
| `daily_transaction_processing.sas` (Step 3: running balance) | `models/intermediate/int_running_balances.sql` | intermediate | **Create** | `SUM() OVER` replacing RETAIN |
| `daily_transaction_processing.sas` (Step 4: anomaly detection) | `models/marts/mart_transaction_anomalies.sql` | marts | **Exists** | Verify Z-score logic, add OVERDRAFT/LARGE_WITHDRAWAL |
| `daily_transaction_processing.sas` (Step 5: curated load) | `models/marts/mart_daily_transactions.sql` | marts | **Exists** | Verify incremental merge config |
| `credit_risk_scoring.sas` (Step 1: feature assembly) | `models/intermediate/int_risk_features.sql` | intermediate | **Create** | 4-way join with latest bureau score |
| `credit_risk_scoring.sas` (Step 2: WOE + scoring) | `models/marts/mart_risk_scores.sql` | marts | **Exists** | Add WOE binning, PD/LGD/EAD calculation |
| `credit_risk_scoring.sas` (Step 3: risk migration) | `models/marts/mart_risk_migration.sql` | marts | **Create** | Upgrade/downgrade/stable classification |
| `credit_risk_scoring.sas` (Step 5: risk summary) | `models/marts/mart_risk_summary.sql` | marts | **Create** | Aggregation by type × rating |

### Key Technical Challenges

**Running Balance (RETAIN replacement)**:
```sql
-- SAS: RETAIN RUNNING_BALANCE; if first.ACCOUNT_ID then RUNNING_BALANCE = PRE_TXN_BALANCE;
-- dbt/Spark:
SELECT *,
  PRE_TXN_BALANCE + SUM(
    CASE
      WHEN TRANSACTION_TYPE IN ('DEP','INT','REF','REV') THEN TRANSACTION_AMOUNT
      WHEN TRANSACTION_TYPE IN ('WDR','PMT','FEE','CHG') THEN -ABS(TRANSACTION_AMOUNT)
      WHEN TRANSACTION_TYPE IN ('TRF','ADJ') THEN TRANSACTION_AMOUNT
      ELSE 0
    END
  ) OVER (
    PARTITION BY ACCOUNT_ID
    ORDER BY TRANSACTION_DATE, TRANSACTION_ID
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS RUNNING_BALANCE
FROM int_txn_enriched
```

**WOE Binning (model coefficients)**:
```sql
-- Port exact coefficient values from credit_risk_scoring.sas lines 96-155
-- Store as dbt vars or seed table for version control
CASE
  WHEN FICO_SCORE >= 760 THEN -1.204
  WHEN FICO_SCORE >= 720 THEN -0.812
  ...
END AS WOE_FICO
```

### Acceptance Criteria
- Running balance values match SAS `CURATED.RUNNING_BALANCES` for sampled accounts
- PD scores match SAS production output to 4 decimal places
- Risk migration matrix classifies identical accounts as UPGRADE/DOWNGRADE/STABLE
- Anomaly detection flags same transactions as SAS (Z-score > 3, overdraft, etc.)

---

## Wave 3: Insurance Domain (Weeks 6-9)

### Objective
Port the complete insurance pipeline: claims processing with fraud screening and policy valuation with IBNR reserves.

### SAS Source → dbt Target Mapping

| SAS Source | dbt Model | Layer | Status | Notes |
|-----------|-----------|-------|--------|-------|
| `Formats/insurance_formats.sas` (all 5) | `macros/format_policy_type.sql` etc. | macro | **Create** | 5 new format macros |
| `claims_processing.sas` (Step 1: validate) | `models/staging/stg_claims_feed.sql` | staging | **Create** | Validation rules |
| `claims_processing.sas` (Step 1: policy lookup) | `models/intermediate/int_claims_validated.sql` | intermediate | **Create** | JOIN replacing hash object |
| `claims_processing.sas` (Step 2: fraud screening) | `models/intermediate/int_claims_fraud_scored.sql` | intermediate | **Create** | Teradata fraud indicator join |
| `claims_processing.sas` (Step 3: auto-adjudication) | `models/marts/mart_claims_adjudicated.sql` | marts | **Create** | Decision tree as CASE WHEN |
| `claims_processing.sas` (Step 4: outputs) | `models/marts/mart_fraud_alerts.sql` | marts | **Create** | SIU alert generation |
| `policy_valuation.sas` (Step 1: in-force) | `models/staging/stg_policies_inforce.sql` | staging | **Create** | Active policy extraction |
| `policy_valuation.sas` (Steps 2-3: claims + premiums) | `models/intermediate/int_policy_experience.sql` | intermediate | **Create** | Claims + premium aggregation |
| `policy_valuation.sas` (Step 4: valuation) | `models/marts/mart_policy_valuation.sql` | marts | **Create** | Loss ratio, IBNR, reserves |
| `policy_valuation.sas` (Step 5: summary) | `models/marts/mart_loss_ratio_summary.sql` | marts | **Create** | LOB-level aggregation |

### Infrastructure Tasks
- [ ] Configure Unity Catalog foreign catalog for Teradata (`ANALYTICS`)
- [ ] Set up Databricks Secrets for Teradata credentials
- [ ] Configure Auto Loader for daily claims feed files
- [ ] Create source YAML for insurance staging sources

### Acceptance Criteria
- Claims auto-adjudication produces same APPR/DENY/PEND split as SAS
- Policy valuation loss ratios match SAS within 0.01%
- IBNR estimates match SAS production output
- Fraud alerts trigger for same claims (FRAUD_SCORE >= 80)

---

## Wave 4: Regulatory Reporting & Profitability (Weeks 9-11)

### Objective
Port regulatory aggregations and profitability analytics, including Excel export replacement.

### SAS Source → dbt Target Mapping

| SAS Source | dbt Model | Layer | Status | Notes |
|-----------|-----------|-------|--------|-------|
| `monthly_regulatory_reporting.sas` (Step 1: RWA) | `models/marts/mart_monthly_rwa.sql` | marts | **Create** | Basel III risk weights |
| `monthly_regulatory_reporting.sas` (Step 2: delinquency) | `models/marts/mart_delinquency_aging.sql` | marts | **Create** | Aging buckets |
| `monthly_regulatory_reporting.sas` (Step 3: LLP) | `models/marts/mart_llp_coverage.sql` | marts | **Create** | Provision coverage |
| `monthly_regulatory_reporting.sas` (Step 5: capital) | `models/marts/mart_capital_adequacy.sql` | marts | **Create** | CET1/Tier1/Total ratios |
| `monthly_regulatory_reporting.sas` (Step 4: xlsx) | `notebooks/export_regulatory_report.py` | notebook | **Create** | openpyxl multi-sheet |
| `customer_profitability.sas` (Steps 1-3) | `models/intermediate/int_customer_revenue.sql` | intermediate | **Create** | Interest + fee + ECL |
| `customer_profitability.sas` (Step 4: P&L) | `models/marts/mart_customer_pnl.sql` | marts | **Create** | Full P&L assembly |
| `customer_profitability.sas` (Step 5: summaries) | `models/marts/mart_segment_profitability.sql` | marts | **Create** | Segment/branch rollups |
| `customer_profitability.sas` (xlsx) | `notebooks/export_profitability_report.py` | notebook | **Create** | openpyxl |

### Acceptance Criteria
- RWA totals match SAS within $1
- Capital adequacy ratios match SAS within 0.01%
- Delinquency bucket counts match exactly
- Excel reports contain all required sheets with matching data

---

## Wave 5: Orchestration & Cutover (Weeks 11-13)

### Objective
Replace Control-M orchestration with Databricks Workflows, implement monitoring, run parallel validation, and plan SAS decommission.

### Tasks

| Task | Detail |
|------|--------|
| **Databricks Workflow: Banking** | 4-task DAG mirroring `run_daily_banking` step chain |
| **Databricks Workflow: Insurance** | 2-task DAG mirroring `run_daily_insurance` |
| **Databricks Workflow: Monthly** | Scheduled tasks for regulatory + profitability |
| **Alerting** | Workflow failure notifications → Slack/PagerDuty; SQL Alerts for data quality thresholds |
| **SIU Fraud Alert** | Webhook integration for high-risk claim alerts |
| **Parallel Run** | Run SAS and Databricks side-by-side for 2 weeks, compare outputs daily |
| **Validation Framework** | Automated row-count and value-comparison checks between SAS and dbt outputs |
| **Control-M Cutover** | Update Control-M to trigger Databricks Workflows API instead of SAS batch |
| **SAS Decommission** | Archive SAS programs, revoke Oracle/Teradata SAS credentials, shut down SAS server |

### Parallel Run Validation Checks

| Check | SAS Dataset | dbt Model | Comparison |
|-------|-----------|-----------|------------|
| Account count | `STG_BANK.CUST_ACCOUNTS_DAILY` | `stg_cust_accounts` | Row count ± 0 |
| Transaction count | `CURATED.DAILY_TRANSACTIONS` | `mart_daily_transactions` | Row count ± 0 |
| Anomaly count | `CURATED.TXN_ANOMALIES` | `mart_transaction_anomalies` | Row count ± 0 |
| PD scores | `CURATED.RISK_SCORES` | `mart_risk_scores` | Mean PD ± 0.0001 |
| RWA totals | `REPORTS.MONTHLY_RWA` | `mart_monthly_rwa` | Sum ± $1 |
| Loss ratios | `REPORTS.LOSS_RATIO_SUMMARY` | `mart_loss_ratio_summary` | Ratio ± 0.01% |
| Claims adjudication | `STG_INS.CLAIMS_REGISTER` | `mart_claims_adjudicated` | Result match 100% |
| Running balances | `CURATED.RUNNING_BALANCES` | `int_running_balances` | Balance ± $0.01 |

---

## Total dbt Model Count

| Layer | Existing | To Create | Total |
|-------|:--------:|:---------:|:-----:|
| Staging | 2 | 3 | 5 |
| Intermediate | 1 | 7 | 8 |
| Marts | 3 | 12 | 15 |
| Macros | 4 | 10 | 14 |
| Notebooks | 0 | 2 | 2 |
| **Total** | **10** | **34** | **44** |
