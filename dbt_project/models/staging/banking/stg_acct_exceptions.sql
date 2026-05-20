{{
  config(
    materialized='table',
    description='Account data quality exceptions — replaces exception routing in load_customer_accounts.sas'
  )
}}

/*
  stg_acct_exceptions.sql
  Replaces: The exception-output branch of the DATA step in
            Programs/Banking/load_customer_accounts.sas (lines 124-147)
  
  In the SAS program, the multi-output DATA step routes records to
  WORK.ACCT_EXCEPTIONS when business rule violations are detected.
  This model replicates those exception conditions as a filtered view
  of the same joined data.
  
  Exception rules:
    1. NEG_BAL   — Negative balance on deposit accounts (CHK, SAV, MMA, CD)
    2. HIGH_UTIL — Credit utilization > 95% on revolving accounts
    3. NO_RISK   — Missing risk rating
*/

with account_base as (

    select
        a.account_id,
        a.customer_id,
        a.account_type,
        a.account_status,
        a.current_balance,
        a.credit_limit,
        d.risk_rating,
        d.region_code,
        d.customer_segment,
        case
            when a.account_type in ('CC', 'LOC', 'HELC') and a.credit_limit > 0
                then (a.current_balance / a.credit_limit) * 100
            else null
        end as utilization_pct,
        {{ var('snapshot_date') }} as snapshot_date,
        current_timestamp() as load_timestamp

    from {{ ref('stg_cust_accounts') }} a
    inner join {{ ref('stg_cust_demographics') }} d
        on a.customer_id = d.customer_id
    where a.account_status not in ('W', 'C')
      and a.open_date <= {{ var('snapshot_date') }}

),

-- Rule 1: Negative balance on deposit accounts (SAS lines 124-130)
neg_balance_exceptions as (

    select
        account_id,
        customer_id,
        account_type,
        'NEG_BAL' as exception_code,
        concat('Negative balance ', cast(current_balance as string),
               ' on deposit account ', account_id) as exception_desc,
        snapshot_date,
        load_timestamp
    from account_base
    where account_type in ('CHK', 'SAV', 'MMA', 'CD')
      and current_balance < 0

),

-- Rule 2: Credit utilization > 95% (SAS lines 133-139)
high_util_exceptions as (

    select
        account_id,
        customer_id,
        account_type,
        'HIGH_UTIL' as exception_code,
        concat('Utilization at ', cast(round(utilization_pct, 1) as string),
               '% for account ', account_id) as exception_desc,
        snapshot_date,
        load_timestamp
    from account_base
    where utilization_pct > 95

),

-- Rule 3: Missing risk rating (SAS lines 142-147)
no_risk_exceptions as (

    select
        account_id,
        customer_id,
        account_type,
        'NO_RISK' as exception_code,
        concat('Missing risk rating for customer ', customer_id) as exception_desc,
        snapshot_date,
        load_timestamp
    from account_base
    where risk_rating is null

)

select * from neg_balance_exceptions
union all
select * from high_util_exceptions
union all
select * from no_risk_exceptions
