# SAS Construct → Databricks/dbt Mapping

Maps every SAS language construct found in this estate to its Databricks equivalent, with specific code-level migration guidance.

---

## DATA Step Constructs

| SAS Construct | Where Used | Databricks/dbt Equivalent | Complexity | Notes |
|---------------|-----------|--------------------------|------------|-------|
| `DATA ... SET ...` (basic) | All programs | `SELECT * FROM` / dbt model | Low | Direct SQL mapping |
| `DATA ... SET ... BY` group | `daily_transaction_processing` | `PARTITION BY ... ORDER BY` | Medium | Must define explicit ordering |
| `RETAIN` variable | `daily_transaction_processing` (running balance) | `SUM() OVER (PARTITION BY ... ORDER BY ... ROWS UNBOUNDED PRECEDING)` | High | Running balance is the primary RETAIN use case; window function with frame spec |
| `first.var / last.var` | `daily_transaction_processing` | `ROW_NUMBER()`, `LEAD()`/`LAG()`, or boundary detection via window functions | Medium | SAS BY-group boundary detection maps to window analytics |
| `OUTPUT` to multiple datasets | `load_customer_accounts`, `daily_transaction_processing`, `claims_processing` | Multiple dbt models with different `WHERE` clauses, or `CASE` logic in a single model | Medium | Split-output pattern requires separate models in dbt |
| `IF/THEN/ELSE` business rules | All programs | SQL `CASE WHEN ... THEN ... END` | Low | Direct 1:1 mapping |
| `MERGE ... BY` | `policy_valuation`, `customer_profitability` | SQL `JOIN` | Low | SAS MERGE is a full outer join with `IN=` filters |
| `declare hash` | `claims_processing` (policy lookup) | Spark broadcast join / dbt `ref()` join | Medium | Hash object → `LEFT JOIN` with broadcast hint for small tables |
| `SET ... key=` (index lookup) | `Parent-Child-Index` | Recursive CTE / self-join | High | Recursive hierarchy traversal |
| `LENGTH` statement | Throughout | Column type definitions in schema.yml | Low | |
| `FORMAT` statement | Throughout | dbt macro / CASE expression | Low | See format mapping below |
| `ARRAY` processing | `Parent-Child-Index` | `TRANSFORM()` / `SEQUENCE()` in Spark SQL, or Python UDF | Medium | |
| `_N_` counter | `claims_processing` | `ROW_NUMBER()` or initialization logic | Low | |
| `_ERROR_` reset | `Parent-Child-Index` | Not needed (error semantics differ) | Low | |

## PROC SQL Constructs

| SAS Construct | Where Used | Databricks/dbt Equivalent | Complexity | Notes |
|---------------|-----------|--------------------------|------------|-------|
| `CREATE TABLE ... AS SELECT` | All programs | dbt model (SQL) | Low | Direct mapping |
| `INSERT INTO ... SELECT` | `load_customer_accounts` | dbt incremental model with `MERGE` | Low | |
| `SELECT ... INTO :macrovar` | `Parent-Child-Index` | dbt `run_query()` + Jinja variable | Medium | |
| `calculated` keyword | `monthly_regulatory_reporting` | Column alias (not needed in Spark SQL) | Low | Replace with CTE or subquery |
| Correlated subquery | `credit_risk_scoring` (latest bureau score) | Window function `ROW_NUMBER()` + qualify, or `QUALIFY` | Medium | |
| `CASE WHEN` | Throughout | `CASE WHEN` (identical) | Low | |
| `HAVING` | `daily_transaction_processing` | `HAVING` (identical) | Low | |

## Procedure Constructs

| SAS Construct | Where Used | Databricks/dbt Equivalent | Complexity | Notes |
|---------------|-----------|--------------------------|------------|-------|
| `PROC FORMAT` | `Formats/` | dbt seed CSV + dbt macro with `CASE WHEN` | Low | See format migration section |
| `PROC MEANS / PROC SUMMARY` | `load_customer_accounts`, `credit_risk_scoring`, `policy_valuation`, `customer_profitability` | `GROUP BY` with `COUNT`, `SUM`, `AVG`, `STDDEV` | Low | Direct SQL aggregation |
| `PROC APPEND` | `daily_transaction_processing`, `credit_risk_scoring`, `claims_processing`, batch jobs | Delta Lake `INSERT INTO` or incremental dbt model | Medium | Locking semantics handled by Delta ACID |
| `PROC DATASETS DELETE` | All programs | Not needed (dbt manages temp models) | Low | Cleanup of WORK datasets not required in dbt |
| `PROC PRINT` | Batch orchestrators | Databricks notebook display / logging | Low | |
| `PROC CONTENTS` | `Parent-Child-Index` | `DESCRIBE TABLE` or `INFORMATION_SCHEMA` | Low | |
| `PROC EXPORT` (via `%export_xlsx`) | `monthly_regulatory_reporting`, `customer_profitability` | Python `openpyxl`/`xlsxwriter` in Databricks notebook, or Databricks SQL dashboard export | Medium | No native dbt equivalent |

## Macro Constructs

| SAS Construct | Where Used | Databricks/dbt Equivalent | Complexity | Notes |
|---------------|-----------|--------------------------|------------|-------|
| `%MACRO / %MEND` | All programs | dbt macro (Jinja) | Low | |
| `%LET` / `&macrovar` | Throughout | dbt `var()` / Jinja `{{ }}` | Low | |
| `%IF / %THEN / %DO` | Throughout | Jinja `{% if %}` | Low | |
| `%EVAL / %SYSEVALF` | Batch orchestrators | Jinja expressions | Low | |
| `%SYSFUNC()` | Throughout (date functions) | dbt date macros / Spark SQL date functions | Low | |
| `%INCLUDE` | Batch orchestrators, all programs | dbt `ref()` dependency chain / Databricks Workflows task sequencing | Medium | |
| `%GOTO / labels` | Error handling | dbt `on-run-end` hooks / Workflow error handling | Medium | |
| `%parmv` | All programs | dbt `config()` validation or custom macro | Low | Parameter validation becomes dbt var validation |
| `%nobs` | All programs | dbt `run_query()` with `COUNT(*)` or post-hook | Low | |
| `%lock` | `daily_transaction_processing`, `credit_risk_scoring` | Not needed (Delta Lake provides ACID) | Low | Delta transactions handle concurrency |
| `%sendmail` | `load_customer_accounts`, `claims_processing`, batch jobs | Databricks SQL Alerts / Workflow notifications / PagerDuty webhook | Medium | |
| `%export_xlsx` | `monthly_regulatory_reporting`, `customer_profitability` | Python notebook step in Workflow | Medium | |
| `%seplist` | `Parent-Child-Index` | Jinja `{{ columns \| join(', ') }}` | Low | |

## System Variables & Options

| SAS Construct | Where Used | Databricks Equivalent |
|---------------|-----------|----------------------|
| `&SYSCC` / `&SYSERR` | Batch orchestrators | Workflow task exit codes |
| `&SYSDATE` / `&SYSTIME` | Throughout | `current_date()`, `current_timestamp()` |
| `&SYSLAST` | `%nobs` macro | Not applicable |
| `options compress=yes` | `autoexec.sas` | Delta Lake default compression (snappy/zstd) |
| `options fmtsearch=` | `autoexec.sas` | dbt macro autoloading |
| `options mlogic mprint symbolgen` | `autoexec.sas` | dbt `--debug` flag / Databricks job logging |
| `options validvarname=v7` | `autoexec.sas` | Spark SQL column naming (backtick escaping for special chars) |

---

## Format Migration Detail

Each SAS `PROC FORMAT` value format maps to a dbt macro returning a `CASE WHEN` expression.

### Banking Formats (9 total)

| Format Name | Type | Values | dbt Macro | Seed Table |
|-------------|------|--------|-----------|------------|
| `$ACCTTYPE` | Character | 11 values + OTHER | `format_account_type()` | **Exists** in target repo |
| `$ACCTSTAT` | Character | 8 values + OTHER | `format_account_status()` | **Exists** in target repo |
| `RISKRATE` | Numeric | 7 values + OTHER | `format_risk_rating()` | **Needed** |
| `$TXNCAT` | Character | 10 values + OTHER | `format_txn_category()` | **Exists** in target repo |
| `DELQBKT` | Numeric range | 7 buckets | `format_delinquency_bucket()` | **Needed** — range-based, requires nested CASE |
| `BALRANGE` | Numeric range | 8 buckets | `format_balance_range()` | **Needed** — range-based |
| `$REGION` | Character | 7 values + OTHER | `format_region()` | **Needed** |
| `$CUSTSEG` | Character | 6 values + OTHER | `format_customer_segment()` | **Exists** in target repo |
| `$LNPURP` | Character | 8 values + OTHER | `format_loan_purpose()` | **Needed** |

### Insurance Formats (5 total)

| Format Name | Type | Values | dbt Macro | Seed Table |
|-------------|------|--------|-----------|------------|
| `$POLTYPE` | Character | 13 values + OTHER | `format_policy_type()` | **Needed** |
| `$CLMSTAT` | Character | 12 values + OTHER | `format_claim_status()` | **Needed** |
| `$RISKCAT` | Character | 5 values + OTHER | `format_risk_category()` | **Needed** |
| `$COVTYPE` | Character | 9 values + OTHER | `format_coverage_type()` | **Needed** |
| `LOSSRANGE` | Numeric range | 7 buckets | `format_loss_range()` | **Needed** — range-based |

**Summary**: 4 of 14 formats already have dbt macros in the target repo. 10 need to be created.
