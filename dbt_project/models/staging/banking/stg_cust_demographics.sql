-- stg_cust_demographics.sql
-- Thin staging select from Oracle DW customer demographics table.
-- Source: ORA_DW.CUST_DEMOGRAPHICS (load_customer_accounts.sas, lines 50-58)

with source as (

    select * from {{ source('oracle_dw', 'cust_demographics') }}

),

renamed as (

    select
        customer_id,
        first_name,
        last_name,
        ssn_hash,
        date_of_birth,
        customer_segment,
        risk_rating,
        region_code,
        primary_email,
        phone_number

    from source

)

select * from renamed
