# Banking Domain: SAS Migration Assessment

> **Scope:** Programs/Banking/ — 4 SAS programs (931 total lines)
> **Config:** Config/autoexec.sas | **Formats:** Formats/banking_formats.sas
> **Orchestrator:** BatchJobs/run_daily_banking.sas

---

## 1. Artifact Inventory

| # | Filename | Lines | Primary Purpose | SAS PROCs Used | DATA Steps | SQL Pass-Throughs |
|---|----------|-------|-----------------|----------------|------------|-------------------|
| 1 | `load_customer_accounts.sas` | 216 | Extract customer accounts from Oracle DW, apply business rules, compute derived metrics (utilization, dormancy, age), load to staging layer | PROC SQL, PROC MEANS, PROC DATASETS | 1 (business rules + derived metrics, lines 82–157) | 1 — implicit Oracle read via `ORA_DW` libname engine (PROC SQL join on `ORA_DW.CUST_ACCOUNTS` ⨝ `ORA_DW.CUST_DEMOGRAPHICS`) |
| 2 | `daily_transaction_processing.sas` | 246 | Ingest daily transaction feed, validate/reject, enrich with account data, compute running balances via RETAIN, detect anomalies (Z-score, overdraft, large withdrawal), load to curated layer | PROC SQL (×3), PROC APPEND (×2), PROC DATASETS | 2 (validation step lines 45–97; running balance lines 137–154) | 1 — implicit read via `RAW_BANK` libname; 1 — read from `CURATED.DAILY_TRANSACTIONS` for 90-day stats |
| 3 | `credit_risk_scoring.sas` | 270 | Apply logistic regression credit risk scorecard (PD/LGD/EAD), WOE binning for FICO/utilization/DPD/age/LTV, risk rating assignment, risk migration tracking | PROC SQL, PROC APPEND (×2), PROC MEANS, PROC DATASETS | 1 (scorecard model application, lines 92–197) | 1 — Oracle reads via `ORA_DW.BUREAU_SCORES`, `ORA_DW.PAYMENT_HISTORY`, `ORA_DW.COLLATERAL` (correlated subquery for latest bureau score) |
| 4 | `monthly_regulatory_reporting.sas` | 199 | Basel III regulatory aggregations: RWA by category, delinquency aging buckets, loan loss provision coverage, capital adequacy ratios (CET1/Tier1/Total), Excel export for regulators | PROC SQL (×4) | 0 | 1 — Oracle read via `ORA_DW.LOAN_DETAILS`, `ORA_DW.COLLATERAL` |

**Totals:** 931 lines | 4 DATA steps | 11 PROC SQL blocks | 4 Oracle implicit pass-throughs

---

## 2. Data Lineage

### 2.1 load_customer_accounts.sas

| Direction | Dataset / Library | Notes |
|-----------|-------------------|-------|
| **Input** | `ORA_DW.CUST_ACCOUNTS` | Oracle DW — account master (balance, status, rates) |
| **Input** | `ORA_DW.CUST_DEMOGRAPHICS` | Oracle DW — customer PII, segment, risk rating, region |
| **Input** | `RAW_BANK.DAILY_RATES` | Referenced in header; not directly read in code (likely upstream dependency) |
| **Output** | `STG_BANK.CUST_ACCOUNTS_DAILY` | Primary staging table — daily snapshot with derived metrics |
| **Output** | `STG_BANK.ACCT_EXCEPTIONS` | Data quality exceptions (NEG_BAL, HIGH_UTIL, NO_RISK) |
| **Work** | `WORK.ACCT_RAW` | Raw Oracle extract before business rules |
| **Work** | `WORK.ACCT_EXCEPTIONS` | Temp exception accumulator |
| **Work** | `WORK.ACCT_SUMMARY` | Summary statistics by account type and region |

### 2.2 daily_transaction_processing.sas

| Direction | Dataset / Library | Notes |
|-----------|-------------------|-------|
| **Input** | `RAW_BANK.TXN_FEED_YYYYMMDD` | Dynamic dataset name derived from `txn_date` parameter |
| **Input** | `STG_BANK.CUST_ACCOUNTS_DAILY` | Produced by `load_customer_accounts.sas` (upstream dependency) |
| **Input** | `CURATED.DAILY_TRANSACTIONS` | Historical 90-day window for anomaly Z-score baseline |
| **Output** | `CURATED.DAILY_TRANSACTIONS` | Appended — enriched, validated transactions with running balance |
| **Output** | `CURATED.TXN_ANOMALIES` | Appended — flagged anomalies (HIGH_AMOUNT, OVERDRAFT, LARGE_WITHDRAWAL, ORPHAN_ACCOUNT) |
| **Output** | `CURATED.RUNNING_BALANCES` | Overwritten — latest running balance per account |
| **Work** | `WORK.TXN_VALIDATED`, `WORK.TXN_REJECTED` | Validation split |
| **Work** | `WORK.TXN_ENRICHED` | Joined with account data |
| **Work** | `WORK.TXN_WITH_BALANCE` | Running balance via RETAIN |
| **Work** | `WORK.TXN_STATS` | 90-day aggregate stats for Z-score |
| **Work** | `WORK.TXN_ANOMALIES` | Anomaly detection results |

### 2.3 credit_risk_scoring.sas

| Direction | Dataset / Library | Notes |
|-----------|-------------------|-------|
| **Input** | `STG_BANK.CUST_ACCOUNTS_DAILY` | Account snapshot with derived metrics (upstream dependency) |
| **Input** | `ORA_DW.BUREAU_SCORES` | FICO, Vantage, bureau metrics; correlated subquery for latest score ≤ score_date |
| **Input** | `ORA_DW.PAYMENT_HISTORY` | 12-month payment behavior (on-time, 30/60/90 DPD counts) |
| **Input** | `ORA_DW.COLLATERAL` | Collateral values and appraisal dates for secured loans |
| **Output** | `CURATED.RISK_SCORES` | Appended — PD, LGD, EAD, expected loss, new risk rating per account |
| **Output** | `CURATED.RISK_MIGRATION` | Appended — rating change records (UPGRADE/DOWNGRADE/STABLE/NEW) |
| **Output** | `REPORTS.RISK_SUMMARY` | Overwritten — aggregated risk stats by account type and rating |
| **Work** | `WORK.SCORE_INPUT` | Feature assembly from 4 source tables |
| **Work** | `WORK.SCORED` | Model output with PD/LGD/EAD/expected loss |
| **Work** | `WORK.RISK_MIGRATION` | Rating change detection |

### 2.4 monthly_regulatory_reporting.sas

| Direction | Dataset / Library | Notes |
|-----------|-------------------|-------|
| **Input** | `STG_BANK.CUST_ACCOUNTS_DAILY` | Account snapshot (upstream dependency) |
| **Input** | `CURATED.DAILY_TRANSACTIONS` | Transaction history (upstream dependency) |
| **Input** | `ORA_DW.LOAN_DETAILS` | Loan specifics: days past due, allowance, LTV |
| **Input** | `ORA_DW.COLLATERAL` | Collateral values for RWA risk weight determination |
| **Output** | `REPORTS.MONTHLY_RWA` | Risk-weighted assets by account type, segment, risk weight |
| **Output** | `REPORTS.DELINQUENCY_AGING` | Delinquency aging in 30/60/90/120/180+ day buckets |
| **Output** | `REPORTS.LLP_COVERAGE` | Loan loss provision and NPL coverage ratios |
| **Output** | `REPORTS.CAPITAL_ADEQUACY` | CET1, Tier 1, Total Capital ratios with pass/fail status |
| **Output** | `/data/sas/reports/output/REG_REPORT_YYYYMM.xlsx` | Excel export with 3 sheets (RWA, Delinquency, LLP_Coverage) |

---

## 3. Macro Dependencies

### 3.1 Directly Referenced Macros

| Macro | Source File | Parameters | Purpose | Used By | Shared Across Domains? |
|-------|------------|------------|---------|---------|----------------------|
| `%parmv` | `Macro/parmv.sas` (359 lines) | `var, _req, _val, _msg, _words, _case, _varchk, _def` | Parameter validation — sets `parmerr=1` on invalid values | All 4 programs | Yes — universal utility |
| `%nobs` | `Macro/nobs.sas` (253 lines) | `data, mvar=` | Return observation count from dataset descriptor or PROC SQL | All 4 programs | Yes — universal utility |
| `%lock` | `Macro/lock.sas` (352 lines) | `member=, timeout=, retry=, action=, onfail=, unlock=, email=` | Obtain/release SAS dataset locks with retry, timeout, and handle integration | `daily_transaction_processing`, `credit_risk_scoring` | Yes — universal utility |
| `%sendmail` | `Macro/sendmail.sas` (260 lines) | `metadata=, to=, cc=, bcc=, from=, subject=, attach=` | Send email notifications via SAS email engine; supports metadata dataset or inline params | `load_customer_accounts` (conditional), `run_daily_banking` | Yes — universal utility |
| `%export_xlsx` | `Macro/export_xlsx.sas` (101 lines) | `data=, path=, replace=, label=` | Wrapper for `%export_dbms` to produce .xlsx files | `monthly_regulatory_reporting` | Yes — shared export utility |

### 3.2 Transitive (Indirect) Macro Dependencies

| Macro | Source File | Called By | Purpose |
|-------|------------|-----------|---------|
| `%seplist` | `Macro/seplist.sas` (200 lines) | `%sendmail`, `%hash_define` | Emit delimited word list |
| `%export_dbms` | `Macro/export_dbms.sas` (520 lines) | `%export_xlsx` | Generic PROC EXPORT wrapper |
| `%handle` | `Macro/handle.sas` (451 lines) | `%lock` | Print/close open file handles on locked datasets |
| `%get_data_attr` | `Macro/get_data_attr.sas` (226 lines) | `%lock` | Return dataset attributes (engine type, lib path) |

### 3.3 Macros Referenced in Task Description but Not Directly Used by Banking Programs

These macros exist in the `Macro/` library (92 macros total) and are available via autocall but are not explicitly `%include`d or invoked by the four banking programs:

| Macro | Purpose | Banking Relevance |
|-------|---------|-------------------|
| `%check_if_empty` | Check if dataset has zero observations | Could replace manual `%nobs` → 0 checks |
| `%hash_define` / `%hash_lookup` | Define and query hash objects for lookups | Not used in banking; used in insurance domain |
| `%logparse` | Extract performance stats from SAS logs | Used by batch monitoring, not individual programs |
| `%batch_submit` | Submit SAS session in batch mode | Used by operations, not program logic |
| `%create_directory` | Create directories via `dlcreatedir` option | Infrastructure utility |
| `%varlist` | Return space-separated variable list from dataset | Data inspection utility |

---

## 4. Complexity Scores

Scoring scale: **1** (trivial) → **5** (very complex)

| Dimension | load_customer_accounts | daily_transaction_processing | credit_risk_scoring | monthly_regulatory_reporting |
|-----------|:-----:|:-----:|:-----:|:-----:|
| **Data Volume Handling** | 3 | 4 | 3 | 3 |
| **Business Logic Complexity** | 3 | 4 | 5 | 4 |
| **External Dependencies** | 3 | 3 | 4 | 4 |
| **Error Handling Sophistication** | 3 | 4 | 2 | 2 |
| **Macro Usage Depth** | 3 | 3 | 2 | 3 |
| **Overall Weighted Score** | **3.0** | **3.7** | **3.5** | **3.2** |

> **Weighting:** Data Volume (20%), Business Logic (30%), External Dependencies (20%), Error Handling (15%), Macro Depth (15%)

### Scoring Rationale

**load_customer_accounts.sas (3.0 — Medium)**
- Straightforward extract-transform-load pattern with Oracle join
- Business rules are clear conditional logic (negative balance, high utilization, dormancy)
- Good error handling: observation count checks, conditional email alerts, WORK cleanup
- Single Oracle connection via libname engine; no complex pass-through SQL

**daily_transaction_processing.sas (3.7 — Medium-High)**
- RETAIN-based running balance is a SAS-specific pattern requiring careful migration (window functions)
- Multi-stage validation/rejection pipeline with 6 validation rules
- Z-score anomaly detection reads 90-day historical window
- Dataset locking via `%lock` macro for concurrent access control
- Dynamic dataset name (`TXN_FEED_YYYYMMDD`) requires parameterized table resolution

**credit_risk_scoring.sas (3.5 — Medium-High)**
- Highest business logic complexity: logistic regression scorecard with 5 WOE binning dimensions
- Hardcoded model coefficients (INTERCEPT, weights) — regulatory model governance concern
- PD/LGD/EAD estimation with account-type-specific logic
- Correlated subquery for latest bureau score adds SQL complexity
- Risk migration matrix tracks rating changes over time

**monthly_regulatory_reporting.sas (3.2 — Medium)**
- Pure SQL aggregation — no DATA steps, so SQL translation is more direct
- Basel III risk weight mapping with nested CASE logic
- Capital adequacy ratios with placeholder GL values (50M/65M/80M)
- Excel export dependency via `%export_xlsx` → must be replaced with target platform export
- Multiple output tables feeding a single consolidated Excel workbook

---

## 5. Recommended Migration Sequence

| Order | Program | Effort | Rationale |
|-------|---------|--------|-----------|
| **1** | `load_customer_accounts.sas` | **M** | Foundation dataset — all other programs depend on `STG_BANK.CUST_ACCOUNTS_DAILY`. Simple ETL pattern (extract → transform → load). Oracle read can be replaced with JDBC/Spark connector. Business rules are portable conditional logic. |
| **2** | `monthly_regulatory_reporting.sas` | **M** | Pure SQL program (no DATA steps). All aggregations translate directly to SQL/Spark SQL. Depends only on `CUST_ACCOUNTS_DAILY` (migrated in step 1) and `ORA_DW.LOAN_DETAILS`. Excel export must be replaced (e.g., Pandas/openpyxl or Databricks notebook export). |
| **3** | `daily_transaction_processing.sas` | **L** | RETAIN-based running balance requires conversion to window functions (`SUM() OVER (PARTITION BY ... ORDER BY ... ROWS UNBOUNDED PRECEDING)`). Z-score anomaly detection needs 90-day historical access. Dataset locking pattern must be replaced with database-level concurrency control. Dynamic dataset naming needs parameterized table/partition logic. |
| **4** | `credit_risk_scoring.sas` | **XL** | Most complex business logic — WOE binning, logistic regression coefficients, PD/LGD/EAD calculations. Requires model governance review before migration. Hardcoded coefficients should be externalized to a configuration/model registry. Correlated subquery for bureau scores may need optimization on target platform. Risk migration matrix depends on both `CUST_ACCOUNTS_DAILY` and the `RISK_SCORES` history. |

### Prerequisites

1. **Oracle DW connectivity** — JDBC driver or Spark Oracle connector configured on target platform
2. **Library/schema mapping** — `RAW_BANK`, `STG_BANK`, `CURATED`, `REPORTS` → target catalog/schema names
3. **Format catalog conversion** — All `PROC FORMAT` values in `banking_formats.sas` must be converted to lookup tables or CASE expressions
4. **Macro replacement** — `%parmv` → parameter validation in target language; `%nobs` → `COUNT(*)` or DataFrame `.count()`; `%lock` → database transactions
5. **Scheduling** — Control-M job chain → target orchestrator (Airflow, Databricks Workflows, etc.)
6. **Email alerting** — `%sendmail` → target alerting service (SNS, SMTP integration, Slack webhook)

### Effort Estimates

| Size | Definition | Estimated Duration |
|------|-----------|-------------------|
| S | Simple SQL translation, minimal logic | 1–2 days |
| M | Moderate SQL + some business logic conversion | 3–5 days |
| L | Complex SAS-specific features (RETAIN, dynamic datasets, locking) | 1–2 weeks |
| XL | Regulatory/model logic requiring validation, governance review, UAT | 2–4 weeks |

---

## 6. Risk Factors & Notes

### 6.1 SAS-Specific Features Requiring Special Handling

| Feature | Programs | Migration Risk | Notes |
|---------|----------|---------------|-------|
| **RETAIN statement** (running balance) | `daily_transaction_processing` | **High** | Must convert to `SUM() OVER()` window function. Ensure identical ordering semantics (`BY ACCOUNT_ID TRANSACTION_DATE TRANSACTION_ID`). |
| **Custom formats** (`$ACCTTYPE.`, `$ACCTSTAT.`, `RISKRATE.`, etc.) | All 4 programs | **Medium** | 10 formats defined in `banking_formats.sas`. Convert to lookup/dimension tables or inline CASE expressions. Formats are used for both display and filtering. |
| **SAS date literals** (`"&run_date"d`) | All 4 programs | **Low** | Replace with target platform date parsing. Macro variable substitution into date literals is pervasive. |
| **`%sysfunc()` / `%sysevalf()`** | All 4 programs | **Low** | SAS macro functions for date arithmetic, string operations. Replace with target language equivalents. |
| **PROC APPEND with FORCE** | `daily_transaction_processing`, `credit_risk_scoring` | **Medium** | Incremental append pattern. Replace with `INSERT INTO ... SELECT` or incremental merge/upsert. |
| **PROC MEANS with NWAY** | `load_customer_accounts`, `credit_risk_scoring` | **Low** | Direct translation to `GROUP BY` aggregation. |
| **Dataset locking (`%lock`)** | `daily_transaction_processing`, `credit_risk_scoring` | **Medium** | SAS file-level locking. Replace with database transactions/row-level locking on target platform. |
| **Dynamic dataset names** (`TXN_FEED_YYYYMMDD`) | `daily_transaction_processing` | **Medium** | Macro-resolved table name. Replace with partitioned tables or parameterized queries. |
| **Correlated subquery** (latest bureau score) | `credit_risk_scoring` | **Medium** | `SELECT MAX(SCORE_DATE) WHERE SCORE_DATE <= &score_date` — performance-sensitive on large tables. Consider window function `ROW_NUMBER()` approach. |
| **Hardcoded model coefficients** | `credit_risk_scoring` | **High** | Intercept + 5 WOE weight vectors embedded in code. Must externalize to config/model registry for governance. |
| **Excel export (`%export_xlsx`)** | `monthly_regulatory_reporting` | **Low** | Replace with target export (Pandas, Databricks notebook, or SSRS). Multi-sheet workbook requires coordinated export. |

### 6.2 Implicit Data Dependencies

- **Execution order is critical:** The batch orchestrator (`run_daily_banking.sas`) enforces step ordering (1→2→3→4). Step 2 reads Step 1's output; Steps 3–4 also depend on Step 1. Step 4 reads Step 2's output.
- **`CURATED.DAILY_TRANSACTIONS` is both read and written** by `daily_transaction_processing.sas` (reads 90-day history for Z-score, then appends new data). This creates a self-referencing dependency.
- **`monthly_regulatory_reporting.sas`** is scheduled monthly but included in the daily batch orchestrator — it runs daily but only produces meaningful output on the 3rd business day.
- **Capital adequacy values** (CET1=50M, Tier1=65M, Total=80M) are hardcoded placeholders — in production these would come from a General Ledger feed.

### 6.3 Database Connectivity Patterns

| Connection | Engine | Config Location | Programs |
|------------|--------|----------------|----------|
| Oracle DW (`ORA_DW`) | SAS/ACCESS to Oracle | `autoexec.sas` lines 62–70 | All 4 (reads) |
| Teradata (`TERA_DW`) | SAS/ACCESS to Teradata | `autoexec.sas` lines 72–79 | Not used by banking programs (insurance/reports domain) |

- Oracle credentials are stored in macro variables (`&ora_uid`, `&ora_pwd`) — must be migrated to a secrets manager
- Read-only access (`access=readonly`) — banking programs do not write back to Oracle
- `readbuff=5000` tuning parameter on Oracle connection may need equivalent on target connector

### 6.4 Scheduling & Orchestration

| Schedule | Control-M Job | Program | Timing |
|----------|---------------|---------|--------|
| Daily | `BANK_MASTER` | `run_daily_banking.sas` | 05:45 |
| Daily | `BANK_DAILY_01` | `load_customer_accounts.sas` | 06:00 |
| Daily | `BANK_DAILY_02` | `daily_transaction_processing.sas` | 07:30 |
| Weekly | `BANK_WEEKLY_01` | `credit_risk_scoring.sas` | Sunday 02:00 |
| Monthly | `BANK_MONTHLY_01` | `monthly_regulatory_reporting.sas` | 3rd business day |

- The batch orchestrator includes all 4 programs in sequence but individual Control-M jobs also exist for standalone execution
- Restart capability via `restart_from=` parameter allows resuming from a failed step
- `ABORT_ON_ERR=Y` (from `autoexec.sas`) causes the batch to halt on first failure with email notification

### 6.5 Key Migration Risks Summary

| Risk | Severity | Mitigation |
|------|----------|------------|
| RETAIN-to-window-function conversion changes running balance semantics if row ordering differs | **High** | Validate with full dataset comparison (SAS vs. target output) |
| Hardcoded credit risk model coefficients bypass model governance | **High** | Externalize to model registry; require sign-off from model validation team |
| Format catalogs used for both display and business logic (e.g., filtering on formatted values) | **Medium** | Audit all format references; separate display formats from business logic lookups |
| Self-referencing read/write on `CURATED.DAILY_TRANSACTIONS` | **Medium** | Use staging pattern or snapshot isolation on target platform |
| Monthly report running in daily batch may produce empty/duplicate output | **Medium** | Add calendar-aware gate logic in target orchestrator |
| Oracle implicit pass-through SQL semantics may differ from explicit SQL on target | **Medium** | Test all Oracle-sourced queries independently on target connector |
| Email notifications via `%sendmail` require SMTP infrastructure | **Low** | Replace with cloud-native alerting (SNS, SendGrid, etc.) |
