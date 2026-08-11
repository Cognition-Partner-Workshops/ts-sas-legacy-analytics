These URLs point to a specific Jenner run and expire when the run is reaped on the server. Re-running this bundle (./run_jenner.sh t002_credit_risk_scoring) regenerates them.

## Files

| Name | Type | Size (bytes) | URL |
|------|------|-------------|-----|
| listing.txt | text/plain | 2261 | [listing.txt](https://api.jenneranalytics.com/v1/run/r_019ed45ed7a47a70b79c63dce54f12ed/files/listing.txt?token=a4835648e9e34ab9b944bcbf1971bbbf) |

## Datasets

| Name | Rows | Columns | Preview |
|------|------|---------|---------|
| risk_summary | 9 | ACCOUNT_TYPE, NEW_RISK_RATING, N_ACCOUNTS, AVG_PD, AVG_LGD, TOTAL_EAD, TOTAL_EL | [preview](https://api.jenneranalytics.com/v1/run/r_019ed45ed7a47a70b79c63dce54f12ed/datasets/risk_summary?token=a4835648e9e34ab9b944bcbf1971bbbf) |
| score_input | 10 | ACCOUNT_ID, CUSTOMER_ID, ACCOUNT_TYPE, CUSTOMER_SEGMENT, REGION_CODE, CURRENT_BALANCE, CREDIT_LIMIT, ACCT_AGE_MONTHS, UTILIZATION_PCT, FICO_SCORE, PMT_LATE_90_12MO, LTV | [preview](https://api.jenneranalytics.com/v1/run/r_019ed45ed7a47a70b79c63dce54f12ed/datasets/score_input?token=a4835648e9e34ab9b944bcbf1971bbbf) |
| scored | 10 | ACCOUNT_ID, CUSTOMER_ID, ACCOUNT_TYPE, CUSTOMER_SEGMENT, REGION_CODE, CURRENT_BALANCE, CREDIT_LIMIT, ACCT_AGE_MONTHS, UTILIZATION_PCT, FICO_SCORE, PMT_LATE_90_12MO, LTV, PD, LGD, EAD, EXPECTED_LOSS, NEW_RISK_RATING | [preview](https://api.jenneranalytics.com/v1/run/r_019ed45ed7a47a70b79c63dce54f12ed/datasets/scored?token=a4835648e9e34ab9b944bcbf1971bbbf) |
