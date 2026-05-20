# SAS-to-Databricks Migration Assessment: Executive Summary

**Assessment Date:** 2026-05-20
**Source Platform:** SAS 9.4 M7 on Linux (RHEL 7)
**Target Platform:** Databricks (Unity Catalog, dbt, Delta Lake)
**Target Repository:** `uc-data-migration-sas-to-databricks`

---

## Estate Overview

| Metric | Count |
|--------|-------|
| Total SAS files | 105 |
| Business programs (ETL/Reporting) | 8 |
| Shared macro utilities | 92 |
| Batch orchestrators | 2 |
| Format catalogs | 2 |
| Configuration files | 1 |
| Lines of code (all `.sas` files) | ~27,400 |
| Lines of code (business programs only) | ~1,790 |

## Domains

| Domain | Programs | Criticality | Schedule |
|--------|----------|------------|----------|
| **Banking ETL** | 4 programs | High | Daily 05:45 (Control-M `BANK_MASTER`) |
| **Insurance ETL** | 2 programs | High | Daily 07:00 (Control-M `INS_MASTER`) |
| **Reporting** | 1 program | Medium | Monthly (Control-M `BANK_MONTHLY_03`) |
| **Utility/Hierarchical** | 1 program | Low | Ad-hoc |

## External Dependencies

| Dependency | Type | Replacement in Databricks |
|------------|------|--------------------------|
| Oracle DW (`FINPROD.DW_BANKING`) | RDBMS (SAS/ACCESS) | Unity Catalog external tables / Lakehouse Federation |
| Teradata (`tdprod.internal.corp/ANALYTICS`) | RDBMS (SAS/ACCESS) | Unity Catalog external tables / Lakehouse Federation |
| File-based feeds (CSV/fixed-width) | Flat files | Auto Loader / COPY INTO |
| Control-M | Job scheduler | Databricks Workflows |
| SMTP email alerts | Notifications | Databricks SQL Alerts / PagerDuty / SNS |
| SAS format catalogs | Metadata | dbt seed tables + CASE macros |

## Migration Readiness Score

| Category | Score | Notes |
|----------|-------|-------|
| **Data Layer Complexity** | Medium | 14 library references, 2 external DBs, file feeds |
| **Code Complexity** | Medium-High | WOE scorecards, hash objects, running balances, PROC APPEND locking |
| **Orchestration Complexity** | Medium | 2 batch chains (4+2 steps), error handling, restart logic |
| **Format/Metadata Complexity** | Low | 9 banking + 5 insurance formats, all value-based |
| **Macro Dependency Depth** | Medium | 92 macros, but only ~8 used by business programs |

**Overall Migration Complexity: MEDIUM**

## Recommended Migration Waves

| Wave | Scope | Estimated Effort | Priority |
|------|-------|-----------------|----------|
| **Wave 1** | Formats + staging models (account load, transaction ingest) | 2-3 weeks | P0 |
| **Wave 2** | Credit risk scoring, running balances, anomaly detection | 2-3 weeks | P0 |
| **Wave 3** | Insurance (claims processing, policy valuation) | 2-3 weeks | P1 |
| **Wave 4** | Regulatory reporting + profitability (Excel exports) | 1-2 weeks | P1 |
| **Wave 5** | Orchestration (Databricks Workflows), alerting, decommission | 1-2 weeks | P2 |

## Key Risks

1. **Scorecard model parity**: WOE binning and logistic regression coefficients must produce identical PD/LGD/EAD values on Databricks.
2. **Running balance ordering**: SAS `RETAIN` + `BY` group processing depends on deterministic sort order; Spark window functions need explicit `ORDER BY`.
3. **Hash object lookups**: The claims processing hash-based policy lookup must be replaced with broadcast joins or map-side joins in Spark.
4. **PROC APPEND locking semantics**: SAS dataset locks have no direct equivalent; Delta Lake MERGE/APPEND is the target pattern.
5. **Data volume**: Production logs show 847K accounts and 2.3M daily transactions (67M cumulative). Confirm Databricks cluster sizing.
6. **Oracle/Teradata credential migration**: Connection strings and credential vaulting need replanning for Databricks Secrets.

## Existing dbt Coverage

The target repo (`uc-data-migration-sas-to-databricks`) already contains partial dbt models:

| dbt Layer | Models | Covers |
|-----------|--------|--------|
| staging | `stg_cust_accounts`, `stg_daily_transactions` | Wave 1 (partial) |
| intermediate | `int_account_metrics` | Wave 2 (partial) |
| marts | `mart_risk_scores`, `mart_daily_transactions`, `mart_transaction_anomalies` | Waves 2-4 (partial) |
| macros | `format_account_type`, `format_account_status`, `format_customer_segment`, `format_txn_category` | 4 of 14 format lookups |

**Gap**: No insurance models, no regulatory reporting, no profitability analytics, no IBNR/loss-ratio logic, no orchestration.
