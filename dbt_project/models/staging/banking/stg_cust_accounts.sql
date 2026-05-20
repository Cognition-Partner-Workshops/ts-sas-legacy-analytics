{{
  config(
    materialized='view'
  )
}}

/*
  stg_cust_accounts.sql
  Source: ORA_DW.CUST_ACCOUNTS (via Config/autoexec.sas Oracle connection)
  Purpose: Base staging of customer account master with column typing and renaming.
*/

select
    account_id,
    customer_id,
    upper(trim(account_type))   as account_type,
    upper(trim(account_status)) as account_status,
    cast(open_date as date)     as open_date,
    cast(close_date as date)    as close_date,
    cast(current_balance as decimal(18,2))   as current_balance,
    cast(available_balance as decimal(18,2)) as available_balance,
    cast(credit_limit as decimal(18,2))      as credit_limit,
    cast(interest_rate as decimal(8,6))      as interest_rate,
    branch_id,
    officer_id,
    cast(last_activity_date as date) as last_activity_date

from {{ source('oracle_dw', 'cust_accounts') }}
