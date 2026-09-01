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

`[PROPOSED]` Empty. Child sessions must register each target as `ow_tp.<schema>.<table>` here before loading it.

## Baseline manifest

`[DISCOVERED]` `Data/csv/` exists but currently contains no `*.csv` files, so there are no file rows to record. The intended banking layout is documented in `Data/README.md:15-35`; the manifest must be repopulated if the seed files are restored.

| Filename | Data rows (wc -l minus 1) | SHA-256 |
|---|---:|---|
| `[DISCOVERED]` None present | n/a | n/a |

| Status | Current repository commit |
|---|---|
| `[DISCOVERED]` | `1aa30f77a68bf810cdbaf6c4b1eb4610a5792945` |

## Circuit breaker

`[PROPOSED]` Halt the wave after 3 failures of the same class.
