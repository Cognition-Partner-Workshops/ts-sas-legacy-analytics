# Construct Inventory

> Detailed inventory of SAS constructs across all programs, categorized for migration planning.

---

## 1. DATA Steps (25 total across estate)

### Business Programs (14 DATA steps)

| Program | Line | Output Dataset(s) | Key Logic |
|---------|------|--------------------|-----------|
| `load_customer_accounts.sas` | 82 | `STG_BANK.CUST_ACCOUNTS_DAILY`, `WORK.ACCT_EXCEPTIONS` | Business rules: utilization %, dormancy flag, high-balance flag, negative balance exception, high-utilization exception, missing risk rating exception |
| `daily_transaction_processing.sas` | 45 | `WORK.TXN_VALIDATED`, `WORK.TXN_REJECTED` | Input validation: required fields, amount range, valid type codes, future-date check |
| `daily_transaction_processing.sas` | 137 | `WORK.TXN_WITH_BALANCE` | **RETAIN** pattern: cumulative running balance by ACCOUNT_ID with BY-group reset |
| `daily_transaction_processing.sas` | 222 | `CURATED.RUNNING_BALANCES` | Persist running balance subset (KEEP list) |
| `credit_risk_scoring.sas` | 92 | `WORK.SCORED` | WOE scorecard: FICO, utilization, DPD, age, LTV bins → log-odds → PD → LGD → EAD → expected loss → risk rating assignment |
| `monthly_regulatory_reporting.sas` | — | (no DATA steps — entirely PROC SQL) | — |
| `claims_processing.sas` | 38 | `WORK.CLAIMS_VALID`, `WORK.CLAIMS_INVALID` | **Hash object** lookup against active policies; validates policy existence, date range, sum insured |
| `claims_processing.sas` | 112 | `WORK.FRAUD_ALERTS` | WHERE subset of fraud check results |
| `claims_processing.sas` | 127 | `WORK.AUTO_ADJUDICATED`, `WORK.MANUAL_REVIEW` | Auto-adjudication rules: deny (high fraud), auto-approve (low risk + small claim), route to manual review |
| `claims_processing.sas` | 184 | `WORK.CLAIMS_COMBINED` | SET + derived columns (processing date, claim status with format) |
| `policy_valuation.sas` | 123 | `STG_INS.POLICY_VALUATION` | 3-way MERGE (in-force + claims + premiums); loss ratio, combined ratio, IBNR estimate, total reserve |
| `policy_valuation.sas` | 184 | `REPORTS.LOSS_RATIO_SUMMARY` | Aggregate loss ratios and combined ratios by policy type |
| `customer_profitability.sas` | 100 | `REPORTS.CUSTOMER_PNL` | 3-way MERGE (interest + fees + ECL); P&L assembly: net profit, ROA, profitability tier |

### Batch Orchestrator DATA Steps (2)

| Program | Line | Output | Purpose |
|---------|------|--------|---------|
| `run_daily_banking.sas` | 31 | `WORK.BATCH_CONTROL` | Empty control table scaffold |
| `run_daily_insurance.sas` | 27 | `WORK.BATCH_CONTROL` | Empty control table scaffold |

### Standalone Program DATA Steps (9 in Parent-Child-Index.sas)

| Line | Output | Purpose |
|------|--------|---------|
| 5, 143 | `source` (indexed) | Hierarchical test data with DATALINES |
| 27, 44 | `option1` | Index KEY= lookup for top-level parent |
| 67 | `option2` | Hierarchy string derivation (CATX with pipe delimiter) |
| 95 | `dim_acct` | Dimension dataset with ARRAY and SCAN |
| 172 | `dim_acct_names` | Dimension with INFILE DATALINES DSD |
| 199 | `dim_acct` | Snowflake schema dimension with KEY= lookup |
| 217 | `v_dim_acct` (view) | DATA step view joining hierarchy + names via KEY= |
| 235 | `fact_stores` | Hash object join (%hash_define + %hash_lookup) |

---

## 2. PROC SQL (25 instances)

### Banking Domain (11 PROC SQL blocks)

| Program | Line | Purpose | Complexity |
|---------|------|---------|------------|
| `load_customer_accounts.sas` | 34 | Extract from Oracle DW: INNER JOIN accounts + demographics, conditional WHERE via macro | Multi-table join, macro-driven WHERE |
| `load_customer_accounts.sas` | 167 | Insert exceptions into staging | Simple INSERT |
| `daily_transaction_processing.sas` | 105 | Enrich transactions: LEFT JOIN to account data, CASE WHEN for post-txn balance | CASE expression, LEFT JOIN |
| `daily_transaction_processing.sas` | 159 | 90-day rolling statistics (mean, std, count) by account | Aggregation with date arithmetic |
| `daily_transaction_processing.sas` | 172 | Anomaly detection: Z-score, overdraft, large withdrawal, orphan account | Calculated columns, HAVING filter |
| `credit_risk_scoring.sas` | 32 | Assemble scoring features: 4-way join (accounts + bureau + payments + collateral), correlated subquery for latest bureau score | Complex multi-join, correlated subquery |
| `credit_risk_scoring.sas` | 202 | Risk migration matrix: join scored vs. current ratings | CASE WHEN for migration direction |
| `monthly_regulatory_reporting.sas` | 40 | RWA by category: Basel III risk weights via CASE WHEN, aggregation | Complex CASE, GROUP BY |
| `monthly_regulatory_reporting.sas` | 72 | Delinquency aging: 30/60/90/120/180+ bucket CASE, custom ORDER BY | Bucketed aggregation |
| `monthly_regulatory_reporting.sas` | 114 | Loan loss provision coverage: NPL ratio, allowance coverage | Conditional aggregation |
| `monthly_regulatory_reporting.sas` | 169 | Capital adequacy: CET1/Tier1/Total ratios, pass/fail flags | Nested CASE expressions |

### Insurance Domain (3 PROC SQL blocks)

| Program | Line | Purpose | Complexity |
|---------|------|---------|------------|
| `claims_processing.sas` | 93 | Fraud screening: LEFT JOIN to Teradata fraud indicators, CASE WHEN risk level | Cross-platform join (Teradata) |
| `policy_valuation.sas` | 34 | Extract in-force policies: date arithmetic, conditional LOB filter, earned premium pro-rata | Date math, macro-conditional WHERE |
| `policy_valuation.sas` | 78 | Claims experience 12-month window: aggregation with conditional SUM | Multiple CASE aggregations |
| `policy_valuation.sas` | 102 | Premium collections: payment status aggregation | Conditional COUNT |

### Reports Domain (3 PROC SQL blocks)

| Program | Line | Purpose | Complexity |
|---------|------|---------|------------|
| `customer_profitability.sas` | 35 | Interest income by customer: lending vs. deposit, NIM | CASE aggregation, calculated columns |
| `customer_profitability.sas` | 65 | Fee income from transactions: fee and interest split | Conditional SUM |
| `customer_profitability.sas` | 85 | Expected credit loss: latest score date via correlated subquery | Correlated subquery |

### Batch Orchestrators (2 PROC SQL blocks)

| Program | Line | Purpose |
|---------|------|---------|
| `run_daily_banking.sas` | 80 | Insert step status into control table |
| `run_daily_insurance.sas` | 70 | Insert step status into control table |

### Parent-Child-Index.sas (4 PROC SQL blocks)

| Line | Purpose |
|------|---------|
| 88 | SELECT INTO for max hierarchy depth |
| 113 | Dynamic view creation with %seplist columns |
| 245 | Fact table via SQL LEFT JOIN (alternative to hash) |
| 266 | Dynamic view with %seplist for reporting |

---

## 3. Hash Objects (2 programs, 4 instances)

| Program | Line | Hash Name | Key | Data Variables | Purpose |
|---------|------|-----------|-----|----------------|---------|
| `claims_processing.sas` | 47 | `h_pol` | `POLICY_ID` | `POLICY_TYPE`, `EFFECTIVE_DATE`, `EXPIRATION_DATE`, `SUM_INSURED`, `DEDUCTIBLE` | Validate claims against active policies (WHERE filter on load) |
| `Parent-Child-Index.sas` | 239 | via `%hash_define` | `acct` | `Lev_Id` | Dimension lookup for fact table join |
| `Parent-Child-Index.sas` | 240 | via `%hash_lookup` | (same) | (same) | Execute the defined hash lookup |

### Hash Macros in Library (not directly invoked by main programs except Parent-Child-Index)

| Macro | Purpose | Migration Target |
|-------|---------|-----------------|
| `%hash_define` | Define hash with configurable keys/data vars | Python dict / Spark broadcast join |
| `%hash_lookup` | Perform lookup from defined hash | Python dict.get() / Spark join |
| `%hash_split_dataset` | Split dataset via hash | Pandas groupby / Spark partitionBy |

---

## 4. RETAIN Patterns (1 instance)

| Program | Line | Variable | BY Group | Purpose | Migration Target |
|---------|------|----------|----------|---------|-----------------|
| `daily_transaction_processing.sas` | 141 | `RUNNING_BALANCE` | `ACCOUNT_ID TRANSACTION_DATE TRANSACTION_ID` | Cumulative running balance: reset on `first.ACCOUNT_ID`, then add/subtract based on transaction type | `SUM() OVER (PARTITION BY account_id ORDER BY transaction_date, transaction_id)` window function |

---

## 5. Format References

### Format Catalog Definitions (2 files, 17 formats)

#### Banking Formats (`Formats/banking_formats.sas` → `BANKING.FORMATS`)

| Format | Type | Values | Used In |
|--------|------|--------|---------|
| `$ACCTTYPE` | Character | 11 account types (CHK, SAV, MMA, CD, IRA, LOC, MTG, AUTO, PERS, CC, HELC) | `load_customer_accounts.sas` (line 87) |
| `$ACCTSTAT` | Character | 8 account statuses (A, C, D, F, R, S, P, W) | `load_customer_accounts.sas` (line 88) |
| `RISKRATE` | Numeric | 7 risk levels (1=Minimal … 7=Loss Expected) | `load_customer_accounts.sas` (line 89) |
| `$TXNCAT` | Character | 10 transaction categories | Referenced in validation logic (not as FORMAT statement) |
| `DELQBKT` | Numeric range | 7 delinquency buckets (Current … 180+) | Conceptually in `monthly_regulatory_reporting.sas` (inline CASE instead) |
| `BALRANGE` | Numeric range | 8 balance ranges | Available but not directly applied |
| `$REGION` | Character | 7 regions (NE, SE, MW, SW, W, NW, HQ) | `load_customer_accounts.sas` (line 91) |
| `$CUSTSEG` | Character | 6 customer segments (RET, PREM, PB, SMB, COMM, CORP) | `load_customer_accounts.sas` (line 90) |
| `$LNPURP` | Character | 8 loan purposes | Available but not directly applied |

#### Insurance Formats (`Formats/insurance_formats.sas` → `INSURANCE.FORMATS`)

| Format | Type | Values | Used In |
|--------|------|--------|---------|
| `$POLTYPE` | Character | 13 policy types (WL, TL, UL, VL, AUTO, HOME, etc.) | `policy_valuation.sas` (line 131) |
| `$CLMSTAT` | Character | 12 claim statuses (NEW, OPEN, INV, ADJ, PEND, etc.) | `claims_processing.sas` (line 191) |
| `$RISKCAT` | Character | 5 risk categories (STD, PREF, SPRM, SUB, DEC) | `policy_valuation.sas` (line 132) |
| `$COVTYPE` | Character | 9 coverage types | Available but not directly applied |
| `LOSSRANGE` | Numeric range | 7 loss amount ranges | Available but not directly applied |

### Format Search Path (from `autoexec.sas`)

```
fmtsearch=(BANKING INSURANCE COMMON WORK LIBRARY)
```

### Migration Strategy for Formats

| SAS Pattern | Migration Target |
|-------------|-----------------|
| `$ACCTTYPE` value format | dbt seed table `ref('seed_account_types')` + CASE/JOIN |
| `RISKRATE` numeric format | dbt seed table or accepted_values test |
| `DELQBKT` numeric range format | CASE WHEN expression in SQL |
| `BALRANGE` numeric range format | CASE WHEN expression with range logic |
| Inline CASE already used | Direct SQL migration (no format dependency) |

---

## 6. PROC MEANS / PROC SUMMARY (9 instances)

| Program | Line | Proc | CLASS vars | VAR vars | Purpose |
|---------|------|------|------------|----------|---------|
| `load_customer_accounts.sas` | 188 | MEANS | ACCOUNT_TYPE, REGION_CODE | CURRENT_BALANCE, UTILIZATION_PCT, ACCT_AGE_MONTHS | Account summary statistics |
| `credit_risk_scoring.sas` | 246 | MEANS | ACCOUNT_TYPE, NEW_RISK_RATING | PD, LGD, EAD, EXPECTED_LOSS | Risk summary report |
| `policy_valuation.sas` | 169 | MEANS | POLICY_TYPE | YTD_EARNED_PREMIUM, TOTAL_INCURRED, TOTAL_PAID, TOTAL_RESERVE, IBNR_ESTIMATE | Loss ratio summary by LOB |
| `customer_profitability.sas` | 140 | MEANS | CUSTOMER_SEGMENT | TOTAL_REVENUE, OPERATING_COST, TOTAL_ECL, NET_PROFIT, TOTAL_RELATIONSHIP | Segment profitability |
| `customer_profitability.sas` | 150 | MEANS | BRANCH_ID, REGION_CODE | TOTAL_REVENUE, OPERATING_COST, TOTAL_ECL, NET_PROFIT | Branch profitability |
| `Parent-Child-Index.sas` | 59 | SUMMARY | toplevel | amount | Top-level parent sum |
| `Parent-Child-Index.sas` | 130 | SUMMARY | lev: | amount | Hierarchy level summary |
| `Parent-Child-Index.sas` | 281 | SUMMARY | Name: | amount | Named hierarchy summary |

---

## 7. PROC APPEND (9 instances)

| Program | Line | Base Dataset | Locking | Purpose |
|---------|------|-------------|---------|---------|
| `daily_transaction_processing.sas` | 207 | `CURATED.DAILY_TRANSACTIONS` | `%lock` before/after | Append validated transactions |
| `daily_transaction_processing.sas` | 214 | `CURATED.TXN_ANOMALIES` | None | Append anomalies (conditional) |
| `credit_risk_scoring.sas` | 231 | `CURATED.RISK_SCORES` | `%lock` before/after | Append scored results |
| `credit_risk_scoring.sas` | 238 | `CURATED.RISK_MIGRATION` | `%lock` before/after | Append migration records |
| `claims_processing.sas` | 194 | `STG_INS.CLAIMS_REGISTER` | None | Append processed claims |
| `claims_processing.sas` | 199 | `STG_INS.CLAIMS_REVIEW_QUEUE` | None | Append manual review queue |
| `claims_processing.sas` | 205 | `STG_INS.FRAUD_ALERTS` | None | Append fraud alerts (conditional) |
| `run_daily_banking.sas` | 142 | `ARCHIVE.BATCH_HISTORY` | None | Archive batch control table |
| `run_daily_insurance.sas` | 121 | `ARCHIVE.BATCH_HISTORY` | None | Archive batch control table |

---

## 8. Other Notable Constructs

### BY-group Processing
- `daily_transaction_processing.sas:139` — `BY ACCOUNT_ID TRANSACTION_DATE TRANSACTION_ID` (with RETAIN)
- `policy_valuation.sas:127` — `BY POLICY_ID` (3-way MERGE)
- `customer_profitability.sas:104` — `BY CUSTOMER_ID` (3-way MERGE)

### Index KEY= Lookups (Parent-Child-Index.sas)
- Lines 37, 50, 75, 207, 224 — `SET ... KEY=acct / unique` for recursive hierarchy traversal

### PROC DATASETS (Cleanup)
- All 6 business programs use `PROC DATASETS ... DELETE` for WORK library cleanup

### LIBNAME Statements
- `autoexec.sas`: 11 LIBNAME assignments (3 RAW, 3 STG, 3 curated/reports, 2 database — Oracle + Teradata)
- `banking_formats.sas` / `insurance_formats.sas`: 1 LIBNAME each for format catalogs

### Macro Variable Resolution (`&var`)
- Global: `&CURR_DT`, `&PREV_YM`, `&FY_START`, `&ENVIRONMENT`, `&BASE_PATH`, `&LOG_PATH`, `&REPORT_PATH`, `&ARCHIVE_PATH`, `&EMAIL_DL`, `&EMAIL_ONCALL`, `&MAX_OBS_WARN`, `&ABORT_ON_ERR`
- Database credentials: `&ora_uid`, `&ora_pwd`, `&tera_uid`, `&tera_pwd`
- Program-local: `&run_date`, `&txn_date`, `&score_date`, `&proc_date`, `&val_date`, `&report_month`, `&batch_id`, `&nobs_*`

### Error Handling Patterns
- `%GOTO EXIT` / `%GOTO ABORT` — used in `daily_transaction_processing.sas`, `claims_processing.sas`, `load_customer_accounts.sas`
- `&SYSCC` checking — used in both batch orchestrators
- `&ABORT_ON_ERR` global flag — controls batch halt-on-error behavior
