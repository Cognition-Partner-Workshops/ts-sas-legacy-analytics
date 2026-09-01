# Migration Progress

`[FACT]` State: setup DONE; STOP A re-confirmed 2026-09-01 (this session). Inventory DONE (`docs/migration/ts-sas-legacy-analytics_estate_inventory.md`); STOP B APPROVED 2026-09-01 → active pipeline **P1 banking-core** (DEC-012). P1 analysis + plan DONE (`docs/migration/ts-sas-legacy-analytics_P1_banking_core_{analysis,plan}.md`); STOP C APPROVED 2026-09-01 (DEC-013/014). **Wave 0 in progress**: W0-A scaffolding child `devin-0a2bebe569e94d90b2015a2bad11dffd` (branch `migration/02-wave0-scaffolding`), W0-R independent reference child `devin-6c0ffc4d5f18462585dab7a141cfcc46` (branch `migration/02-wave0-reference`), launched 2026-09-01. Coverage 144 = 9 + 16 + 82 + 37; completeness UNVERIFIABLE.

| Pipeline | Setup | Inventory | Analysis | Convert | Recon | Cutover |
|---|---|---|---|---|---|---|
| `[FACT]` P1 shared-objects (wave 0) | DONE | DONE | DONE | NOT STARTED | NOT STARTED | NOT STARTED |
| `[FACT]` P1 banking / `load_customer_accounts` | DONE | DONE | DONE | NOT STARTED | NOT STARTED | NOT STARTED |
| `[FACT]` P1 banking / `daily_transaction_processing` | DONE | DONE | DONE | NOT STARTED | NOT STARTED | NOT STARTED |
| `[FACT]` P1 banking / `credit_risk_scoring` | DONE | DONE | DONE | NOT STARTED | NOT STARTED | NOT STARTED |
| `[FACT]` P1 banking / `monthly_regulatory_reporting` | DONE | DONE | DONE | NOT STARTED | NOT STARTED | NOT STARTED |
| `[FACT]` P1 banking / `run_daily_banking` (orchestrator) | DONE | DONE | DONE | NOT STARTED | NOT STARTED | NOT STARTED |
| `[PROPOSED]` P3 insurance / `claims_processing` | DONE | DONE | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED |
| `[PROPOSED]` P3 insurance / `policy_valuation` | DONE | DONE | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED |
| `[PROPOSED]` P2 reports / `customer_profitability` | DONE | DONE | NOT STARTED | NOT STARTED | NOT STARTED | NOT STARTED |

## Write targets registered

Register each target as `sas_legacy.<schema>.<table>` here before loading it; halt on collision.

| Target | Owner (wave/batch) | Registered |
|---|---|---|
| catalog `sas_legacy`; schemas `sas_bronze sas_silver sas_gold sas_ref sas_recon`; volume `sas_bronze.landing` | W0-A | 2026-09-01 |
| `sas_bronze.cust_accounts`, `cust_demographics`, `bureau_scores`, `payment_history`, `collateral`, `loan_details`, `daily_rates`, `txn_feed_20240131`, `daily_transactions_hist`, `_manifest` | W0-A | 2026-09-01 |
| `sas_ref.fmt_*` (9 banking formats), `sas_ref.fmt_registry` | W0-A | 2026-09-01 |
| `sas_recon.run_log` | W0-A | 2026-09-01 |
| `sas_silver.cust_accounts_daily`, `sas_silver.acct_exceptions` | W1 B1 (U1) | reserved |
| `sas_silver.daily_transactions`, `running_balances`, `txn_anomalies`, `txn_rejected` | W2 B2 (U2) | reserved |
| `sas_silver.risk_scores`, `risk_migration`; `sas_gold.risk_summary` | W2 B3 (U3) | reserved |
| `sas_gold.monthly_rwa`, `delinquency_aging`, `llp_coverage`, `capital_adequacy`; volume path `landing/reports/` | W2 B4 (U4) | reserved |
| `sas_silver.archive_batch_history`; job `sas_legacy_run_daily_banking` | W3 B5 (U5) | reserved |

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
