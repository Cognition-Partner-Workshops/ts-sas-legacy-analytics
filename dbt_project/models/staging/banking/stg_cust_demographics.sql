{{
  config(
    materialized='view'
  )
}}

/*
  stg_cust_demographics.sql
  Source: ORA_DW.CUST_DEMOGRAPHICS (via Config/autoexec.sas Oracle connection)
  Purpose: Base staging of customer demographic attributes.
*/

select
    customer_id,
    first_name,
    last_name,
    ssn_hash,
    cast(date_of_birth as date)       as date_of_birth,
    upper(trim(customer_segment))     as customer_segment,
    cast(risk_rating as int)          as risk_rating,
    upper(trim(region_code))          as region_code,
    primary_email,
    phone_number

from {{ source('oracle_dw', 'cust_demographics') }}
