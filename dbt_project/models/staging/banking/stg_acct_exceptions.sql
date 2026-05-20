-- stg_acct_exceptions.sql
-- Account data quality exceptions — replaces the exception routing logic
-- in load_customer_accounts.sas (lines 124-147).
--
-- Generates exception records for: NEG_BAL, HIGH_UTIL, NO_RISK.

with accounts as (

    select * from {{ ref('stg_cust_accounts') }}

),

demographics as (

    select * from {{ ref('stg_cust_demographics') }}

),

joined as (

    select
        a.account_id,
        a.customer_id,
        a.account_type,
        a.account_status,
        a.current_balance,
        a.credit_limit,
        a.last_activity_date,
        d.risk_rating

    from accounts as a
    inner join demographics as d
        on a.customer_id = d.customer_id
    where a.account_status not in ('W', 'C')
      and a.open_date <= current_date()

),

with_utilization as (

    select
        j.*,
        case
            when j.account_type in ('CC', 'LOC', 'HELC') and j.credit_limit > 0
                then (j.current_balance / j.credit_limit) * 100
            else null
        end as utilization_pct

    from joined as j

),

-- NEG_BAL: negative balance on deposit accounts (SAS: lines 124-130)
neg_bal as (

    select
        account_id,
        customer_id,
        'NEG_BAL' as exception_code,
        'Negative balance on deposit account ' || cast(account_id as string) as exception_desc,
        current_date() as snapshot_date

    from with_utilization
    where account_type in ('CHK', 'SAV', 'MMA', 'CD')
      and current_balance < 0

),

-- HIGH_UTIL: utilization > 95% (SAS: lines 133-139)
high_util as (

    select
        account_id,
        customer_id,
        'HIGH_UTIL' as exception_code,
        'Utilization at ' || cast(round(utilization_pct, 1) as string) || '% for account ' || cast(account_id as string) as exception_desc,
        current_date() as snapshot_date

    from with_utilization
    where utilization_pct > 95

),

-- NO_RISK: missing risk rating (SAS: lines 142-147)
no_risk as (

    select
        account_id,
        customer_id,
        'NO_RISK' as exception_code,
        'Missing risk rating for customer ' || cast(customer_id as string) as exception_desc,
        current_date() as snapshot_date

    from with_utilization
    where risk_rating is null

),

final as (

    select * from neg_bal
    union all
    select * from high_util
    union all
    select * from no_risk

)

select * from final
