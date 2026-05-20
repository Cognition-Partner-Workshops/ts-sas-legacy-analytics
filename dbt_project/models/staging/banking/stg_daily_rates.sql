{{
  config(
    materialized='view'
  )
}}

/*
  stg_daily_rates.sql
  Source: RAW_BANK.DAILY_RATES (file feed landing zone)
  Purpose: Base staging of daily interest rate reference data.
*/

select
    cast(rate_date as date)          as rate_date,
    rate_type,
    cast(rate_value as decimal(8,6)) as rate_value,
    currency_code,
    term_months

from {{ source('raw_bank', 'daily_rates') }}
