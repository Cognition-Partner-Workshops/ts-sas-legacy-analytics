-- U2 idempotency checksum: row count and SUM(hash(all target columns))
SELECT 'daily_transactions' AS tbl, COUNT(*) AS n,
       SUM(hash(transaction_id, account_id, transaction_date, transaction_type,
                transaction_amount, channel, merchant_category, description, post_date,
                currency_code)) AS checksum
FROM sas_legacy.sas_silver.daily_transactions
UNION ALL
SELECT 'running_balances', COUNT(*),
       SUM(hash(account_id, transaction_date, transaction_id, running_balance))
FROM sas_legacy.sas_silver.running_balances
WHERE transaction_date = DATE'2024-01-31'
UNION ALL
SELECT 'txn_anomalies', COUNT(*),
       SUM(hash(transaction_id, account_id, transaction_date, transaction_type,
                transaction_amount, channel, merchant_category, description, post_date,
                currency_code, account_type, customer_id, customer_segment, region_code,
                branch_id, pre_txn_balance, post_txn_balance, risk_rating, running_balance,
                avg_txn_amt, std_txn_amt, z_score, anomaly_type))
FROM sas_legacy.sas_silver.txn_anomalies
WHERE transaction_date = DATE'2024-01-31'
UNION ALL
SELECT 'txn_rejected', COUNT(*),
       SUM(hash(transaction_id, account_id, transaction_date, transaction_type,
                transaction_amount, channel, merchant_category, description, post_date,
                currency_code))
FROM sas_legacy.sas_silver.txn_rejected
