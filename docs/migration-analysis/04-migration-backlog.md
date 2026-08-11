# Migration Backlog Tickets

> Prioritized work items for migrating the SAS estate to a modern platform (dbt/Databricks/Snowflake).
> Each ticket includes scope, SAS source, target pattern, complexity, and acceptance criteria.

---

## Epic 1: Foundation & Environment Setup

### TICKET-001: Scaffold dbt Project Structure and Connection Profiles

**Priority:** P0 — Blocker for all other work
**Complexity:** S — Small
**Source:** `Config/autoexec.sas`

**Description:**
Create the dbt project skeleton mirroring the SAS library/layer architecture. Define profiles for Databricks (or Snowflake) connections replacing the 11 LIBNAME assignments and 2 database connections (Oracle, Teradata) in `autoexec.sas`.

**Acceptance Criteria:**
- [ ] `dbt_project.yml` with `models/staging/`, `models/intermediate/`, `models/marts/` directories
- [ ] Connection profile for target warehouse (replaces ORA_DW, TERA_DW LIBNAMEs)
- [ ] Project variables replacing global macro vars: `CURR_DT`, `PREV_YM`, `FY_START`, `ENVIRONMENT`, `REPORT_PATH`
- [ ] `dbt debug` passes with live connection
- [ ] Source definitions for all upstream tables (`sources.yml`)

---

### TICKET-002: Migrate Banking Format Catalogs to dbt Seeds

**Priority:** P0 — Blocker (formats referenced across banking programs)
**Complexity:** S — Small
**Source:** `Formats/banking_formats.sas` (9 formats, 131 lines)

**Description:**
Convert PROC FORMAT value definitions to dbt seed CSV files (one per format). These replace format-based lookups with `ref()` joins or CASE expressions.

| SAS Format | Seed Table | Rows |
|-----------|-----------|------|
| `$ACCTTYPE` | `seed_account_types` | 11 |
| `$ACCTSTAT` | `seed_account_status` | 8 |
| `RISKRATE` | `seed_risk_ratings` | 7 |
| `$TXNCAT` | `seed_txn_categories` | 10 |
| `DELQBKT` | `seed_delinquency_buckets` | 7 |
| `BALRANGE` | `seed_balance_ranges` | 8 |
| `$REGION` | `seed_regions` | 7 |
| `$CUSTSEG` | `seed_customer_segments` | 6 |
| `$LNPURP` | `seed_loan_purposes` | 8 |

**Acceptance Criteria:**
- [ ] 9 seed CSV files in `seeds/banking/`
- [ ] `dbt seed` loads all successfully
- [ ] `schema.yml` with accepted_values tests on code columns
- [ ] Macro or CASE helper for range-based formats (DELQBKT, BALRANGE)

---

### TICKET-003: Migrate Insurance Format Catalogs to dbt Seeds

**Priority:** P0 — Blocker (formats referenced in insurance programs)
**Complexity:** S — Small
**Source:** `Formats/insurance_formats.sas` (5 formats, 85 lines)

**Description:**
Convert insurance PROC FORMAT definitions to dbt seed tables.

| SAS Format | Seed Table | Rows |
|-----------|-----------|------|
| `$POLTYPE` | `seed_policy_types` | 13 |
| `$CLMSTAT` | `seed_claim_statuses` | 12 |
| `$RISKCAT` | `seed_risk_categories` | 5 |
| `$COVTYPE` | `seed_coverage_types` | 9 |
| `LOSSRANGE` | `seed_loss_ranges` | 7 |

**Acceptance Criteria:**
- [ ] 5 seed CSV files in `seeds/insurance/`
- [ ] `dbt seed` loads all successfully
- [ ] `schema.yml` with accepted_values tests

---

## Epic 2: Staging Layer — Data Ingestion (replaces DATA steps + Oracle/Teradata extracts)

### TICKET-004: Migrate load_customer_accounts to Staging Models

**Priority:** P1 — Critical path (all downstream depends on this)
**Complexity:** L — Large (216 lines, PROC SQL + DATA step + business rules + format refs + exception handling)
**Source:** `Programs/Banking/load_customer_accounts.sas`

**Description:**
Replace the Oracle DW extract (PROC SQL with INNER JOIN on CUST_ACCOUNTS + CUST_DEMOGRAPHICS) and business-rule DATA step with dbt staging models.

**SAS Constructs to Migrate:**
- PROC SQL: 2 blocks (Oracle extract, exception insert)
- DATA step: 1 block (derived columns: ACCT_AGE_MONTHS, DAYS_INACTIVE, UTILIZATION_PCT, DORMANCY_FLAG, HIGH_BALANCE_FLAG + 3 exception rules)
- PROC MEANS: 1 block (summary statistics by ACCOUNT_TYPE × REGION_CODE)
- Macros: `%parmv`, `%nobs`, `%sendmail`
- Formats: `$ACCTTYPE`, `$ACCTSTAT`, `RISKRATE`, `$CUSTSEG`, `$REGION`

**Target Models:**
- `stg_cust_accounts_daily.sql` — Extract + business rules + derived columns
- `stg_acct_exceptions.sql` — Data quality exception capture
- `stg_acct_summary.sql` — Summary statistics (replaces PROC MEANS)

**Acceptance Criteria:**
- [ ] Models build and pass `dbt test`
- [ ] Row counts match SAS output (use `%nobs` equivalent dbt test)
- [ ] All 5 format references resolved to seed joins or CASE expressions
- [ ] Exception rules produce equivalent output
- [ ] Alerting for >100 exceptions (replaces `%sendmail`) — defer to TICKET-019

---

### TICKET-005: Migrate daily_transaction_processing to Staging + Intermediate Models

**Priority:** P1 — Critical path
**Complexity:** XL — Extra Large (246 lines, DATA step validation, PROC SQL enrichment, RETAIN running balance, anomaly detection, PROC APPEND with locking)
**Source:** `Programs/Banking/daily_transaction_processing.sas`

**SAS Constructs to Migrate:**
- DATA steps: 3 blocks (validation with split output, running balance with RETAIN, balance persistence)
- PROC SQL: 3 blocks (enrichment join, rolling statistics, anomaly detection with Z-score)
- RETAIN: `RUNNING_BALANCE` with BY-group reset on `first.ACCOUNT_ID`
- PROC APPEND: 2 blocks (with `%lock` for CURATED.DAILY_TRANSACTIONS)
- Macros: `%parmv`, `%nobs`, `%lock`

**Target Models:**
- `stg_txn_validated.sql` — Input validation (replaces DATA step validation logic)
- `int_txn_enriched.sql` — Account enrichment join
- `int_txn_running_balance.sql` — `SUM() OVER (PARTITION BY account_id ORDER BY ...)` window function replacing RETAIN
- `int_txn_anomalies.sql` — Z-score anomaly detection, overdraft flagging
- Incremental model config replacing PROC APPEND + `%lock`

**Acceptance Criteria:**
- [ ] Running balance matches SAS RETAIN output within ±$0.01
- [ ] Anomaly detection logic (Z-score > 3, OVERDRAFT, LARGE_WITHDRAWAL, ORPHAN_ACCOUNT) equivalent
- [ ] Incremental materialization replaces PROC APPEND pattern
- [ ] Dataset locking no longer needed (handled by warehouse transactions)

---

### TICKET-006: Migrate claims_processing to Staging + Intermediate Models

**Priority:** P1 — Critical path for insurance pipeline
**Complexity:** XL — Extra Large (238 lines, hash object, Teradata join, auto-adjudication rules, fraud screening)
**Source:** `Programs/Insurance/claims_processing.sas`

**SAS Constructs to Migrate:**
- DATA steps: 4 blocks (hash validation, fraud alerts, auto-adjudication, claim combining)
- **Hash object**: `declare hash h_pol` loaded from `RAW_INS.POLICIES(where=(STATUS='ACTIVE'))` — keyed on POLICY_ID, validates policy existence + date range + sum insured
- PROC SQL: 1 block (fraud screening LEFT JOIN to Teradata)
- PROC APPEND: 3 blocks (claims register, review queue, fraud alerts)
- Formats: `$CLMSTAT`
- Macros: `%parmv`, `%nobs`, `%sendmail`

**Target Models:**
- `stg_claims_validated.sql` — Replace hash lookup with SQL LEFT JOIN to active policies
- `int_claims_fraud_screening.sql` — Fraud indicator join (replaces Teradata cross-platform query)
- `int_claims_adjudicated.sql` — Auto-adjudication rules as CASE WHEN
- `int_claims_review_queue.sql` — Manual review subset
- `int_fraud_alerts.sql` — High-risk claim alerts

**Acceptance Criteria:**
- [ ] Hash object validation replaced with equivalent LEFT JOIN + IS NULL check
- [ ] Auto-adjudication logic (deny/approve/manual thresholds) matches SAS output
- [ ] Fraud alert notification replaced with Databricks alert (see TICKET-019)

---

### TICKET-007: Migrate policy_valuation to Staging + Intermediate Models

**Priority:** P1
**Complexity:** L — Large (206 lines, 3-way MERGE, PROC SQL extracts, PROC MEANS, actuarial calculations)
**Source:** `Programs/Insurance/policy_valuation.sas`

**SAS Constructs to Migrate:**
- PROC SQL: 3 blocks (in-force extract with date arithmetic, claims experience 12-month window, premium collections)
- DATA step: 2 blocks (3-way MERGE with loss ratio/combined ratio/IBNR/reserve calcs, aggregate loss ratios)
- PROC MEANS: 1 block (loss ratio summary by POLICY_TYPE)
- Formats: `$POLTYPE`, `$RISKCAT`
- Macros: `%parmv`, `%nobs`

**Target Models:**
- `stg_inforce_policies.sql` — In-force extract with earned premium calculation
- `int_claims_experience.sql` — 12-month claims aggregation
- `int_premium_collections.sql` — Premium collection aggregation
- `int_policy_valuation.sql` — Joined valuation metrics (replaces 3-way MERGE)
- `marts_loss_ratio_summary.sql` — Aggregated loss ratios by LOB

**Acceptance Criteria:**
- [ ] Earned premium pro-rata calculation matches SAS within ±$0.01
- [ ] IBNR estimate formula replicated: `max(0, earned_premium * 0.15 - total_paid)`
- [ ] Combined ratio = loss ratio + 0.30 expense load

---

## Epic 3: Intermediate Layer — Business Logic & Scoring

### TICKET-008: Migrate credit_risk_scoring to Intermediate Models

**Priority:** P1
**Complexity:** XL — Extra Large (270 lines, WOE scorecard, PD/LGD/EAD, multi-table assembly, risk migration matrix)
**Source:** `Programs/Banking/credit_risk_scoring.sas`

**SAS Constructs to Migrate:**
- PROC SQL: 2 blocks (4-way feature assembly with correlated subquery, risk migration matrix)
- DATA step: 1 block (WOE binning → log-odds → PD → LGD → EAD → expected loss → risk rating; 130+ lines of model logic)
- PROC APPEND: 2 blocks (with `%lock`)
- PROC MEANS: 1 block (risk summary)
- Macros: `%parmv`, `%nobs`, `%lock`

**Target Models:**
- `int_score_input.sql` — Feature assembly (4-way join replacing correlated subquery with window function)
- `int_risk_scored.sql` — WOE scorecard as CASE WHEN chains → PD/LGD/EAD calculation
- `int_risk_migration.sql` — Rating migration matrix
- `marts_risk_summary.sql` — Aggregated risk summary (replaces PROC MEANS)

**Acceptance Criteria:**
- [ ] WOE bin boundaries match model CRM-2023-Q4-v2 coefficients exactly
- [ ] PD = 1 / (1 + exp(-log_odds)) formula preserved
- [ ] LGD, EAD, Expected Loss formulas match within floating point tolerance
- [ ] Risk rating bands (PD thresholds: 0.5%, 1%, 3%, 7%, 15%, 30%) preserved
- [ ] Risk migration direction logic (NEW/UPGRADE/DOWNGRADE/STABLE) equivalent

---

## Epic 4: Marts Layer — Regulatory Reporting & Analytics

### TICKET-009: Migrate monthly_regulatory_reporting to Marts Models

**Priority:** P1
**Complexity:** L — Large (199 lines, 4 PROC SQL blocks + export)
**Source:** `Programs/Banking/monthly_regulatory_reporting.sas`

**SAS Constructs to Migrate:**
- PROC SQL: 4 blocks (RWA, delinquency aging, LLP coverage, capital adequacy)
- `%export_xlsx`: 3 calls (multi-sheet Excel for regulators)
- Macros: `%parmv`, `%nobs`, `%export_xlsx`

**Target Models:**
- `marts_monthly_rwa.sql` — Risk-weighted assets by category
- `marts_delinquency_aging.sql` — 30/60/90/120/180+ buckets
- `marts_llp_coverage.sql` — Loan loss provision coverage
- `marts_capital_adequacy.sql` — CET1/Tier1/Total capital ratios with pass/fail

**Acceptance Criteria:**
- [ ] Basel III risk weights match SAS CASE WHEN exactly
- [ ] Delinquency buckets identical
- [ ] Capital adequacy pass/fail thresholds: CET1 ≥ 4.5%, Tier1 ≥ 6%, Total ≥ 8%
- [ ] Excel export replaced with Databricks notebook or Python openpyxl (TICKET-017)

---

### TICKET-010: Migrate customer_profitability to Marts Models

**Priority:** P2
**Complexity:** M — Medium (176 lines, 3 PROC SQL + DATA step MERGE + 2 PROC MEANS)
**Source:** `Programs/Reports/customer_profitability.sas`

**SAS Constructs to Migrate:**
- PROC SQL: 3 blocks (interest income, fee income, expected credit loss)
- DATA step: 1 block (3-way MERGE, P&L assembly, profitability tier)
- PROC MEANS: 2 blocks (segment profitability, branch profitability)
- `%export_xlsx`: 1 call
- Macros: `%parmv`, `%nobs`, `%export_xlsx`

**Target Models:**
- `marts_customer_pnl.sql` — Full customer P&L (replaces 3-way MERGE)
- `marts_segment_profitability.sql` — Segment-level aggregation
- `marts_branch_profitability.sql` — Branch-level aggregation

**Acceptance Criteria:**
- [ ] Operating cost allocation formula: $15/account/month
- [ ] ROA = (NET_PROFIT × 12) / TOTAL_RELATIONSHIP
- [ ] Profitability tiers: Highly Profitable (≥$500), Profitable (≥$100), Marginal (≥$0), Unprofitable (<$0)

---

## Epic 5: Macro Library Migration

### TICKET-011: Migrate Core Utility Macros to dbt Macros

**Priority:** P1 — Required by all models
**Complexity:** M — Medium (5 macros)

**Macros to Migrate:**
| SAS Macro | dbt Equivalent |
|-----------|---------------|
| `%parmv` | dbt macro with `exceptions.raise_compiler_error()` |
| `%nobs` | dbt `{{ get_row_count(ref('model')) }}` macro |
| `%lock` | Not needed — warehouse handles concurrency |
| `%sendmail` | Databricks alerts / external webhook |
| `%export_xlsx` | Python openpyxl task or Databricks notebook |

**Acceptance Criteria:**
- [ ] `parmv.sql` macro validates required variables at compile time
- [ ] `get_row_count.sql` macro returns observation count for any ref
- [ ] Documented decision: lock/sendmail/export_xlsx handled outside dbt

---

### TICKET-012: Migrate Hash Object Macros to Python/SQL Patterns

**Priority:** P2
**Complexity:** S — Small (3 macros)

**Macros to Migrate:**
| SAS Macro | Target Pattern |
|-----------|---------------|
| `%hash_define` + `%hash_lookup` | SQL LEFT JOIN or Spark broadcast join |
| `%hash_split_dataset` | `INSERT INTO ... SELECT ... WHERE` partitioned writes |

**Acceptance Criteria:**
- [ ] All hash-based lookups replaced with SQL joins in relevant models
- [ ] Performance validated (broadcast join for small dimension tables)

---

### TICKET-013: Migrate %seplist and String Macros to dbt/Jinja

**Priority:** P2
**Complexity:** S — Small

| SAS Macro | dbt Equivalent |
|-----------|---------------|
| `%seplist` | Jinja `{{ columns \| join(', ') }}` or custom macro |
| `%count_words` | Jinja `{{ var.split() \| length }}` |
| `%squote` | Jinja `'{{ var }}'` |
| `%dedup_mstring` | Jinja `{{ var.split() \| unique \| join(' ') }}` |

**Acceptance Criteria:**
- [ ] dbt macro `seplist.sql` replicates `%seplist` prefix/delimiter behavior
- [ ] Used in at least one migrated model to validate

---

### TICKET-014: Document Unmigrated Macro Library (68 macros)

**Priority:** P3 — Backlog
**Complexity:** S — Small

**Description:**
The remaining ~68 macros in `Macro/` are not directly invoked by the 7 main programs. Catalog them with migration notes for each category:

| Category | Count | Migration Note |
|----------|-------|---------------|
| Export variants (SPSS, Stata, SAPHARI, etc.) | 7 | Replaced by warehouse-native exports |
| Flow control (RunAll, batch_submit, loop variants) | 5 | Replaced by Databricks Workflows / dbt run |
| Environment utilities (kill, delete_file, dirlist, etc.) | 8 | OS-level; not needed in cloud warehouse |
| Connectivity (libname_sqlsvr, queryActiveDirectory, etc.) | 5 | Replaced by Unity Catalog / SSO |
| Reporting (pagexofy, align_decimals, txt2pdf, etc.) | 7 | Replaced by BI tools (Tableau, Power BI) |
| Others (age, bench, marker, reduce_pixel, etc.) | 36 | Case-by-case assessment |

**Acceptance Criteria:**
- [ ] Each macro has a one-line migration recommendation
- [ ] Macros with no business-program callers flagged as "archive candidates"

---

## Epic 6: Orchestration & Operations

### TICKET-015: Replace Batch Orchestrators with Databricks Workflows

**Priority:** P1 — Required for production deployment
**Complexity:** M — Medium
**Source:** `BatchJobs/run_daily_banking.sas` (161 lines), `BatchJobs/run_daily_insurance.sas` (133 lines)

**SAS Constructs to Replace:**
- `%include` chain with error handling → Workflow DAG task dependencies
- `%run_step` macro with `&SYSCC` checking → Task-level success/failure handling
- `WORK.BATCH_CONTROL` tracking table → Workflow run history
- `PROC APPEND base=ARCHIVE.BATCH_HISTORY` → Workflow audit log
- `&ABORT_ON_ERR` / `&restart_from` logic → Workflow retry/restart policies

**Target Architecture:**
```
Banking Workflow (daily 05:45)
  Task 1: dbt run --select stg_cust_accounts_daily
  Task 2: dbt run --select int_txn_* (depends on Task 1)
  Task 3: dbt run --select int_risk_* (depends on Task 2)
  Task 4: dbt run --select marts_monthly_* (depends on Task 3, monthly gate)
  On-failure: alert via PagerDuty/email

Insurance Workflow (daily 07:00)
  Task 1: dbt run --select stg_claims_* int_claims_*
  Task 2: dbt run --select int_policy_valuation marts_loss_ratio (depends on Task 1)
  On-failure: alert
```

**Acceptance Criteria:**
- [ ] Databricks Workflow JSON definitions for both pipelines
- [ ] Dependency chain matches SAS step ordering
- [ ] Restart-from-step capability configured
- [ ] Batch control history accessible via Workflow run API

---

### TICKET-016: Replace Control-M Scheduling with Databricks Triggers

**Priority:** P2
**Complexity:** S — Small

**Description:**
Map Control-M job schedules to Databricks Workflow triggers.

| Control-M Job | Schedule | Databricks Trigger |
|--------------|----------|-------------------|
| `BANK_MASTER` | Daily 05:45 | Cron: `45 5 * * *` |
| `BANK_DAILY_01` | Daily 06:00 | Task within banking workflow |
| `BANK_DAILY_02` | Daily 07:30 | Task within banking workflow |
| `BANK_WEEKLY_01` | Weekly Sun 02:00 | Separate workflow, cron: `0 2 * * 0` |
| `BANK_MONTHLY_01` | Monthly 3rd bday | Separate workflow with calendar trigger |
| `BANK_MONTHLY_03` | Monthly 10th bday | Separate workflow with calendar trigger |
| `INS_MASTER` | Daily 07:00 | Cron: `0 7 * * *` |
| `INS_DAILY_01` | Daily 08:00 | Task within insurance workflow |
| `INS_MONTHLY_01` | Monthly 5th bday | Separate workflow with calendar trigger |

**Acceptance Criteria:**
- [ ] All 9 Control-M jobs mapped to Databricks triggers
- [ ] Business-day logic for monthly jobs implemented

---

### TICKET-017: Replace Excel Exports with Databricks Notebooks

**Priority:** P2
**Complexity:** M — Medium
**Source:** 4 `%export_xlsx` calls across 2 programs

**Description:**
Replace SAS `%export_xlsx` macro calls with Python notebook tasks or openpyxl scripts in the Databricks workflow.

| Current Export | File | Sheets |
|---------------|------|--------|
| Regulatory report | `REG_REPORT_YYYYMM.xlsx` | RWA, Delinquency, LLP_Coverage |
| Profitability report | `PROFITABILITY_YYYYMM.xlsx` | By_Segment |

**Acceptance Criteria:**
- [ ] Python notebook generates multi-sheet Excel with identical layout
- [ ] Files written to cloud storage (S3/ADLS) replacing `/data/sas/reports/output/`
- [ ] Integrated as post-run task in Databricks workflow

---

### TICKET-018: Replace Dataset Locking with Delta Lake Transactions

**Priority:** P2
**Complexity:** S — Small

**Description:**
The `%lock` macro is used in 2 programs (3 lock/unlock pairs) to prevent concurrent writes to CURATED tables. Delta Lake's ACID transactions and MERGE operations eliminate this need.

| SAS Pattern | Delta Lake Replacement |
|------------|----------------------|
| `%lock(CURATED.DAILY_TRANSACTIONS)` + `PROC APPEND` + `%lock(unlock)` | `MERGE INTO` or incremental model |
| `%lock(CURATED.RISK_SCORES)` + `PROC APPEND` | Incremental model with `unique_key` |
| `%lock(CURATED.RISK_MIGRATION)` + `PROC APPEND` | Incremental model |

**Acceptance Criteria:**
- [ ] All PROC APPEND + lock patterns replaced with dbt incremental models
- [ ] Concurrent write safety confirmed via Delta Lake documentation

---

### TICKET-019: Replace Email Notifications with Databricks Alerts

**Priority:** P3
**Complexity:** S — Small

**Description:**
Replace `%sendmail` calls (4 programs) with Databricks SQL Alerts or PagerDuty integration.

| SAS Call | Trigger | Replacement |
|---------|---------|-------------|
| `load_customer_accounts` | >100 exceptions | SQL Alert on exception count |
| `claims_processing` | Fraud alerts detected | SQL Alert + PagerDuty |
| `run_daily_banking` | Step failure | Workflow failure notification |
| `run_daily_banking` | Batch summary | Workflow completion notification |
| `run_daily_insurance` | Step failure | Workflow failure notification |

**Acceptance Criteria:**
- [ ] Databricks SQL Alert definitions for exception and fraud thresholds
- [ ] Workflow notifications configured for failure and completion
- [ ] Notification targets: replaces `&EMAIL_DL` and `&EMAIL_ONCALL`

---

## Epic 7: Testing & Validation

### TICKET-020: Build dbt Test Suite Mirroring SAS Business Rules

**Priority:** P1
**Complexity:** M — Medium

**Description:**
Create dbt tests that encode the same business rules currently embedded in SAS DATA step logic.

| SAS Business Rule | dbt Test |
|-------------------|----------|
| Negative balance on deposit accounts → exception | `test_no_negative_deposit_balances` |
| Credit utilization > 95% → exception | `test_utilization_threshold` |
| Missing risk rating → exception | `not_null` test on `risk_rating` |
| Transaction validation (required fields, amount range, valid type) | `not_null`, `accepted_values`, custom range test |
| Future-dated transactions rejected | Custom test: `transaction_date <= current_date` |
| Claims: policy must be active | `relationships` test to active policies |
| Claims: loss date within policy period | Custom date range test |
| Claims: claimed amount ≤ sum insured | Custom comparison test |

**Acceptance Criteria:**
- [ ] All 8+ business rules have corresponding dbt tests
- [ ] Tests run in CI (GitHub Actions) on every PR
- [ ] Zero test failures on production data

---

### TICKET-021: Build Reconciliation Framework (SAS vs. dbt Output Comparison)

**Priority:** P1
**Complexity:** L — Large

**Description:**
Create a parallel-run comparison framework to validate that dbt models produce identical output to SAS programs during the migration transition period.

**Key Metrics to Reconcile:**
- Row counts per model vs. SAS `%nobs` output
- Sum of CURRENT_BALANCE, TRANSACTION_AMOUNT, EXPECTED_LOSS
- Count of exceptions, anomalies, fraud alerts
- Risk rating distribution (rating 1-7 counts)
- Delinquency bucket totals
- Loss ratio aggregates

**Acceptance Criteria:**
- [ ] Reconciliation notebook compares SAS log output vs. dbt results
- [ ] Automated tolerance checks (exact for counts, ±$0.01 for currency, ±0.0001 for ratios)
- [ ] Dashboard showing reconciliation status per model

---

### TICKET-022: Migrate Parent-Child-Index Pattern to Recursive CTE

**Priority:** P3
**Complexity:** M — Medium
**Source:** `Programs/Parent-Child-Index.sas` (286 lines)

**SAS Constructs to Migrate:**
- INDEX KEY= recursive lookups for hierarchy traversal
- PROC SUMMARY with TYPES (lev:) for multi-level aggregation
- Hash object join (`%hash_define` / `%hash_lookup`) for dimension lookup
- Dynamic code generation via PROC CONTENTS + SELECT INTO

**Target:**
- Recursive CTE (`WITH RECURSIVE`) for hierarchy traversal
- GROUP BY ROLLUP/CUBE for multi-level aggregation
- Standard SQL JOIN replacing hash lookup

**Acceptance Criteria:**
- [ ] Recursive CTE produces identical hierarchy to SAS KEY= traversal
- [ ] Multi-level aggregation matches PROC SUMMARY output
- [ ] Dynamic column handling via Jinja macro

---

## Summary

| Priority | Ticket Count | Estimated Effort |
|----------|-------------|-----------------|
| P0 (Blockers) | 3 | 1 sprint |
| P1 (Critical) | 9 | 3-4 sprints |
| P2 (Important) | 5 | 2 sprints |
| P3 (Backlog) | 5 | 2 sprints |
| **Total** | **22** | **8-9 sprints** |

### Recommended Sprint Sequence

1. **Sprint 1:** TICKET-001 (scaffold), TICKET-002 (banking formats), TICKET-003 (insurance formats)
2. **Sprint 2:** TICKET-004 (load_customer_accounts), TICKET-011 (core macros)
3. **Sprint 3:** TICKET-005 (transactions — RETAIN/running balance), TICKET-006 (claims — hash object)
4. **Sprint 4:** TICKET-007 (policy valuation), TICKET-008 (credit risk scoring)
5. **Sprint 5:** TICKET-009 (regulatory reporting), TICKET-010 (profitability), TICKET-020 (test suite)
6. **Sprint 6:** TICKET-015 (workflows), TICKET-016 (scheduling), TICKET-021 (reconciliation)
7. **Sprint 7:** TICKET-012, TICKET-013, TICKET-017, TICKET-018
8. **Sprint 8:** TICKET-014, TICKET-019, TICKET-022
