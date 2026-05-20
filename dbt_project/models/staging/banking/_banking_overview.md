{% docs banking_staging_overview %}

## Banking Staging Models — Migration Overview

This directory contains the first wave of dbt staging models migrated from the
legacy SAS ETL estate. These models replace **`load_customer_accounts.sas`**
(Program #1), the foundational daily account snapshot pipeline that all
downstream banking programs depend on.

### What was migrated

| SAS Artifact | dbt Model | Purpose |
|---|---|---|
| `ORA_DW.CUST_ACCOUNTS` extract | `stg_cust_accounts` | Thin select / rename from source |
| `ORA_DW.CUST_DEMOGRAPHICS` extract | `stg_cust_demographics` | Thin select / rename from source |
| `RAW_BANK.DAILY_RATES` extract | `stg_daily_rates` | Thin select from source |
| `STG_BANK.CUST_ACCOUNTS_DAILY` | `stg_cust_accounts_daily` | Main daily snapshot with derived metrics |
| `STG_BANK.ACCT_EXCEPTIONS` | `stg_acct_exceptions` | Data quality exception records |

### How to verify

1. **Row count parity** — Compare `select count(*) from stg_cust_accounts_daily`
   against the SAS log entry `Records loaded: &nobs_out` for the same run date.
2. **Sample value checks** — Pick 5–10 account IDs and compare key derived fields
   (`acct_age_months`, `utilization_pct`, `dormancy_flag`, `high_balance_flag`)
   between the SAS output and the dbt model.
3. **Exception counts** — Compare `select count(*) from stg_acct_exceptions`
   against the SAS log entry `Exceptions: &nobs_except`.
4. **Schema tests** — Run `dbt test --select staging.banking` to validate
   not-null, unique, and accepted-values constraints.

### What comes next

- **Program #2–5**: Transaction processing, credit risk scoring, regulatory
  reporting, and customer profitability models will be migrated in subsequent
  waves, building on the account base established here.
- **Seed data**: Lookup tables (`seed_account_type`, `seed_account_status`,
  `seed_risk_rating`, `seed_customer_segment`, `seed_region`) will be populated
  with CSV files matching the SAS PROC FORMAT definitions.
- **Intermediate / Curated layers**: Business logic currently embedded in
  downstream SAS programs will be refactored into the `curated/` layer.

{% enddocs %}
