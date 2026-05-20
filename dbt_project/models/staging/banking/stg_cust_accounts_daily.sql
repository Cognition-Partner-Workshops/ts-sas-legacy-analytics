-- stg_cust_accounts_daily.sql
-- Daily Customer Account Snapshot — replaces load_customer_accounts.sas (Program #1)
--
-- Joins accounts + demographics + rates, applies business rules, and computes
-- derived metrics (utilization %, account age, dormancy/high-balance flags).
-- Mirrors SAS PROC SQL join (lines 34-69) and DATA step logic (lines 82-157).

{{ config(materialized='table') }}

with accounts as (

    select * from {{ ref('stg_cust_accounts') }}

),

demographics as (

    select * from {{ ref('stg_cust_demographics') }}

),

daily_rates as (

    select * from {{ ref('stg_daily_rates') }}

),

seed_account_type as (

    select * from {{ ref('seed_account_type') }}

),

seed_account_status as (

    select * from {{ ref('seed_account_status') }}

),

seed_risk_rating as (

    select * from {{ ref('seed_risk_rating') }}

),

seed_customer_segment as (

    select * from {{ ref('seed_customer_segment') }}

),

seed_region as (

    select * from {{ ref('seed_region') }}

),

-- Step 1: Join accounts + demographics (mirrors SAS PROC SQL, lines 34-69)
joined as (

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

    from accounts as a
    inner join demographics as d
        on a.customer_id = d.customer_id
    where a.account_status not in ('W', 'C')
      and a.open_date <= current_date()

),

-- Step 2: Derive metrics (mirrors SAS DATA step, lines 99-121)
with_metrics as (

    select
        j.*,

        -- Account age in months (SAS: intck('month', OPEN_DATE, run_date))
        datediff(month, j.open_date, current_date()) as acct_age_months,

        -- Days since last activity (SAS: run_date - LAST_ACTIVITY_DATE)
        datediff(day, j.last_activity_date, current_date()) as days_inactive,

        -- Utilization % for revolving accounts (SAS: lines 106-109)
        case
            when j.account_type in ('CC', 'LOC', 'HELC') and j.credit_limit > 0
                then (j.current_balance / j.credit_limit) * 100
            else null
        end as utilization_pct,

        -- Dormancy flag (SAS: lines 112-115)
        case
            when datediff(day, j.last_activity_date, current_date()) > 365
                 and j.account_status = 'A'
                then 'Y'
            else 'N'
        end as dormancy_flag,

        -- High-balance flag (SAS: lines 118-121)
        case
            when j.current_balance >= 250000 then 'Y'
            else 'N'
        end as high_balance_flag

    from joined as j

),

-- Step 3: Join seed lookup tables for formatted descriptions (SAS FORMAT assignments, lines 87-95)
final as (

    select
        m.account_id,
        m.customer_id,
        m.account_type,
        sat.description as account_type_desc,
        m.account_status,
        sas.description as account_status_desc,
        m.open_date,
        m.close_date,
        m.current_balance,
        m.available_balance,
        m.credit_limit,
        m.interest_rate,
        m.branch_id,
        m.officer_id,
        m.last_activity_date,
        m.first_name,
        m.last_name,
        m.ssn_hash,
        m.date_of_birth,
        m.customer_segment,
        scs.description as customer_segment_desc,
        m.risk_rating,
        srr.description as risk_rating_desc,
        m.region_code,
        sr.description as region_desc,
        m.primary_email,
        m.phone_number,
        m.acct_age_months,
        m.days_inactive,
        m.utilization_pct,
        m.dormancy_flag,
        m.high_balance_flag,
        current_date() as snapshot_date,
        current_timestamp() as load_timestamp

    from with_metrics as m
    left join seed_account_type as sat
        on m.account_type = sat.code
    left join seed_account_status as sas
        on m.account_status = sas.code
    left join seed_risk_rating as srr
        on m.risk_rating = srr.code
    left join seed_customer_segment as scs
        on m.customer_segment = scs.code
    left join seed_region as sr
        on m.region_code = sr.code

)

select * from final
order by customer_id, account_id
