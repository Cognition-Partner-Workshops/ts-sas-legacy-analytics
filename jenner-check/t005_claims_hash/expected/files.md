These URLs point to a specific Jenner run and expire when the run is reaped on the server. Re-running this bundle (./run_jenner.sh t005_claims_hash) regenerates them.

## Files

| Name | Type | Size (bytes) | URL |
|------|------|-------------|-----|
| listing.txt | text/plain | 694 | [listing.txt](https://api.jenneranalytics.com/v1/run/r_019ed46301747bd0b3d4b1eb8fcd358b/files/listing.txt?token=a764fc2fc8c14e1d9f764d47162288e9) |

## Datasets

| Name | Rows | Columns | Preview |
|------|------|---------|---------|
| claims_feed | 7 | CLAIM_ID, POLICY_ID, CLAIMANT_ID, LOSS_DATE, CLAIMED_AMOUNT | [preview](https://api.jenneranalytics.com/v1/run/r_019ed46301747bd0b3d4b1eb8fcd358b/datasets/claims_feed?token=a764fc2fc8c14e1d9f764d47162288e9) |
| claims_invalid | 4 | POLICY_TYPE, SUM_INSURED, DEDUCTIBLE, CLAIM_ID, POLICY_ID, CLAIMANT_ID, LOSS_DATE, CLAIMED_AMOUNT, effective_date, expiration_date | [preview](https://api.jenneranalytics.com/v1/run/r_019ed46301747bd0b3d4b1eb8fcd358b/datasets/claims_invalid?token=a764fc2fc8c14e1d9f764d47162288e9) |
| claims_valid | 3 | POLICY_TYPE, SUM_INSURED, DEDUCTIBLE, CLAIM_ID, POLICY_ID, CLAIMANT_ID, LOSS_DATE, CLAIMED_AMOUNT, effective_date, expiration_date | [preview](https://api.jenneranalytics.com/v1/run/r_019ed46301747bd0b3d4b1eb8fcd358b/datasets/claims_valid?token=a764fc2fc8c14e1d9f764d47162288e9) |
| policies | 6 | POLICY_ID, POLICY_TYPE, STATUS, EFFECTIVE_DATE, EXPIRATION_DATE, SUM_INSURED, DEDUCTIBLE | [preview](https://api.jenneranalytics.com/v1/run/r_019ed46301747bd0b3d4b1eb8fcd358b/datasets/policies?token=a764fc2fc8c14e1d9f764d47162288e9) |
