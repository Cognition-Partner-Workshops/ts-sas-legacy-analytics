# Data Lineage & Flow Map

Visual representation of all data flows across the SAS estate, from source systems through processing layers to final outputs.

---

## High-Level Data Flow

```
 SOURCES                    STAGING                 CURATED/REPORTS            OUTPUTS
 ──────────────────────────────────────────────────────────────────────────────────────

 Oracle DW ──────┐
   CUST_ACCOUNTS │
   CUST_DEMOGRAPHICS        ┌──────────────────┐
   BUREAU_SCORES  ├────────►│ load_customer_   │──► STG_BANK.CUST_ACCOUNTS_DAILY ──┐
   PAYMENT_HISTORY│         │ accounts.sas     │──► STG_BANK.ACCT_EXCEPTIONS       │
   COLLATERAL    │         └──────────────────┘                                    │
   LOAN_DETAILS  │                                                                 │
   COST_OF_FUNDS ┘                                                                 │
                                                                                   │
 Flat Files ─────┐          ┌──────────────────┐                                   │
   TXN_FEED_     │          │ daily_transaction│                                   │
   YYYYMMDD      ├─────────►│ _processing.sas  │──► CURATED.DAILY_TRANSACTIONS ────┤
                  │         └──────────────────┘──► CURATED.TXN_ANOMALIES         │
                  │          ▲ reads from              CURATED.RUNNING_BALANCES     │
                  │          │ STG_BANK.CUST_                                       │
                  │          │ ACCOUNTS_DAILY                                       │
                  │                                                                 │
                  │          ┌──────────────────┐                                   │
                  │          │ credit_risk_     │                                   │
                  └─────────►│ scoring.sas      │──► CURATED.RISK_SCORES ──────────┤
                             └──────────────────┘──► CURATED.RISK_MIGRATION        │
                              ▲ reads from             REPORTS.RISK_SUMMARY         │
                              │ STG_BANK, ORA_DW                                   │
                                                                                   │
                             ┌──────────────────┐                                  │
                             │ monthly_         │                                  │
                             │ regulatory_      │──► REPORTS.MONTHLY_RWA           │
                             │ reporting.sas    │──► REPORTS.CAPITAL_ADEQUACY      │
                             └──────────────────┘──► REPORTS.DELINQUENCY_AGING ─►XLSX
                              ▲ reads from             REPORTS.LLP_COVERAGE        │
                              │ STG_BANK, ORA_DW                                   │
                                                                                   │
                             ┌──────────────────┐                                  │
                             │ customer_        │                                  │
                             │ profitability.sas│──► REPORTS.CUSTOMER_PNL          │
                             └──────────────────┘──► REPORTS.SEGMENT_PROFITABILITY─►XLSX
                              ▲ reads from             REPORTS.BRANCH_PROFITABILITY│
                              │ STG_BANK, CURATED,                                 │
                              │ ORA_DW                                             │

 Teradata DW ────┐          ┌──────────────────┐                                   │
   FRAUD_INDICATORS├────────►│ claims_          │                                   │
   ACTUARIAL_TABLES│        │ processing.sas   │──► STG_INS.CLAIMS_REGISTER       │
                   │        └──────────────────┘──► STG_INS.CLAIMS_REVIEW_QUEUE   │
 Flat Files ──────┤          ▲ reads from             STG_INS.FRAUD_ALERTS ──► EMAIL
   CLAIMS_FEED_   │          │ RAW_INS.POLICIES                                    │
   YYYYMMDD       ┘                                                                │
                                                                                   │
 RAW_INS ────────┐          ┌──────────────────┐                                   │
   POLICIES       │          │ policy_          │                                   │
   CLAIMS         ├─────────►│ valuation.sas    │──► STG_INS.POLICY_VALUATION     │
   PREMIUMS       │         └──────────────────┘──► REPORTS.LOSS_RATIO_SUMMARY    │
                  ┘          ▲ reads from             REPORTS.RESERVE_ADEQUACY     │
                             │ TERA_DW                                             │
                                                                                   │
 ◄── ARCHIVE.BATCH_HISTORY (batch control table, fed by both orchestrators) ──────┘
```

---

## Library Reference Map

### Source Libraries (Read-Only)

| Library | Path / Connection | Programs That Read |
|---------|-------------------|--------------------|
| `RAW` | `/data/sas/raw` | — |
| `RAW_BANK` | `/data/sas/raw/banking` | `load_customer_accounts`, `daily_transaction_processing` |
| `RAW_INS` | `/data/sas/raw/insurance` | `claims_processing`, `policy_valuation` |
| `ORA_DW` | Oracle `FINPROD.DW_BANKING` | `load_customer_accounts`, `credit_risk_scoring`, `monthly_regulatory_reporting`, `customer_profitability` |
| `TERA_DW` | Teradata `tdprod.internal.corp/ANALYTICS` | `claims_processing`, `policy_valuation` |

### Intermediate Libraries (Read-Write)

| Library | Path | Written By | Read By |
|---------|------|-----------|---------|
| `STG_BANK` | `/data/sas/staging/banking` | `load_customer_accounts` | `daily_transaction_processing`, `credit_risk_scoring`, `monthly_regulatory_reporting`, `customer_profitability` |
| `STG_INS` | `/data/sas/staging/insurance` | `claims_processing`, `policy_valuation` | — |
| `STAGING` | `/data/sas/staging` | — | — |

### Curated Libraries (Read-Write)

| Library | Path | Written By | Read By |
|---------|------|-----------|---------|
| `CURATED` | `/data/sas/curated` | `daily_transaction_processing`, `credit_risk_scoring` | `monthly_regulatory_reporting`, `customer_profitability`, `daily_transaction_processing` (90-day lookback) |
| `REPORTS` | `/data/sas/reports` | `credit_risk_scoring`, `monthly_regulatory_reporting`, `policy_valuation`, `customer_profitability` | — (terminal) |
| `ARCHIVE` | `/data/sas/archive` | Both batch orchestrators | — |

### Format Catalog Libraries

| Library | Path | Contents |
|---------|------|----------|
| `BANKING` | `/data/sas/formats/banking` | 9 custom formats |
| `INSURANCE` | `/data/sas/formats/insurance` | 5 custom formats |
| `COMMON` | `/data/sas/formats/common` | Referenced but not defined in repo |

---

## Dataset Dependency Graph

```
STEP 1: load_customer_accounts
  ORA_DW.CUST_ACCOUNTS ──┐
  ORA_DW.CUST_DEMOGRAPHICS──► STG_BANK.CUST_ACCOUNTS_DAILY
                              STG_BANK.ACCT_EXCEPTIONS

STEP 2: daily_transaction_processing
  RAW_BANK.TXN_FEED_* ──────┐
  STG_BANK.CUST_ACCOUNTS_DAILY──► CURATED.DAILY_TRANSACTIONS
  CURATED.DAILY_TRANSACTIONS ──►  CURATED.TXN_ANOMALIES
    (90-day lookback for stats)    CURATED.RUNNING_BALANCES

STEP 3: credit_risk_scoring
  STG_BANK.CUST_ACCOUNTS_DAILY──┐
  ORA_DW.BUREAU_SCORES ──────────► CURATED.RISK_SCORES
  ORA_DW.PAYMENT_HISTORY ────────► CURATED.RISK_MIGRATION
  ORA_DW.COLLATERAL ──────────────► REPORTS.RISK_SUMMARY

STEP 4: monthly_regulatory_reporting
  STG_BANK.CUST_ACCOUNTS_DAILY──┐
  ORA_DW.LOAN_DETAILS ──────────► REPORTS.MONTHLY_RWA
  ORA_DW.COLLATERAL ─────────────► REPORTS.CAPITAL_ADEQUACY
  CURATED.DAILY_TRANSACTIONS ────► REPORTS.DELINQUENCY_AGING
                                   REPORTS.LLP_COVERAGE
                                   REG_REPORT_*.xlsx

INSURANCE STEP 1: claims_processing
  RAW_INS.CLAIMS_FEED_* ────┐
  RAW_INS.POLICIES ──────────► STG_INS.CLAIMS_REGISTER
  TERA_DW.FRAUD_INDICATORS ──► STG_INS.CLAIMS_REVIEW_QUEUE
                                STG_INS.FRAUD_ALERTS

INSURANCE STEP 2: policy_valuation
  RAW_INS.POLICIES ──────┐
  RAW_INS.CLAIMS ─────────► STG_INS.POLICY_VALUATION
  RAW_INS.PREMIUMS ────────► REPORTS.LOSS_RATIO_SUMMARY
  TERA_DW.ACTUARIAL_TABLES─► REPORTS.RESERVE_ADEQUACY

MONTHLY: customer_profitability
  STG_BANK.CUST_ACCOUNTS_DAILY──┐
  CURATED.DAILY_TRANSACTIONS ─────► REPORTS.CUSTOMER_PNL
  CURATED.RISK_SCORES ────────────► REPORTS.SEGMENT_PROFITABILITY
  ORA_DW.COST_OF_FUNDS ──────────► REPORTS.BRANCH_PROFITABILITY
                                    PROFITABILITY_*.xlsx
```

---

## Oracle DW Tables Referenced

| Table | Columns Used | Programs |
|-------|-------------|----------|
| `CUST_ACCOUNTS` | ACCOUNT_ID, CUSTOMER_ID, ACCOUNT_TYPE, ACCOUNT_STATUS, OPEN_DATE, CLOSE_DATE, CURRENT_BALANCE, AVAILABLE_BALANCE, CREDIT_LIMIT, INTEREST_RATE, BRANCH_ID, OFFICER_ID, LAST_ACTIVITY_DATE | `load_customer_accounts` |
| `CUST_DEMOGRAPHICS` | CUSTOMER_ID, FIRST_NAME, LAST_NAME, SSN_HASH, DATE_OF_BIRTH, CUSTOMER_SEGMENT, RISK_RATING, REGION_CODE, PRIMARY_EMAIL, PHONE_NUMBER | `load_customer_accounts` |
| `BUREAU_SCORES` | CUSTOMER_ID, SCORE_DATE, FICO_SCORE, VANTAGE_SCORE, BUREAU_INQS_6MO, BUREAU_TRADES_OPEN, BUREAU_DEROGS, BUREAU_UTIL_PCT, BUREAU_OLDEST_TRADE_MO | `credit_risk_scoring` |
| `PAYMENT_HISTORY` | ACCOUNT_ID, PMT_ONTIME_12MO, PMT_LATE_30_12MO, PMT_LATE_60_12MO, PMT_LATE_90_12MO, MAX_DAYS_PAST_DUE_EVER, MONTHS_SINCE_LAST_DPD, AVG_PMT_RATIO_12MO | `credit_risk_scoring` |
| `COLLATERAL` | ACCOUNT_ID, COLLATERAL_VALUE, LAST_APPRAISAL_DATE | `credit_risk_scoring`, `monthly_regulatory_reporting` |
| `LOAN_DETAILS` | ACCOUNT_ID, LTV, DAYS_PAST_DUE, PAST_DUE_AMOUNT, ALLOWANCE_AMT | `monthly_regulatory_reporting` |
| `COST_OF_FUNDS` | (referenced but columns not specified in code) | `customer_profitability` |

## Teradata Tables Referenced

| Table | Columns Used | Programs |
|-------|-------------|----------|
| `FRAUD_INDICATORS` | POLICY_ID, CLAIMANT_ID, FRAUD_SCORE, INDICATOR_FLAGS | `claims_processing` |
| `ACTUARIAL_TABLES` | (referenced but columns not specified in code) | `policy_valuation` |
