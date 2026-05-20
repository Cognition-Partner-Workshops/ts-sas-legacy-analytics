# Macro Dependency Catalog

Full catalog of the 92 SAS macros in the `Macro/` directory with migration relevance classification.

---

## Macros Used by Business Programs (Migration-Critical)

These macros are directly `%INCLUDE`d or invoked by the 8 business programs and 2 batch orchestrators.

| Macro | Lines | Purpose | Called By | dbt Equivalent | Migration Action |
|-------|:-----:|---------|-----------|----------------|------------------|
| `parmv.sas` | 359 | Parameter validation — checks required/optional params, valid value lists, type coercion (0/1 → boolean) | All 8 programs | dbt `config()` validation or Jinja `{% if %}` assertions | **Port** — Create a dbt macro `validate_var()` or use dbt native `config(required=true)` |
| `nobs.sas` | 253 | Return observation count from dataset descriptor or PROC SQL | All 8 programs | `run_query("SELECT COUNT(*) ...")` or dbt `adapter.get_relation()` | **Port** — Create `get_row_count()` dbt macro |
| `lock.sas` | 352 | Obtain/release dataset lock with retry, timeout, and email on failure | `daily_transaction_processing`, `credit_risk_scoring` | Not needed — Delta Lake ACID | **Drop** — Document that Delta transactions replace locking |
| `sendmail.sas` | 260 | Send email via SAS SMTP with metadata-driven body, attachments | `load_customer_accounts`, `claims_processing`, both batch orchestrators | Databricks Workflow notifications / SQL Alerts / webhook | **Replace** — Configure Workflow alerting + webhook for SIU alerts |
| `export_xlsx.sas` | 101 | Wrapper for PROC EXPORT to Excel (calls `export_dbms`) | `monthly_regulatory_reporting`, `customer_profitability` | Python `openpyxl` in Databricks notebook | **Replace** — Create Python notebook task in Workflow |
| `export_dbms.sas` | 520 | Core PROC EXPORT wrapper with error handling | Called by `export_xlsx` | Same as above | **Replace** — Covered by xlsx replacement |
| `seplist.sas` | ~150 | Generate separated list from space-delimited input (SQL column lists) | `Parent-Child-Index` | Jinja `{{ list \| join(', ') }}` | **Port** — Trivial Jinja replacement |

**Total migration-critical macros: 7** (of which 2 can be dropped, 2 replaced, 3 ported)

---

## Macros Referenced by Critical Macros (Transitive Dependencies)

| Macro | Lines | Purpose | Called By | Migration Action |
|-------|:-----:|---------|-----------|------------------|
| `get_data_attr.sas` | ~200 | Return dataset attributes (NOBS, NVAR, engine, etc.) | `lock.sas` | **Drop** (parent dropped) |
| `handle.sas` | 451 | Close open file handles on locked datasets, send notification | `lock.sas` | **Drop** (parent dropped) |

---

## Full Macro Library Classification

### Category A: Data I/O and Export (16 macros)

| Macro | Lines | Purpose | Migration Relevance |
|-------|:-----:|---------|:------------------:|
| `export.sas` | 355 | Replacement for PROC EXPORT | Low |
| `export_csv.sas` | ~100 | CSV export wrapper | Low — Databricks can write CSV natively |
| `export_dbms.sas` | 520 | Core PROC EXPORT wrapper | Medium — used by export_xlsx |
| `export_dlm.sas` | 614 | Delimited file export | Low |
| `export_rldx.sas` | 390 | RLDX format export | None |
| `export_sas.sas` | 363 | SAS dataset copy | None |
| `export_saphari.sas` | 336 | SAPHARI-specific export | None |
| `export_spss.sas` | ~100 | SPSS export wrapper | None |
| `export_stata.sas` | ~100 | Stata export wrapper | None |
| `export_tab.sas` | ~100 | Tab-delimited export | Low |
| `export_xlsx.sas` | 101 | Excel export wrapper | **High** — used in production |
| `excel2sas.sas` | 557 | Excel import to SAS | Low |
| `txt2pdf.sas` | 733 | Text to PDF conversion | None |
| `txt2rtf.sas` | ~150 | Text to RTF conversion | None |
| `log2pdf.sas` | ~100 | Log file to PDF | None |
| `reduce_pixel.sas` | ~100 | Image pixel reduction | None |

### Category B: Data Utilities (18 macros)

| Macro | Lines | Purpose | Migration Relevance |
|-------|:-----:|---------|:------------------:|
| `nobs.sas` | 253 | Observation count | **High** — used in all programs |
| `check_if_empty.sas` | ~100 | Check empty dataset | Low |
| `empty.sas` | ~100 | Check empty dataset (alt) | Low |
| `varexist.sas` | ~100 | Check variable exists | Low |
| `varlist.sas` | ~150 | Return variable list | Low |
| `varlist2.sas` | ~150 | Variable list variant | Low |
| `get_data_attr.sas` | ~200 | Dataset attributes | Low |
| `get_lib_attr.sas` | ~150 | Library attributes | None |
| `get_dups.sas` | 327 | Find duplicate records | Low |
| `guess_pk.sas` | 915 | Guess primary key | Low |
| `compare.sas` | 522 | PROC COMPARE wrapper | Low — useful for validation |
| `subset_data.sas` | ~100 | Dataset subset | None |
| `hash_define.sas` | 499 | Hash object definition | Medium |
| `hash_lookup.sas` | 310 | Hash object lookup | Medium |
| `hash_split_dataset.sas` | ~150 | Hash-based dataset split | Low |
| `transpose.sas` | 351 | PROC TRANSPOSE wrapper | Low |
| `create_format.sas` | 408 | Create format from dataset | Medium |
| `CreateTableOrView.sas` | 1541 | Dynamic table/view creation | Low |

### Category C: String and Macro Utilities (15 macros)

| Macro | Lines | Purpose | Migration Relevance |
|-------|:-----:|---------|:------------------:|
| `parmv.sas` | 359 | Parameter validation | **High** — used in all programs |
| `seplist.sas` | ~150 | Separated list generator | **Medium** — used in Parent-Child-Index |
| `stp_seplist.sas` | ~100 | STP variant of seplist | None |
| `count_words.sas` | ~100 | Word count in string | None |
| `dedup_string.sas` | ~150 | Remove duplicate words | None |
| `dedup_mstring.sas` | ~100 | Macro string dedup | None |
| `squote.sas` | ~50 | Single-quote wrapper | None |
| `splitvar.sas` | ~100 | Split variable values | None |
| `format_text.sas` | ~100 | Text formatting | None |
| `justify.sas` | ~100 | Text justification | None |
| `align_decimals.sas` | 442 | Decimal alignment | None |
| `fmtexist.sas` | ~100 | Check format exists | None |
| `fmtlist.sas` | 299 | List formats in catalog | None |
| `max_decimals.sas` | ~100 | Max decimal places | None |
| `symget.sas` | ~100 | Macro variable getter | None |

### Category D: System and Infrastructure (17 macros)

| Macro | Lines | Purpose | Migration Relevance |
|-------|:-----:|---------|:------------------:|
| `lock.sas` | 352 | Dataset locking | **High** — used in 2 programs (drop) |
| `handle.sas` | 451 | File handle management | Medium — dependency of lock |
| `sendmail.sas` | 260 | Email notification | **High** — used in 4 places (replace) |
| `logparse.sas` | 654 | Log file parser | Low |
| `batch_submit.sas` | ~100 | Batch session submission | None |
| `stp_batch_submit.sas` | 350 | STP batch submission | None |
| `stp_session.sas` | ~100 | STP session management | None |
| `kill.sas` | ~100 | Process termination | None |
| `optsave.sas` | ~100 | Save SAS options | None |
| `optload.sas` | ~100 | Load SAS options | None |
| `optval.sas` | ~100 | Get option value | None |
| `delete_file.sas` | ~100 | File deletion | None |
| `create_directory.sas` | ~100 | Directory creation (dlcreatedir) | None |
| `execpath.sas` | ~100 | Execution path | None |
| `marker.sas` | ~100 | Execution marker | None |
| `bench.sas` | ~100 | Benchmark timer | None |
| `dump_mvars.sas` | ~100 | Dump macro variables | None |

### Category E: Date/Time and Math (8 macros)

| Macro | Lines | Purpose | Migration Relevance |
|-------|:-----:|---------|:------------------:|
| `age.sas` | ~100 | Age calculation | Low |
| `date_impute.sas` | 326 | Partial date imputation | Low |
| `time_interval.sas` | ~100 | Time interval calculation | Low |
| `sql_datetime.sas` | ~100 | SQL datetime conversion | Low |
| `create_datetime_range.sas` | ~100 | Datetime range creation | Low |
| `IsNum.sas` | ~100 | Numeric check | None |
| `IsNumD.sas` | ~100 | Numeric check (data step) | None |
| `IsNumM.sas` | ~100 | Numeric check (macro) | None |

### Category F: Reporting and Presentation (6 macros)

| Macro | Lines | Purpose | Migration Relevance |
|-------|:-----:|---------|:------------------:|
| `pagexofy.sas` | 470 | Page X of Y headers | None |
| `attrib.sas` | ~150 | Attribute statements from template | None |
| `randlist.sas` | ~100 | Random list generation | None |
| `get_permutations.sas` | 501 | Permutation generation | None |
| `get_parameters.sas` | 446 | Parameter extraction | None |
| `@TEMPLATE.sas` | ~50 | Macro template | None |

### Category G: External System Integration (5 macros)

| Macro | Lines | Purpose | Migration Relevance |
|-------|:-----:|---------|:------------------:|
| `queryActiveDirectory.sas` | 480 | Active Directory lookup | None |
| `useridToEmail.sas` | ~100 | Userid to email mapping | None |
| `getpassword.sas` | ~100 | Password retrieval | None — Databricks Secrets |
| `libname_sqlsvr.sas` | ~100 | SQL Server LIBNAME | None |
| `libname_attr_sqlsvr.sas` | ~100 | SQL Server attributes | None |

### Category H: Advanced Processing (7 macros)

| Macro | Lines | Purpose | Migration Relevance |
|-------|:-----:|---------|:------------------:|
| `loop.sas` | ~100 | Loop control | None |
| `loop_control.sas` | ~150 | Advanced loop control | None |
| `execute_macro.sas` | ~100 | Dynamic macro execution | None |
| `RunAll.sas` | 303 | Async program runner | Low — Databricks parallel tasks |
| `RunAll_ControlTable.sas` | ~200 | Control table runner | Low |
| `realloc_concat_libs.sas` | ~100 | Library concatenation | None |
| `dirlist.sas` | ~100 | Directory listing | None |

---

## Migration Action Summary

| Action | Count | Macros |
|--------|:-----:|--------|
| **Port to dbt** | 3 | `parmv`, `nobs`, `seplist` |
| **Replace** | 3 | `sendmail` → Workflow alerts, `export_xlsx`/`export_dbms` → Python notebook |
| **Drop** | 3 | `lock`, `handle`, `get_data_attr` |
| **No action needed** | 83 | Utility library not referenced by business programs |
