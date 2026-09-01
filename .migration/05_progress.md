# Migration Progress

`[FACT]` State: setup complete; awaiting STOP A. No downstream phase starts before STOP A.

| Pipeline | Setup | Inventory | Analysis | Convert | Recon | Cutover |
|---|---|---|---|---|---|---|
| `[PROPOSED]` shared-objects (wave 0) | DONE | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED |
| `[PROPOSED]` banking / `load_customer_accounts` | DONE | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED |
| `[PROPOSED]` banking / `daily_transaction_processing` | DONE | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED |
| `[PROPOSED]` banking / `credit_risk_scoring` | DONE | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED |
| `[PROPOSED]` banking / `monthly_regulatory_reporting` | DONE | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED |
| `[PROPOSED]` insurance / `claims_processing` | DONE | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED |
| `[PROPOSED]` insurance / `policy_valuation` | DONE | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED |
| `[PROPOSED]` reports / `customer_profitability` | DONE | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED |

## Write targets registered

`[PROPOSED]` Empty. Child sessions must register each target as `sas_legacy.<schema>.<table>` here before loading it.

## Baseline manifest

`[DISCOVERED]` Banking seed snapshots, business date 31JAN2024 (`Data/README.md`). Insurance: none. Curated `DAILY_TRANSACTIONS.csv` is a 90-day history *input* (pre-existing CURATED state), not a legacy output.

| Filename | Data rows (wc -l minus 1) | SHA-256 |
|---|---:|---|
| `Data/csv/curated/DAILY_TRANSACTIONS.csv` | 18293 | `f31519447f5e2df2be283dc8dcf7c46e1fd3175ac235205abd97418739cbdbe5` |
| `Data/csv/oracle_dw/BUREAU_SCORES.csv` | 500 | `989f8077cc84b3dfe3daf2a6fc5f5a995d49cd8e4a911831b4f3f6e9ffe5025c` |
| `Data/csv/oracle_dw/COLLATERAL.csv` | 114 | `fbdc1cf8b38d43e18c26a2e34b70616a19cf0637be1447f95a7d49f6b6b9bb6b` |
| `Data/csv/oracle_dw/CUST_ACCOUNTS.csv` | 487 | `30d762718cc7f15d7659f6734df28dbaf36532ebf5323a422ffeed49068c8b13` |
| `Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv` | 250 | `2050f727d3065926b7b3b047f6967150f16488d1acdfc20d384133b01019182b` |
| `Data/csv/oracle_dw/LOAN_DETAILS.csv` | 248 | `0eba231eb28d31ea2e4df7e0ee61e5b37f7e74fbcee5f6968627d0207730a1f7` |
| `Data/csv/oracle_dw/PAYMENT_HISTORY.csv` | 248 | `f745b79820420ca2ac870ae14992dde704d24e2e1e7942aebedd896f66c9f396` |
| `Data/csv/raw_bank/DAILY_RATES.csv` | 455 | `d61d8a5310a9c40530c07ef73bfed9b3e748a5a59fcc0a34581b7303b5490d6a` |
| `Data/csv/raw_bank/TXN_FEED_20240131.csv` | 622 | `0bebabbc3e4a8a4e799d51afccb2e0e1388bbce9b72ebc056b241f131c8e82b6` |

| Status | Current repository commit |
|---|---|
| `[DISCOVERED]` | `2c985b279f9127e805d38645c3d8faa7689fbe99` (branch migration/00-setup; Data/ unchanged since main) |

## Circuit breaker

`[PROPOSED]` Halt the wave after 3 failures of the same class.
