-- stg_daily_rates.sql
-- Thin staging select from raw bank daily rates table.
-- Source: RAW_BANK.DAILY_RATES (load_customer_accounts.sas, line 7)

with source as (

    select * from {{ source('raw_bank', 'daily_rates') }}

),

renamed as (

    select * from source

)

select * from renamed
