-- stg_cust_accounts.sql
-- Thin staging select from Oracle DW customer accounts table.
-- Source: ORA_DW.CUST_ACCOUNTS (load_customer_accounts.sas, lines 34-69)

with source as (

    select * from {{ source('oracle_dw', 'cust_accounts') }}

),

renamed as (

    select
        account_id,
        customer_id,
        account_type,
        account_status,
        open_date,
        close_date,
        current_balance,
        available_balance,
        credit_limit,
        interest_rate,
        branch_id,
        officer_id,
        last_activity_date

    from source

)

select * from renamed
