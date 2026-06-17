These URLs point to a specific Jenner run and expire when the run is reaped on the server. Re-running this bundle (./run_jenner.sh t007_customer_profitability) regenerates them.

## Files

| Name | Type | Size (bytes) | URL |
|------|------|-------------|-----|
| listing.txt | text/plain | 1986 | [listing.txt](https://api.jenneranalytics.com/v1/run/r_019ed47ca320751192d32a9ddac1c251/files/listing.txt?token=53f7403835d24531adfe0f3aa94a310b) |

## Datasets

| Name | Rows | Columns | Preview |
|------|------|---------|---------|
| cust_accounts_daily | 8 | CUSTOMER_ID, ACCOUNT_ID, ACCOUNT_TYPE, CUSTOMER_SEGMENT, REGION_CODE, BRANCH_ID, CURRENT_BALANCE, INTEREST_RATE | [preview](https://api.jenneranalytics.com/v1/run/r_019ed47ca320751192d32a9ddac1c251/datasets/cust_accounts_daily?token=53f7403835d24531adfe0f3aa94a310b) |
| customer_pnl | 5 | PROFIT_TIER, CUSTOMER_ID, CUSTOMER_SEGMENT, REGION_CODE, BRANCH_ID, LENDING_INCOME, DEPOSIT_COST, NET_INTEREST_INCOME, NUM_ACCOUNTS, TOTAL_RELATIONSHIP, FEE_INCOME, INT_CREDITED, TXN_VOLUME, TOTAL_ECL, OPERATING_COST, TOTAL_REVENUE, NET_PROFIT, ROA, REPORT_MONTH | [preview](https://api.jenneranalytics.com/v1/run/r_019ed47ca320751192d32a9ddac1c251/datasets/customer_pnl?token=53f7403835d24531adfe0f3aa94a310b) |
| ecl | 4 | CUSTOMER_ID, TOTAL_ECL | [preview](https://api.jenneranalytics.com/v1/run/r_019ed47ca320751192d32a9ddac1c251/datasets/ecl?token=53f7403835d24531adfe0f3aa94a310b) |
| fee_income | 4 | CUSTOMER_ID, FEE_INCOME, INT_CREDITED, TXN_VOLUME | [preview](https://api.jenneranalytics.com/v1/run/r_019ed47ca320751192d32a9ddac1c251/datasets/fee_income?token=53f7403835d24531adfe0f3aa94a310b) |
| interest_income | 5 | CUSTOMER_ID, CUSTOMER_SEGMENT, REGION_CODE, BRANCH_ID, LENDING_INCOME, DEPOSIT_COST, NET_INTEREST_INCOME, NUM_ACCOUNTS, TOTAL_RELATIONSHIP | [preview](https://api.jenneranalytics.com/v1/run/r_019ed47ca320751192d32a9ddac1c251/datasets/interest_income?token=53f7403835d24531adfe0f3aa94a310b) |
| segment_profitability | 5 | CUSTOMER_SEGMENT, N_CUSTOMERS, TOTAL_REVENUE, OPERATING_COST, TOTAL_ECL, NET_PROFIT, TOTAL_RELATIONSHIP, AVG_PROFIT_PER_CUSTOMER | [preview](https://api.jenneranalytics.com/v1/run/r_019ed47ca320751192d32a9ddac1c251/datasets/segment_profitability?token=53f7403835d24531adfe0f3aa94a310b) |
