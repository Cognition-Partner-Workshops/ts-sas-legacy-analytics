{% docs banking_staging_overview %}

# Banking Staging Models — SAS Migration

## What is this?

This is the first migrated program from the SAS banking batch pipeline. It replaces
`Programs/Banking/load_customer_accounts.sas` — the foundational ETL that produces
the daily customer account snapshot.

## Original SAS Program

- **File**: `Programs/Banking/load_customer_accounts.sas`
- **Schedule**: Daily 06:00 via Control-M job `BANK_DAILY_01`
- **Orchestrator**: Step 1 of `BatchJobs/run_daily_banking.sas`

## How to Run

```bash
# Build just this model and its dependencies
dbt build --select stg_cust_accounts_daily

# Build the full staging layer including exceptions
dbt build --select +stg_cust_accounts_daily +stg_acct_exceptions

# Run seeds first (required on initial setup)
dbt seed --select banking
dbt build --select +stg_cust_accounts_daily
```

## Verification

After running the dbt model, compare output against the SAS table:

1. **Row counts**: Compare `SELECT COUNT(*) FROM stg_cust_accounts_daily` against
   the SAS observation count of `STG_BANK.CUST_ACCOUNTS_DAILY`

2. **Key metrics**: For a sample of accounts, compare:
   - `current_balance`
   - `utilization_pct`
   - `acct_age_months`
   - `days_inactive`
   - `dormancy_flag`

3. **Exception records**: Compare counts from `stg_acct_exceptions` against
   `STG_BANK.ACCT_EXCEPTIONS` by exception code

## Format Replacement Strategy

SAS `PROC FORMAT` catalogs are replaced by dbt seed CSV files:

| SAS Format | dbt Seed |
|-----------|----------|
| `$ACCTTYPE.` | `seed_account_type` |
| `$ACCTSTAT.` | `seed_account_status` |
| `RISKRATE.` | `seed_risk_rating` |
| `$CUSTSEG.` | `seed_customer_segment` |
| `$REGION.` | `seed_region` |

## What Comes Next

The migration sequence follows the dependency chain:

1. ✓ `load_customer_accounts.sas` → **this model** (stg_cust_accounts_daily)
2. `daily_transaction_processing.sas` → curated.daily_transactions (RETAIN/BY → window functions)
3. `credit_risk_scoring.sas` → curated.risk_scores (WOE scorecard → CASE WHEN bins)
4. `monthly_regulatory_reporting.sas` → reports.monthly_rwa (Basel III RWA + Excel export)

{% enddocs %}
