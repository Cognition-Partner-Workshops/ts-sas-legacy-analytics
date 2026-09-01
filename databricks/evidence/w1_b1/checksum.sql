-- idempotency checksum: all 28 non-load_timestamp columns (T-7), utilization_pct rounded 6dp
SELECT 'cust_accounts_daily' AS tbl, COUNT(*) AS n, COUNT(DISTINCT load_timestamp) AS n_ts,
       SUM(hash(account_id, customer_id, account_type, account_status, open_date, close_date,
                current_balance, available_balance, credit_limit, interest_rate, branch_id, officer_id,
                last_activity_date, first_name, last_name, ssn_hash, date_of_birth, customer_segment,
                risk_rating, region_code, primary_email, phone_number, acct_age_months, days_inactive,
                ROUND(utilization_pct, 6), dormancy_flag, high_balance_flag, snapshot_date)) AS checksum
FROM sas_legacy.sas_silver.cust_accounts_daily WHERE snapshot_date = DATE'2024-01-31'
UNION ALL
SELECT 'acct_exceptions', COUNT(*), COUNT(DISTINCT load_timestamp),
       SUM(hash(account_id, customer_id, account_type, account_status, open_date, close_date,
                current_balance, available_balance, credit_limit, interest_rate, branch_id, officer_id,
                last_activity_date, first_name, last_name, ssn_hash, date_of_birth, customer_segment,
                risk_rating, region_code, primary_email, phone_number, acct_age_months, days_inactive,
                ROUND(utilization_pct, 6), dormancy_flag, high_balance_flag, snapshot_date))
FROM sas_legacy.sas_silver.acct_exceptions
