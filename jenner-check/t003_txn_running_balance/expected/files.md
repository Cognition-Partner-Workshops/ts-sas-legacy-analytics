These URLs point to a specific Jenner run and expire when the run is reaped on the server. Re-running this bundle (./run_jenner.sh t003_txn_running_balance) regenerates them.

## Files

| Name | Type | Size (bytes) | URL |
|------|------|-------------|-----|
| listing.txt | text/plain | 2014 | [listing.txt](https://api.jenneranalytics.com/v1/run/r_019ed46071337201993994294e03c59e/files/listing.txt?token=132e95a09f7a445a8a4e3251f9b35dfc) |

## Datasets

| Name | Rows | Columns | Preview |
|------|------|---------|---------|
| cust_accounts_daily | 4 | ACCOUNT_ID, CURRENT_BALANCE | [preview](https://api.jenneranalytics.com/v1/run/r_019ed46071337201993994294e03c59e/datasets/cust_accounts_daily?token=132e95a09f7a445a8a4e3251f9b35dfc) |
| txn_enriched | 11 | transaction_id, account_id, transaction_type, transaction_amount, transaction_date, pre_txn_balance | [preview](https://api.jenneranalytics.com/v1/run/r_019ed46071337201993994294e03c59e/datasets/txn_enriched?token=132e95a09f7a445a8a4e3251f9b35dfc) |
| txn_feed | 15 | TRANSACTION_ID, ACCOUNT_ID, TRANSACTION_TYPE, TRANSACTION_AMOUNT, TRANSACTION_DATE | [preview](https://api.jenneranalytics.com/v1/run/r_019ed46071337201993994294e03c59e/datasets/txn_feed?token=132e95a09f7a445a8a4e3251f9b35dfc) |
| txn_rejected | 4 | TRANSACTION_ID, ACCOUNT_ID, TRANSACTION_TYPE, TRANSACTION_AMOUNT, TRANSACTION_DATE | [preview](https://api.jenneranalytics.com/v1/run/r_019ed46071337201993994294e03c59e/datasets/txn_rejected?token=132e95a09f7a445a8a4e3251f9b35dfc) |
| txn_validated | 11 | TRANSACTION_ID, ACCOUNT_ID, TRANSACTION_TYPE, TRANSACTION_AMOUNT, TRANSACTION_DATE | [preview](https://api.jenneranalytics.com/v1/run/r_019ed46071337201993994294e03c59e/datasets/txn_validated?token=132e95a09f7a445a8a4e3251f9b35dfc) |
| txn_with_balance | 11 | RUNNING_BALANCE, transaction_id, account_id, transaction_type, transaction_amount, transaction_date, pre_txn_balance | [preview](https://api.jenneranalytics.com/v1/run/r_019ed46071337201993994294e03c59e/datasets/txn_with_balance?token=132e95a09f7a445a8a4e3251f9b35dfc) |
