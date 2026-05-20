{{
  config(
    materialized='table',
    description='Daily customer account snapshot — replaces SAS load_customer_accounts.sas'
  )
}}

/*
  stg_cust_accounts_daily.sql
  Replaces: Programs/Banking/load_customer_accounts.sas
  
  This model replicates the full logic of the SAS program:
    Step 1: PROC SQL join of ORA_DW.CUST_ACCOUNTS + ORA_DW.CUST_DEMOGRAPHICS
            (filtering out Written-Off and Closed accounts)
    Step 2: DATA step deriving metrics (utilization, dormancy, account age, etc.)
            and applying format labels via seed table joins
  
  The SAS program outputs to STG_BANK.CUST_ACCOUNTS_DAILY.
  Exception records are routed to a separate model (stg_acct_exceptions.sql).
*/

with accounts as (

    select * from {{ ref('stg_cust_accounts') }}

),

demographics as (

    select * from {{ ref('stg_cust_demographics') }}

),

daily_rates as (

    select * from {{ ref('stg_daily_rates') }}

),

-- Replicate SAS PROC SQL join (load_customer_accounts.sas lines 34-69)
-- Filters: account_status not in ('W','C') and open_date <= run_date
account_base as (

    select
        a.account_id,
        a.customer_id,
        a.account_type,
        a.account_status,
        a.open_date,
        a.close_date,
        a.current_balance,
        a.available_balance,
        a.credit_limit,
        a.interest_rate,
        a.branch_id,
        a.officer_id,
        a.last_activity_date,
        d.first_name,
        d.last_name,
        d.ssn_hash,
        d.date_of_birth,
        d.customer_segment,
        d.risk_rating,
        d.region_code,
        d.primary_email,
        d.phone_number

    from accounts a
    inner join demographics d
        on a.customer_id = d.customer_id
    where a.account_status not in ('W', 'C')
      and a.open_date <= current_date()

),

-- Replicate SAS DATA step derived metrics (lines 99-121)
with_derived_metrics as (

    select
        *,

        -- Account age in months (SAS: intck('month', OPEN_DATE, "&run_date"d))
        months_between(current_date(), open_date) as acct_age_months,

        -- Days since last activity (SAS: "&run_date"d - LAST_ACTIVITY_DATE)
        datediff(current_date(), last_activity_date) as days_inactive,

        -- Utilization ratio for revolving accounts (SAS lines 106-109)
        case
            when account_type in ('CC', 'LOC', 'HELC') and credit_limit > 0
                then (current_balance / credit_limit) * 100
            else null
        end as utilization_pct,

        -- Dormancy flag (SAS lines 112-115)
        case
            when datediff(current_date(), last_activity_date) > 365
                 and account_status = 'A'
                then 'Y'
            else 'N'
        end as dormancy_flag,

        -- High-balance flag (SAS lines 118-121)
        case
            when current_balance >= 250000 then 'Y'
            else 'N'
        end as high_balance_flag,

        -- Snapshot metadata (SAS lines 150-152)
        current_date() as snapshot_date,
        current_timestamp() as load_timestamp

    from account_base

),

-- Join seed lookup tables to replace SAS PROC FORMAT display labels
with_labels as (

    select
        m.*,
        at.description as account_type_desc,
        ast.description as account_status_desc,
        rr.description as risk_rating_desc,
        cs.description as customer_segment_desc,
        rg.description as region_desc

    from with_derived_metrics m
    left join {{ ref('seed_account_type') }} at
        on m.account_type = at.code
    left join {{ ref('seed_account_status') }} ast
        on m.account_status = ast.code
    left join {{ ref('seed_risk_rating') }} rr
        on m.risk_rating = rr.rating_code
    left join {{ ref('seed_customer_segment') }} cs
        on m.customer_segment = cs.code
    left join {{ ref('seed_region') }} rg
        on m.region_code = rg.code

)

select * from with_labels
