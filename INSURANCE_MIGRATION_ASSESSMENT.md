# Insurance Domain: SAS Migration Assessment

## 1. Artifact Inventory

| Filename | Lines | Primary Purpose | SAS PROCs Used | Data Steps | SQL Pass-Throughs |
|---|---|---|---|---|---|
| `claims_processing.sas` | 238 | Daily claims intake, validation against policy data, auto-adjudication rules, fraud screening, claims register update | `PROC SQL`, `PROC APPEND` (×3), `PROC DATASETS` | 5 (`CLAIMS_VALID`/`CLAIMS_INVALID`, `FRAUD_ALERTS`, `AUTO_ADJUDICATED`/`MANUAL_REVIEW`, `CLAIMS_COMBINED`) | 0 (Teradata accessed via LIBNAME engine, not explicit pass-through) |
| `policy_valuation.sas` | 206 | Monthly policy book valuation — in-force metrics, premium adequacy, loss ratios, IBNR reserve estimates | `PROC SQL` (×3), `PROC MEANS`, `PROC APPEND` (implicit via DATA step output), `PROC DATASETS` | 2 (`POLICY_VALUATION` merge step, `LOSS_RATIO_SUMMARY` enhancement) | 0 (Teradata accessed via LIBNAME engine) |

**Supporting artifacts:**

| Artifact | Lines | Role |
|---|---|---|
| `Config/autoexec.sas` | 118 | Global library assignments, macro variables, DB connections |
| `Formats/insurance_formats.sas` | 85 | Custom format catalog (`$POLTYPE`, `$CLMSTAT`, `$RISKCAT`, `$COVTYPE`, `LOSSRANGE`) |
| `BatchJobs/run_daily_insurance.sas` | 133 | Master batch orchestrator — executes claims_processing then policy_valuation |

---

## 2. Data Lineage

### 2.1 claims_processing.sas

| Direction | Dataset / Library | Description |
|---|---|---|
| **Input** | `RAW_INS.CLAIMS_FEED_YYYYMMDD` | Daily claims feed file (date-stamped) |
| **Input** | `RAW_INS.POLICIES` | Policy master (filtered to `STATUS='ACTIVE'`) |
| **Input** | `TERA_DW.FRAUD_INDICATORS` | Fraud scoring data from Teradata (`FRAUD_SCORE`, `INDICATOR_FLAGS`) |
| **Output** | `STG_INS.CLAIMS_REGISTER` | Appended adjudicated claims (auto + manual) |
| **Output** | `STG_INS.CLAIMS_REVIEW_QUEUE` | Appended claims requiring manual review |
| **Output** | `STG_INS.FRAUD_ALERTS` | High-risk fraud alerts (conditionally appended) |
| **Temp (WORK)** | `CLAIMS_VALID`, `CLAIMS_INVALID` | Validation split |
| **Temp (WORK)** | `FRAUD_CHECK` | Claims enriched with fraud scores |
| **Temp (WORK)** | `FRAUD_ALERTS` | Staging for high-risk alerts |
| **Temp (WORK)** | `AUTO_ADJUDICATED`, `MANUAL_REVIEW` | Adjudication split |
| **Temp (WORK)** | `CLAIMS_COMBINED` | Union of auto + manual before register append |

**External systems:** Teradata (`TERA_DW`) read via SAS/ACCESS LIBNAME engine; SMTP email via `%sendmail` on fraud alerts.

### 2.2 policy_valuation.sas

| Direction | Dataset / Library | Description |
|---|---|---|
| **Input** | `RAW_INS.POLICIES` | Policy master (filtered to active, in-force on valuation date) |
| **Input** | `RAW_INS.CLAIMS` | Claims history (12-month lookback window) |
| **Input** | `RAW_INS.PREMIUMS` | Premium payment records (YTD) |
| **Input** | `TERA_DW.ACTUARIAL_TABLES` | Actuarial reference data (declared in header; not directly referenced in code — potential future dependency) |
| **Output** | `STG_INS.POLICY_VALUATION` | Per-policy valuation metrics (labeled by month) |
| **Output** | `REPORTS.LOSS_RATIO_SUMMARY` | Aggregated loss ratios by line of business |
| **Temp (WORK)** | `INFORCE` | Extracted in-force policies with earned premium calc |
| **Temp (WORK)** | `CLAIMS_EXP` | Aggregated claims experience per policy |
| **Temp (WORK)** | `PREMIUM_COLL` | Aggregated premium collections per policy |

**External systems:** Teradata (`TERA_DW`) read via SAS/ACCESS LIBNAME engine.

---

## 3. Macro Dependencies

| Macro | Source File | Parameters | Purpose | Shared / Insurance-Specific |
|---|---|---|---|---|
| `%parmv` | `Macro/parmv.sas` | Positional: macro var name; `_req=`, `_val=`, `_words=`, `_case=`, `_msg=`, `_varchk=`, `_def=` | Parameter validation — sets `parmerr=1` and logs ERROR on invalid values | **Shared** (used across all domains) |
| `%nobs` | `Macro/nobs.sas` | Positional: dataset name; `MVAR=` | Returns observation count from dataset descriptor or PROC SQL fallback | **Shared** (used across all domains) |
| `%sendmail` | `Macro/sendmail.sas` | `METADATA=`, `TO=`, `CC=`, `BCC=`, `FROM=`, `SUBJECT=`, `BODY=`, `ATTACH=` | Sends email via SAS SMTP using metadata dataset; depends on `%parmv` and `%seplist` | **Shared** (used across all domains) |
| `%seplist` | `Macro/seplist.sas` | List processing / delimiter insertion | Converts space-delimited lists into custom-delimited strings; called by `%sendmail` | **Shared** (utility macro) |

**Notes:**
- All four macros are **shared utilities** — none are insurance-specific.
- `claims_processing.sas` explicitly `%include`s `parmv`, `nobs`, and `sendmail` from `/opt/sas/custom/macros/`.
- `policy_valuation.sas` explicitly `%include`s `parmv` and `nobs`.
- The hash object in `claims_processing.sas` is implemented **inline** using `declare hash` / `h_pol.find()` — it does not use the `%hash_define` or `%hash_lookup` utility macros from the Macro library.
- The batch orchestrator (`run_daily_insurance.sas`) additionally calls `%sendmail` for failure notifications and uses `%include` to execute child programs.
- `autoexec.sas` sets autocall paths (`sasautos`), so macros may also resolve via autocall without explicit `%include`.

---

## 4. Complexity Scores

Scoring scale: **1** (trivial) → **5** (highly complex)

| Dimension | claims_processing.sas | policy_valuation.sas | Weight |
|---|---|---|---|
| Data Volume Handling | 3 — date-stamped daily feed; PROC APPEND for incremental loads; WORK cleanup | 4 — 12-month claims lookback; three-way merge of policies × claims × premiums; PROC MEANS aggregation | 20% |
| Business Logic Complexity | 4 — multi-tier adjudication rules (auto-approve, auto-deny, manual); fraud risk tiering (HIGH/MEDIUM/LOW); deductible math | 4 — earned premium pro-rata calc; loss ratio; combined ratio (30% expense load); IBNR estimation; premium adequacy; renewal flagging | 25% |
| External Dependencies | 4 — Teradata fraud indicators; SMTP email alerts; RAW_INS feed files; date-stamped input naming | 3 — Teradata actuarial tables (declared, not yet coded); RAW_INS policy/claims/premiums | 20% |
| Error Handling Sophistication | 3 — %parmv validation; feed existence check with %goto ABORT; WORK cleanup; conditional email alerts | 2 — %parmv validation; WORK cleanup; no explicit error branching | 15% |
| Macro Usage Depth | 3 — %parmv, %nobs, %sendmail; inline hash object; conditional %goto; macro variables for date formatting | 2 — %parmv, %nobs; conditional macro logic for LOB filter; simpler macro variable usage | 20% |

### Overall Weighted Scores

| Program | Weighted Score | Rating |
|---|---|---|
| `claims_processing.sas` | **3.45** | Medium-High |
| `policy_valuation.sas` | **3.15** | Medium |

*Calculation: claims = 3×0.20 + 4×0.25 + 4×0.20 + 3×0.15 + 3×0.20 = 3.45; valuation = 4×0.20 + 4×0.25 + 3×0.20 + 2×0.15 + 2×0.20 = 3.15*

---

## 5. Recommended Migration Sequence

| Order | Program | Estimated Effort | Rationale |
|---|---|---|---|
| **1** | `Formats/insurance_formats.sas` | **S** | **Prerequisite.** Format catalog (`$POLTYPE`, `$CLMSTAT`, `$RISKCAT`, `$COVTYPE`, `LOSSRANGE`) must be migrated first as both programs depend on these formats. Convert to lookup tables / CASE expressions / enum mappings in the target platform. |
| **2** | `Macro/parmv.sas`, `Macro/nobs.sas` | **S** | **Prerequisite.** Shared utility macros. `parmv` → parameter validation function/decorator. `nobs` → row-count utility (e.g., `SELECT COUNT(*)` or DataFrame method). |
| **3** | `policy_valuation.sas` | **L** | Lower complexity (3.15). Pure SQL/DATA step logic — no external email, no hash objects. Three-way merge and actuarial calculations are well-suited for SQL window functions / CTEs. IBNR logic is a clear, formulaic calculation. Migrate first to establish the valuation pipeline, as it has no dependency on claims_processing output. |
| **4** | `claims_processing.sas` | **L** | Higher complexity (3.45). Requires hash object replacement (JOIN or broadcast join), fraud screening integration with Teradata, multi-path adjudication logic, and email alerting replacement. Depends on Teradata connectivity being established. |
| **5** | `Macro/sendmail.sas` | **M** | Replace SAS SMTP with target platform alerting (e.g., SMTP library, SNS, Slack webhook). Only needed once claims_processing is migrated. |
| **6** | `BatchJobs/run_daily_insurance.sas` | **M** | Orchestrator migration — replace with Airflow DAG, dbt run sequence, Databricks Workflow, or equivalent scheduler. Migrate last since it wraps the child programs. |

**Effort key:** S = Small (1–2 days), M = Medium (3–5 days), L = Large (1–2 weeks), XL = Extra Large (2+ weeks)

---

## 6. Risk Factors & Notes

### 6.1 SAS-Specific Features Requiring Special Handling

| Feature | Location | Migration Risk | Notes |
|---|---|---|---|
| **Hash Object** (`declare hash`) | `claims_processing.sas` lines 47–52 | **High** | Used for in-memory policy lookup during DATA step. Replace with JOIN (SQL) or broadcast join (Spark). Must preserve the single-pass lookup semantics and `rc` return code error handling. |
| **RETAIN Logic** (implicit via DATA step) | `policy_valuation.sas` merge step | **Medium** | The three-way `MERGE ... BY POLICY_ID` with `if a` relies on SAS DATA step RETAIN behavior for carrying forward variables. Replace with SQL LEFT JOIN. |
| **Custom Formats** (`$POLTYPE.`, `$CLMSTAT.`, `$RISKCAT.`) | Both programs | **Medium** | Used for display and implicit data validation. Convert to dimension/lookup tables or CASE WHEN expressions. The `fmtsearch` order in autoexec.sas (BANKING, INSURANCE, COMMON, WORK, LIBRARY) must be understood to resolve format conflicts. |
| **PROC APPEND with FORCE** | Both programs (claims: ×3, valuation: implicit) | **Medium** | Incremental load pattern. Replace with INSERT INTO, MERGE/UPSERT, or incremental model in dbt. The `FORCE` option allows schema mismatches — target platform may need explicit schema evolution handling. |
| **PROC MEANS with NWAY** | `policy_valuation.sas` line 169 | **Low** | Aggregation by `POLICY_TYPE`. Straightforward replacement with `GROUP BY` in SQL. |
| **Date-Stamped Dataset Names** | `claims_processing.sas` line 23 | **Medium** | Dynamic dataset name construction (`CLAIMS_FEED_%sysfunc(...)`) based on processing date. Replace with parameterized table names or date-partitioned tables. |
| **Macro Conditional Logic** | `policy_valuation.sas` lines 66–68 | **Low** | `%if &lob ne ALL` conditional SQL filter. Replace with parameterized WHERE clause or Jinja conditional in dbt. |

### 6.2 IBNR and Actuarial Calculations

- **IBNR Estimate** (`policy_valuation.sas` line 155): Simplified formula — `max(0, YTD_EARNED_PREMIUM × 0.15 − TOTAL_PAID)`. This is a basic percentage-of-premium method. Production actuarial systems typically use chain-ladder, Bornhuetter-Ferguson, or other triangle-based methods. Validate with actuarial team whether this simplified approach is intentional or should be enhanced during migration.
- **Combined Ratio** (line 144): Uses a hard-coded 30% expense load (`LOSS_RATIO + 0.30`). Confirm whether this should be parameterized or sourced from an expense table.
- **TERA_DW.ACTUARIAL_TABLES** is declared in the program header as an input but is not referenced in the current code. This may indicate planned functionality or a documentation discrepancy — clarify before migration.

### 6.3 Database Connectivity Patterns

| Connection | Engine | Used By | Migration Consideration |
|---|---|---|---|
| `TERA_DW` (Teradata) | SAS/ACCESS LIBNAME (`teradata`) | `claims_processing.sas` (FRAUD_INDICATORS), `policy_valuation.sas` (ACTUARIAL_TABLES — header only) | Teradata access is via LIBNAME engine (implicit SQL generation), not explicit pass-through. Migration target must establish equivalent connectivity (JDBC/ODBC). Bulk-load option (`bulkload=yes`) in autoexec suggests large data volumes. |
| `ORA_DW` (Oracle) | SAS/ACCESS LIBNAME (`oracle`) | Not directly used by insurance programs (banking domain) | No immediate migration concern for insurance, but shared autoexec means Oracle credentials are loaded. |
| SMTP | SAS `filename email` | `claims_processing.sas` via `%sendmail` | Email alerts for fraud (SIU) and batch failures. Replace with platform-native alerting. |

### 6.4 Implicit Data Dependencies

- **Batch execution order matters**: `run_daily_insurance.sas` runs `claims_processing` (Step 1) before `policy_valuation` (Step 2). While policy_valuation does not directly consume claims_processing output, the `STG_INS.CLAIMS_REGISTER` updates may affect downstream reporting that depends on both datasets being current.
- **Global macro variables**: Both programs rely on `&CURR_DT` set in `autoexec.sas` (or overridden by the batch orchestrator). The orchestrator propagates `run_date` → `CURR_DT` for consistent date handling across steps.
- **Library paths are environment-specific**: All `/data/sas/...` paths and `/opt/sas/...` paths are hard-coded in `autoexec.sas`. Migration must replace these with target platform storage references (e.g., Unity Catalog schemas, S3 paths, ADLS containers).
- **Format catalog search order** (`fmtsearch=(BANKING INSURANCE COMMON WORK LIBRARY)`) means format name collisions across catalogs are resolved by order. Ensure no format name conflicts exist when consolidating to lookup tables.

### 6.5 Testing and Validation Considerations

- Both programs lack unit tests — validation is limited to `%parmv` parameter checks and dataset existence checks.
- **Reconciliation approach**: Compare row counts (`%nobs`), sum of key monetary fields (`CLAIMED_AMOUNT`, `APPROVED_AMOUNT`, `YTD_EARNED_PREMIUM`, `TOTAL_INCURRED`), and distribution of categorical fields (`ADJUDICATION_RESULT`, `FRAUD_RISK`, `POLICY_TYPE`) between SAS output and migrated output.
- The `REPORTS.LOSS_RATIO_SUMMARY` output from `policy_valuation.sas` provides a natural validation checkpoint — aggregate loss ratios by LOB should match exactly post-migration.
- `PROC DATASETS ... DELETE` cleanup at the end of each program means intermediate WORK datasets are not preserved for debugging. Consider adding checkpoint/audit logging in the migrated version.
