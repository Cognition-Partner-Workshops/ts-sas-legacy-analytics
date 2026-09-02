SELECT file, rows FROM sas_legacy.sas_bronze._manifest WHERE file IN ('LOAN_DETAILS.csv','CUST_ACCOUNTS.csv');
SELECT COUNT(*) AS loan_details_count FROM sas_legacy.sas_bronze.loan_details;
SELECT COUNT(*) AS cust_accounts_daily_count FROM sas_legacy.sas_silver.cust_accounts_daily WHERE snapshot_date=DATE'2024-01-31';
