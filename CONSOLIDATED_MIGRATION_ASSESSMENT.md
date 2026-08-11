# Consolidated SAS Migration Assessment

> **Scope:** 7 SAS programs across 3 domains (1,551 total lines)
> **Repository:** `ts-sas-legacy-analytics`
> **Config:** `Config/autoexec.sas` | **Formats:** `Formats/banking_formats.sas`, `Formats/insurance_formats.sas`
> **Target Repos:** `uc-data-migration-sas-to-databricks` (dbt/Databricks), `uc-data-migration-sas-to-snowflake` (Snowflake validation)

---

## Table of Contents

1. [Cross-Domain Dataset Dependencies](#1-cross-domain-dataset-dependencies)
2. [Shared Macro Usage Across Domains](#2-shared-macro-usage-across-domains)
3. [Unified Migration Sequence](#3-unified-migration-sequence)
4. [Total Effort Estimate](#4-total-effort-estimate)
5. [Domain Summaries](#5-domain-summaries)
6. [Risk Register](#6-risk-register)

---

## 1. Cross-Domain Dataset Dependencies

### Complete Data Flow Graph

```
┌─────────────────── EXTERNAL SOURCES ──────────────────────┐
│                                                            │
│  Oracle DW (ORA_DW)         Teradata (TERA_DW)            │
│  ├── CUST_ACCOUNTS          ├── FRAUD_INDICATORS          │
│  ├── CUST_DEMOGRAPHICS      └── ACTUARIAL_TABLES (unused) │
│  ├── BUREAU_SCORES                                        │
│  ├── PAYMENT_HISTORY        RAW File Feeds                │
│  ├── COLLATERAL             ├── RAW_BANK.TXN_FEED_*       │
│  └── LOAN_DETAILS           ├── RAW_INS.CLAIMS_FEED_*     │
│                              ├── RAW_INS.POLICIES          │
└──────────────────────────────├── RAW_INS.CLAIMS            │
                               └── RAW_INS.PREMIUMS          │
                                                             │
┌─────────────────── BANKING DOMAIN ────────────────────────┐
│                                                            │
│  [1] load_customer_accounts.sas                            │
│       └──▶ STG_BANK.CUST_ACCOUNTS_DAILY ─────────┐        │
│            STG_BANK.ACCT_EXCEPTIONS               │        │
│                                                   ▼        │
│  [2] daily_transaction_processing.sas ◀───────────┤        │
│       └──▶ CURATED.DAILY_TRANSACTIONS ────────────┤        │
│            CURATED.TXN_ANOMALIES                  │        │
│            CURATED.RUNNING_BALANCES               │        │
│                                                   ▼        │
│  [3] credit_risk_scoring.sas ◀────────────────────┤        │
│       └──▶ CURATED.RISK_SCORES ───────────────────┤        │
│            CURATED.RISK_MIGRATION                 │        │
│            REPORTS.RISK_SUMMARY                   │        │
│                                                   ▼        │
│  [4] monthly_regulatory_reporting.sas ◀───────────┘        │
│       └──▶ REPORTS.MONTHLY_RWA                             │
│            REPORTS.DELINQUENCY_AGING                        │
│            REPORTS.LLP_COVERAGE                             │
│            REPORTS.CAPITAL_ADEQUACY                         │
│            REG_REPORT_YYYYMM.xlsx                          │
└────────────────────────────────────────────────────────────┘

┌─────────────────── INSURANCE DOMAIN ──────────────────────┐
│                                                            │
│  [5] claims_processing.sas                                 │
│       └──▶ STG_INS.CLAIMS_REGISTER                         │
│            STG_INS.CLAIMS_REVIEW_QUEUE                      │
│            STG_INS.FRAUD_ALERTS                             │
│                                                            │
│  [6] policy_valuation.sas                                  │
│       └──▶ STG_INS.POLICY_VALUATION                        │
│            REPORTS.LOSS_RATIO_SUMMARY                       │
└────────────────────────────────────────────────────────────┘

┌─────────────────── REPORTS DOMAIN ────────────────────────┐
│                                                            │
│  [7] customer_profitability.sas                            │
│       ◀── STG_BANK.CUST_ACCOUNTS_DAILY (from [1])         │
│       ◀── CURATED.DAILY_TRANSACTIONS   (from [2])         │
│       ◀── CURATED.RISK_SCORES          (from [3])         │
│       └──▶ REPORTS.CUSTOMER_PNL                            │
│            REPORTS.SEGMENT_PROFITABILITY                    │
│            REPORTS.BRANCH_PROFITABILITY                     │
│            PROFITABILITY_YYYYMM.xlsx                        │
└────────────────────────────────────────────────────────────┘
```

### Cross-Domain Dependencies Matrix

| Consumer Program | Producer Program | Shared Dataset | Dependency Type |
|---|---|---|---|
| `daily_transaction_processing.sas` | `load_customer_accounts.sas` | `STG_BANK.CUST_ACCOUNTS_DAILY` | Intra-domain (Banking) |
| `credit_risk_scoring.sas` | `load_customer_accounts.sas` | `STG_BANK.CUST_ACCOUNTS_DAILY` | Intra-domain (Banking) |
| `monthly_regulatory_reporting.sas` | `load_customer_accounts.sas` | `STG_BANK.CUST_ACCOUNTS_DAILY` | Intra-domain (Banking) |
| `monthly_regulatory_reporting.sas` | `daily_transaction_processing.sas` | `CURATED.DAILY_TRANSACTIONS` | Intra-domain (Banking) |
| `customer_profitability.sas` | `load_customer_accounts.sas` | `STG_BANK.CUST_ACCOUNTS_DAILY` | **Cross-domain** (Reports ← Banking) |
| `customer_profitability.sas` | `daily_transaction_processing.sas` | `CURATED.DAILY_TRANSACTIONS` | **Cross-domain** (Reports ← Banking) |
| `customer_profitability.sas` | `credit_risk_scoring.sas` | `CURATED.RISK_SCORES` | **Cross-domain** (Reports ← Banking) |

### Key Findings

- **Reports domain is fully dependent on Banking** — all 3 input datasets for `customer_profitability.sas` originate from Banking pipelines
- **Insurance domain is independent** — no cross-domain dataset dependencies (operates on its own RAW feeds and Teradata)
- **Banking has self-referencing datasets** — `CURATED.DAILY_TRANSACTIONS` is both read and written by `daily_transaction_processing.sas`
- **Shared output library** — Both Banking and Reports write to the `REPORTS` library, but to different tables (no write conflicts)

---

## 2. Shared Macro Usage Across Domains

### Macro Usage Matrix

| Macro | Banking | Insurance | Reports | Total Programs | Role |
|---|:---:|:---:|:---:|:---:|---|
| `%parmv` | ✓ (4/4) | ✓ (2/2) | ✓ (1/1) | **7/7** | Parameter validation — universal entry guard |
| `%nobs` | ✓ (4/4) | ✓ (2/2) | ✓ (1/1) | **7/7** | Observation count — universal data check |
| `%sendmail` | ✓ (1/4) | ✓ (1/2) | ✗ | **2/7** | Email notification — conditional alerts |
| `%lock` | ✓ (2/4) | ✗ | ✗ | **2/7** | Dataset locking — concurrent access control |
| `%export_xlsx` | ✓ (1/4) | ✗ | ✓ (1/1) | **2/7** | XLSX export — reporting output |
| `%seplist` | indirect | indirect | ✗ | **—** | List delimiter — transitive via `%sendmail` |
| `%export_dbms` | indirect | ✗ | indirect | **—** | Generic export — transitive via `%export_xlsx` |
| `%handle` | indirect | ✗ | ✗ | **—** | File handles — transitive via `%lock` |
| `%get_data_attr` | indirect | ✗ | ✗ | **—** | Dataset attributes — transitive via `%lock` |

### Macro Migration Priority

| Priority | Macro | Effort | Rationale |
|---|---|---|---|
| **1** | `%parmv` | S | Used by every program. Convert to function parameter validation / assertions. |
| **2** | `%nobs` | S | Used by every program. Convert to `COUNT(*)` or DataFrame `.count()`. |
| **3** | `%export_xlsx` + `%export_dbms` | S | Used by 2 domains for reporting output. Replace with openpyxl/pandas/native export. |
| **4** | `%sendmail` + `%seplist` | M | Email alerting. Replace with platform-native notifications (SNS, Slack, SMTP lib). |
| **5** | `%lock` + `%handle` + `%get_data_attr` | M | Concurrency control. Replace with database transactions / row-level locking. |

### Domain-Specific vs. Shared Classification

- **All macros used are shared utilities** — no domain-specific macros were identified
- The `Macro/` library contains 92 macros total; only 9 are actively used by the 7 programs
- Insurance's hash object usage is **inline** (`declare hash`) — it does NOT use `%hash_define`/`%hash_lookup` from the macro library

---

## 3. Unified Migration Sequence

### Phase 0: Foundation (Prerequisites)

| Step | Item | Effort | Domains Affected |
|---|---|---|---|
| 0.1 | Convert `Formats/banking_formats.sas` (10 formats) to lookup tables / CASE expressions | S | Banking, Reports |
| 0.2 | Convert `Formats/insurance_formats.sas` (5 formats) to lookup tables / CASE expressions | S | Insurance |
| 0.3 | Migrate shared macros: `%parmv` → validation, `%nobs` → count utility | S | All |
| 0.4 | Establish Oracle DW connectivity (JDBC/Spark connector) | M | Banking |
| 0.5 | Establish Teradata connectivity (JDBC/ODBC) | M | Insurance |
| 0.6 | Define target schema mapping: `RAW_BANK`→`raw.banking`, `STG_BANK`→`staging.banking`, `CURATED`→`curated`, `REPORTS`→`marts.reports` | S | All |

### Phase 1: Banking Core (Foundation Datasets)

| Step | Program | Effort | Rationale |
|---|---|---|---|
| 1.1 | `load_customer_accounts.sas` | **M** | Foundation — all Banking programs + Reports depend on `STG_BANK.CUST_ACCOUNTS_DAILY`. Simple ETL pattern (Oracle extract → business rules → staging). |
| 1.2 | `monthly_regulatory_reporting.sas` | **M** | Pure SQL aggregation (no DATA steps). All logic translates directly to SQL. Depends only on step 1.1 output + Oracle DW. |

### Phase 2: Banking Advanced (Complex Logic)

| Step | Program | Effort | Rationale |
|---|---|---|---|
| 2.1 | `daily_transaction_processing.sas` | **L** | RETAIN-based running balance → window functions. Z-score anomaly detection needs 90-day lookback. Dataset locking → database concurrency. Dynamic dataset names → parameterized partitions. |
| 2.2 | `credit_risk_scoring.sas` | **XL** | WOE binning + logistic regression coefficients (model governance review). PD/LGD/EAD with account-type logic. Correlated subqueries for bureau scores. Risk migration matrix. |

### Phase 3: Insurance (Independent Track — Can Parallel with Phase 1–2)

| Step | Program | Effort | Rationale |
|---|---|---|---|
| 3.1 | `policy_valuation.sas` | **L** | Lower complexity (3.15). Three-way merge suited for SQL CTEs/JOINs. IBNR calculation is formulaic. No hash objects or email dependencies. |
| 3.2 | `claims_processing.sas` | **L** | Higher complexity (3.45). Hash object replacement. Multi-tier adjudication logic. Fraud screening via Teradata. Email alerting via `%sendmail`. |

### Phase 4: Reports (Downstream — Requires Banking Complete)

| Step | Program | Effort | Rationale |
|---|---|---|---|
| 4.1 | `customer_profitability.sas` | **M** | Terminal node. Requires all Banking outputs stable. Straightforward SQL translation. Main effort is validation/reconciliation of P&L numbers. |

### Phase 5: Orchestration & Operationalization

| Step | Item | Effort | Notes |
|---|---|---|---|
| 5.1 | Migrate `BatchJobs/run_daily_banking.sas` to target scheduler | M | Airflow DAG / Databricks Workflow with step dependencies |
| 5.2 | Migrate `BatchJobs/run_daily_insurance.sas` to target scheduler | M | Separate DAG — can run independently of Banking |
| 5.3 | Implement `%sendmail` equivalent (alerting) | S | SNS / Slack webhook / SMTP library |
| 5.4 | Implement `%lock` equivalent (concurrency) | S | Database transactions / optimistic locking |
| 5.5 | Parallel-run validation (SAS vs. target) | L | Run both for ≥2 months; reconcile row counts, financial totals |

### Dependency Diagram (Phases)

```
Phase 0 (Foundation)
    │
    ├───────────────────────────────────────┐
    │                                       │
    ▼                                       ▼
Phase 1 (Banking Core)          Phase 3 (Insurance) ◀── CAN RUN IN PARALLEL
    │
    ▼
Phase 2 (Banking Advanced)
    │
    ▼
Phase 4 (Reports)
    │
    ▼
Phase 5 (Orchestration & Validation)
```

---

## 4. Total Effort Estimate

### By Program

| # | Program | Domain | Lines | Complexity Score | Effort | Est. Duration |
|---|---|---|---|---|---|---|
| 1 | `load_customer_accounts.sas` | Banking | 216 | 3.0 | M | 3–5 days |
| 2 | `daily_transaction_processing.sas` | Banking | 246 | 3.7 | L | 1–2 weeks |
| 3 | `credit_risk_scoring.sas` | Banking | 270 | 3.5 | XL | 2–4 weeks |
| 4 | `monthly_regulatory_reporting.sas` | Banking | 199 | 3.2 | M | 3–5 days |
| 5 | `claims_processing.sas` | Insurance | 238 | 3.45 | L | 1–2 weeks |
| 6 | `policy_valuation.sas` | Insurance | 206 | 3.15 | L | 1–2 weeks |
| 7 | `customer_profitability.sas` | Reports | 176 | 2.7 | M | 3–5 days |

### By Phase (Aggregate)

| Phase | Programs | Total Effort | Calendar Duration (Sequential) | Calendar Duration (Parallel) |
|---|---|---|---|---|
| Phase 0: Foundation | Prerequisites | ~2 weeks | 2 weeks | 2 weeks |
| Phase 1: Banking Core | 2 programs | M + M | 2 weeks | 1.5 weeks |
| Phase 2: Banking Advanced | 2 programs | L + XL | 5–6 weeks | 4 weeks |
| Phase 3: Insurance | 2 programs | L + L | 3–4 weeks | 2–3 weeks (parallel with Phases 1–2) |
| Phase 4: Reports | 1 program | M | 1 week | 1 week |
| Phase 5: Orchestration | Infrastructure | M + L (validation) | 3–4 weeks | 3 weeks |
| | | | | |
| **TOTAL** | **7 programs** | | **16–19 weeks (sequential)** | **12–14 weeks (with parallelism)** |

### Effort Size Key

| Size | Definition | Duration |
|---|---|---|
| S | Simple translation, minimal logic | 1–2 days |
| M | Moderate SQL + business logic conversion | 3–5 days |
| L | Complex SAS-specific features (RETAIN, hash, dynamic datasets) | 1–2 weeks |
| XL | Regulatory/model logic requiring governance review + UAT | 2–4 weeks |

### Resource Recommendations

| Track | Skills Needed | FTE |
|---|---|---|
| Banking Track (Phases 1–2) | SQL, Spark/dbt, credit risk domain knowledge | 2 engineers |
| Insurance Track (Phase 3) | SQL, actuarial domain knowledge, Teradata | 1 engineer |
| Reports + Orchestration (Phases 4–5) | SQL, scheduling, DevOps | 1 engineer |
| Validation & QA | SAS knowledge, financial reconciliation | 1 engineer (part-time) |

**Recommended team size: 4–5 engineers for a 12–14 week timeline with parallelism.**

---

## 5. Domain Summaries

### Banking Domain (4 programs, 931 lines)

| Program | Complexity | Key Challenge |
|---|---|---|
| `load_customer_accounts.sas` | 3.0 (M) | Oracle DW extract → staging; foundation for all downstream |
| `daily_transaction_processing.sas` | 3.7 (M-H) | RETAIN running balance → window functions; Z-score anomaly; dataset locking |
| `credit_risk_scoring.sas` | 3.5 (M-H) | WOE binning, PD/LGD/EAD; hardcoded model coefficients; model governance |
| `monthly_regulatory_reporting.sas` | 3.2 (M) | Basel III RWA/CET1 aggregation; multi-sheet XLSX; pure SQL (easiest translation) |

**Critical path:** `load_customer_accounts` → `daily_transaction_processing` → `credit_risk_scoring` → `monthly_regulatory_reporting`

### Insurance Domain (2 programs, 444 lines)

| Program | Complexity | Key Challenge |
|---|---|---|
| `claims_processing.sas` | 3.45 (M-H) | Inline hash object for policy lookup; multi-tier auto-adjudication; fraud screening via Teradata |
| `policy_valuation.sas` | 3.15 (M) | Three-way merge; IBNR estimation (simplified 15%-of-premium); earned premium pro-rata |

**Independent track:** No dependencies on Banking or Reports. Can be migrated in parallel.

### Reports Domain (1 program, 176 lines)

| Program | Complexity | Key Challenge |
|---|---|---|
| `customer_profitability.sas` | 2.7 (M) | Cross-domain dependency on all Banking outputs; P&L accuracy (financial reconciliation); `%export_xlsx` parameter mismatch |

**Terminal node:** Must wait for Banking Phases 1–2 to complete.

---

## 6. Risk Register

### High Severity

| # | Risk | Domain | Impact | Mitigation |
|---|---|---|---|---|
| 1 | RETAIN-to-window-function conversion changes running balance semantics if row ordering differs | Banking | Incorrect account balances | Full dataset comparison (SAS vs. target); enforce deterministic ORDER BY |
| 2 | Hardcoded credit risk model coefficients bypass model governance | Banking | Regulatory non-compliance | Externalize to model registry; require sign-off from model validation team before migration |
| 3 | Cross-domain data dependency — Reports cannot run until Banking is stable | Reports | Report pipeline blocked until Banking complete | Establish data contracts (schema + SLA); run Banking end-to-end in target before Reports work begins |
| 4 | P&L calculation accuracy — floating-point differences between SAS and target | Reports | Audit/regulatory risk | Use DECIMAL types for monetary columns; automated reconciliation during parallel-run |
| 5 | Hash object replacement in claims_processing — must preserve single-pass lookup semantics | Insurance | Incorrect claim adjudication | Replace with SQL JOIN or Spark broadcast join; validate with full claims dataset comparison |

### Medium Severity

| # | Risk | Domain | Impact | Mitigation |
|---|---|---|---|---|
| 6 | Self-referencing read/write on `CURATED.DAILY_TRANSACTIONS` | Banking | Data corruption during concurrent runs | Use staging pattern or snapshot isolation on target |
| 7 | Format catalogs used for both display and business logic | All | Logic errors if formats not fully migrated | Audit all format references; separate display from logic |
| 8 | Oracle/Teradata implicit pass-through SQL may have different semantics on target | Banking/Insurance | Silent data differences | Test all external-sourced queries independently |
| 9 | PROC APPEND FORCE allows schema mismatches — target may not handle silently | Insurance | Schema evolution failures | Implement explicit schema validation before insert |
| 10 | `%export_xlsx` parameter mismatch (`file=`/`sheet=` vs `PATH=`) in Reports | Reports | XLSX export may be broken in production | Verify actual production behavior before migration |
| 11 | Dynamic dataset names (`TXN_FEED_YYYYMMDD`) require parameterized resolution | Banking | Failed ingestion on target | Use date-partitioned tables or parameterized queries |
| 12 | Dataset locking (`%lock`) has no equivalent in most modern platforms | Banking | Concurrent access issues | Replace with database transactions / optimistic locking |

### Low Severity

| # | Risk | Domain | Impact | Mitigation |
|---|---|---|---|---|
| 13 | SAS date literals and `%sysfunc()` pervasive across all programs | All | Tedious but straightforward translation | Systematic find-and-replace with target date functions |
| 14 | Email notifications via `%sendmail` | Banking/Insurance | Alert gap during transition | Implement cloud-native alerting early in Phase 5 |
| 15 | Control-M scheduling must be recreated | All | Operational gap | Document all schedules and recreate in target orchestrator |
| 16 | Hardcoded paths (`/data/sas/...`) in autoexec.sas | All | Environment portability | Replace with target platform storage references (Unity Catalog, S3, ADLS) |
| 17 | Capital adequacy values (CET1=50M, Tier1=65M) are hardcoded placeholders | Banking | Incorrect regulatory ratios in production | Source from GL feed in target platform |

---

## Appendix: Source Assessments

This consolidated view synthesizes findings from three domain-specific assessments:

- **[BANKING_MIGRATION_ASSESSMENT.md](./BANKING_MIGRATION_ASSESSMENT.md)** — PR #11
- **[INSURANCE_MIGRATION_ASSESSMENT.md](./INSURANCE_MIGRATION_ASSESSMENT.md)** — PR #10
- **[REPORTS_MIGRATION_ASSESSMENT.md](./REPORTS_MIGRATION_ASSESSMENT.md)** — PR #12

Each domain assessment contains detailed per-program analysis including full data lineage tables, macro call graphs, complexity scoring rationale, and SAS-feature-specific migration notes.
