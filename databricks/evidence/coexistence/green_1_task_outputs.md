## recon_U1

```text
# recon U1 2024-01-31 — PASS
mode: DEGRADED (reference-derived, not SAS-produced); tolerances v1; run_id 7f33000b-7e03-4ea0-9d06-9df13b53cf6d
reference manifest sha256: aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7

| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | failing rules |
|---|---|---|---|---|---|---|---|---|
| cust_accounts_daily | row_level | 466 | 466 | 40 | 0 | 2 | 0 | - |
| acct_exceptions | row_level | 32 | 32 | 12 | 0 | 2 | 1 | - |

warehouse statements: 6, elapsed_s: 3.4

```

## recon_U2

```text
# recon U2 2024-01-31 — PASS
mode: DEGRADED (reference-derived, not SAS-produced); tolerances v1; run_id e0c75fc7-039f-4590-bc9b-694ac2dce047
reference manifest sha256: aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7

| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | failing rules |
|---|---|---|---|---|---|---|---|---|
| daily_transactions | row_level | 18903 | 18903 | 15 | 0 | 2 | 0 | - |
| running_balances | row_level | 610 | 610 | 8 | 0 | 2 | 0 | - |
| txn_anomalies | row_level | 46 | 46 | 35 | 0 | 2 | 0 | - |
| txn_rejected | row_level | 12 | 12 | 6 | 0 | 2 | 1 | - |

warehouse statements: 12, elapsed_s: 6.5

```

## recon_U3

```text
# recon U3 2024-01-31 — FAIL
mode: DEGRADED (reference-derived, not SAS-produced); tolerances v1; run_id 9b38bd0c-301f-415b-8f47-f423f0057abc
reference manifest sha256: aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7

| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | failing rules |
|---|---|---|---|---|---|---|---|---|
| risk_scores | row_level | 236 | 236 | 64 | 1 | 4 | 0 | T-3:model_id |
| risk_migration | row_level | 195 | 195 | 15 | 0 | 4 | 0 | - |
| risk_summary | row_level | 12 | 12 | 16 | 0 | 2 | 0 | - |

warehouse statements: 9, elapsed_s: 7.6



/databricks/python/lib/python3.11/site-packages/IPython/core/interactiveshell.py:3585: UserWarning: To exit: use 'exit', 'quit', or Ctrl-D.
  warn("To exit: use 'exit', 'quit', or Ctrl-D.", stacklevel=1)
```

## recon_U4

```text
# recon U4 2024-01-31 — PASS
mode: DEGRADED (reference-derived, not SAS-produced); tolerances v1; run_id 4c56379a-9004-430f-a21a-d2d0e4f66c14
reference manifest sha256: aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7
xlsx: /Volumes/sas_legacy/sas_bronze/landing/reports/REG_REPORT_202401.xlsx sha256=850d6d21a24f963fe65a1b88f8b5422fed9a7b55d5aa977aef12b5311e2d4e86

| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | failing rules |
|---|---|---|---|---|---|---|---|---|
| monthly_rwa | row_level | 59 | 59 | 16 | 0 | 1 | 0 | - |
| delinquency_aging | row_level | 70 | 70 | 14 | 0 | 2 | 0 | - |
| llp_coverage | row_level | 6 | 6 | 18 | 0 | 2 | 0 | - |
| capital_adequacy | row_level | 1 | 1 | 22 | 0 | 2 | 0 | - |

warehouse statements: 12, elapsed_s: 6.2

```

## recon_U5

```text
# recon U5 2024-01-31 — PASS
mode: DEGRADED (reference-derived, not SAS-produced); tolerances v1; run_id 0a73f95c-1978-4fd4-bd9e-2267f5884a48
reference manifest sha256: aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7

| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | failing rules |
|---|---|---|---|---|---|---|---|---|
| archive_batch_history | row_level | 4 | 4 | 13 | 0 | 2 | 0 | - |

warehouse statements: 3, elapsed_s: 1.6

```

