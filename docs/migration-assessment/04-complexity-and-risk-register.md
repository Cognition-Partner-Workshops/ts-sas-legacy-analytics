# Migration Complexity Assessment & Risk Register

---

## Per-Program Complexity Scoring

Scoring criteria:
- **Data access**: Number of source systems, join complexity, external DB connections
- **Business logic**: Calculation complexity, branching rules, domain expertise required
- **SAS-specific patterns**: Constructs with no direct SQL equivalent (RETAIN, hash, recursive SET key=)
- **Testing burden**: Regulatory/audit requirements, numerical precision requirements

| Program | Data Access | Business Logic | SAS Patterns | Testing | Overall | Wave |
|---------|:-----------:|:--------------:|:------------:|:-------:|:-------:|:----:|
| `load_customer_accounts` | Medium (2 Oracle tables) | Medium (5 derived fields, 3 exceptions) | Low | Low | **Low-Medium** | 1 |
| `daily_transaction_processing` | Medium (file + staging) | High (validation, enrichment, anomaly) | High (RETAIN, PROC APPEND lock) | Medium | **High** | 1-2 |
| `credit_risk_scoring` | High (4-way join, correlated subquery) | High (WOE, logistic regression, PD/LGD/EAD) | Medium (WOE binning) | Critical (regulatory) | **High** | 2 |
| `monthly_regulatory_reporting` | Medium (staging + Oracle) | High (Basel III risk weights, capital adequacy) | Low (pure SQL) | Critical (regulatory) | **Medium-High** | 4 |
| `claims_processing` | Medium (file + hash + Teradata) | High (auto-adjudication decision tree) | High (hash object) | Medium | **High** | 3 |
| `policy_valuation` | Medium (3 internal + Teradata) | High (IBNR, loss ratio, combined ratio) | Low (MERGE = JOIN) | High (actuarial) | **Medium** | 3 |
| `customer_profitability` | Medium (staging + curated + Oracle) | Medium (P&L assembly, ROA) | Low (MERGE + PROC MEANS) | Medium | **Medium** | 4 |
| `Parent-Child-Index` | Low (inline data) | Medium (recursive hierarchy) | High (recursive SET key=) | Low | **Medium** | 5 |

---

## Risk Register

### R1: Credit Risk Model Numerical Parity (CRITICAL)

| Attribute | Detail |
|-----------|--------|
| **Risk** | WOE binning boundaries and logistic regression coefficients in `credit_risk_scoring.sas` must produce bit-identical PD/LGD/EAD values on Databricks |
| **Impact** | Regulatory non-compliance if risk scores diverge from validated model |
| **Likelihood** | Medium — floating-point differences between SAS and Spark are common |
| **Mitigation** | (1) Create validation dataset with known inputs/outputs from SAS production, (2) Run parallel scoring on Databricks and compare at 4+ decimal places, (3) Document all coefficient values in version-controlled config, (4) Establish tolerance thresholds with risk committee |
| **Owner** | Risk/Model Governance team + Migration team |

### R2: Running Balance Determinism (HIGH)

| Attribute | Detail |
|-----------|--------|
| **Risk** | SAS `RETAIN` + `BY ACCOUNT_ID TRANSACTION_DATE TRANSACTION_ID` guarantees deterministic row processing order. Spark SQL window functions require explicit `ORDER BY` and may produce different results if sort keys are not unique |
| **Impact** | Incorrect running balances, false overdraft anomalies |
| **Likelihood** | Medium — if TRANSACTION_ID is not strictly unique per account per date |
| **Mitigation** | (1) Verify TRANSACTION_ID uniqueness, (2) Use `SUM() OVER (PARTITION BY account_id ORDER BY transaction_date, transaction_id ROWS UNBOUNDED PRECEDING)`, (3) Add tiebreaker column if needed |

### R3: Hash Object Performance on Spark (MEDIUM)

| Attribute | Detail |
|-----------|--------|
| **Risk** | SAS hash object in `claims_processing.sas` loads active policies into memory for O(1) lookup. Naive SQL JOIN on Spark may cause shuffle |
| **Impact** | Performance degradation for large policy tables |
| **Likelihood** | Low-Medium — depends on policy table size |
| **Mitigation** | Use Spark broadcast join hint (`/*+ BROADCAST(policies) */`) for small-to-medium policy tables; if >10M rows, use bucketed join |

### R4: Oracle/Teradata Connectivity Migration (HIGH)

| Attribute | Detail |
|-----------|--------|
| **Risk** | 6 Oracle tables and 2 Teradata tables are accessed via SAS/ACCESS LIBNAME. Credentials use macro variables (`&ora_uid`, `&ora_pwd`, `&tera_uid`, `&tera_pwd`) |
| **Impact** | No data ingestion until connections are re-established on Databricks |
| **Likelihood** | Certain — SAS/ACCESS drivers do not exist on Databricks |
| **Mitigation** | (1) Use Databricks Lakehouse Federation for Oracle/Teradata, (2) Store credentials in Databricks Secrets, (3) Create Unity Catalog foreign catalogs, (4) Alternatively, migrate to nightly data lake ingestion via Airbyte/Fivetran |

### R5: Excel Report Generation (MEDIUM)

| Attribute | Detail |
|-----------|--------|
| **Risk** | `%export_xlsx` used by `monthly_regulatory_reporting` and `customer_profitability` produces multi-sheet Excel workbooks. dbt has no native Excel export |
| **Impact** | Regulatory report delivery gap during cutover |
| **Likelihood** | Certain — requires alternative implementation |
| **Mitigation** | (1) Create Python notebook in Databricks Workflow that reads mart tables and writes xlsx via openpyxl, (2) Or replace with Databricks SQL dashboard with PDF/CSV export |

### R6: Batch Orchestration Restart Logic (MEDIUM)

| Attribute | Detail |
|-----------|--------|
| **Risk** | Both batch orchestrators support `restart_from=` parameter for mid-pipeline recovery. This pattern needs equivalent in Databricks Workflows |
| **Impact** | Ops team cannot restart failed pipelines from point of failure |
| **Likelihood** | Low — Databricks Workflows supports task-level retry |
| **Mitigation** | Model each SAS step as a separate Workflow task with automatic retry and dependency edges |

### R7: Email Notification Migration (LOW-MEDIUM)

| Attribute | Detail |
|-----------|--------|
| **Risk** | `%sendmail` used in 5 places for operational alerts (batch failures, data quality exceptions, SIU fraud alerts). SMTP integration needs replacement |
| **Impact** | Loss of operational alerting during cutover |
| **Likelihood** | Certain — SMTP not available from Databricks |
| **Mitigation** | (1) Use Databricks SQL Alerts for data quality checks, (2) Webhook integration with PagerDuty/Slack for batch failures, (3) Workflow notification settings for task failures |

### R8: Dataset Locking Semantics (LOW)

| Attribute | Detail |
|-----------|--------|
| **Risk** | `%lock` macro used before `PROC APPEND` to prevent concurrent writes. Delta Lake provides ACID transactions natively |
| **Impact** | None — risk is that migration team over-engineers concurrency control |
| **Likelihood** | Low |
| **Mitigation** | Document that Delta Lake ACID replaces SAS locking; no custom implementation needed |

### R9: Production Data Volume Sizing (MEDIUM)

| Attribute | Detail |
|-----------|--------|
| **Risk** | Production logs show: 847K accounts, 2.3M daily transactions (67M cumulative), ~3.4K anomalies/day. Databricks cluster must be sized appropriately |
| **Impact** | Job timeouts or excessive cost if under/over-provisioned |
| **Likelihood** | Low |
| **Mitigation** | (1) Profile actual data volumes from production, (2) Start with autoscaling cluster, (3) Benchmark dbt runs against production-equivalent data |

### R10: Actuarial Table Dependency (MEDIUM)

| Attribute | Detail |
|-----------|--------|
| **Risk** | `policy_valuation.sas` references `TERA_DW.ACTUARIAL_TABLES` but the exact columns and calculation logic is not fully visible in the code. The current IBNR estimate uses a simplified 15% factor |
| **Impact** | Actuarial accuracy may depend on Teradata lookup values not captured in assessment |
| **Likelihood** | Medium — depends on whether production uses the simplified formula or more complex actuarial tables |
| **Mitigation** | (1) Interview actuarial team to document full IBNR methodology, (2) Extract actuarial tables to Delta Lake seed data, (3) Validate reserve calculations against SAS production output |

---

## Complexity Summary by Migration Wave

| Wave | Programs | Avg Complexity | Key Challenges |
|------|----------|:-------------:|----------------|
| **Wave 1** | `load_customer_accounts`, `daily_transaction_processing` (staging) | Medium-High | Oracle extract, RETAIN running balance, file feed ingestion |
| **Wave 2** | `credit_risk_scoring`, `daily_transaction_processing` (anomaly) | High | WOE binning, model coefficients, regulatory validation, Z-score |
| **Wave 3** | `claims_processing`, `policy_valuation` | Medium-High | Hash object, Teradata connection, IBNR actuarial logic |
| **Wave 4** | `monthly_regulatory_reporting`, `customer_profitability` | Medium | Basel III risk weights, Excel export replacement |
| **Wave 5** | Orchestration + decommission | Medium | Databricks Workflows, alerting, parallel run validation |
