## recon_U3

```text
recon output dir: /tmp/sas_legacy_recon_U3_s4ueue12
# recon U3 2024-02-29 — FAIL
mode: DEGRADED (reference-derived, not SAS-produced); tolerances v1; run_id cf33434f-7de1-4b2a-a5af-b0f16d80a7fa
reference manifest sha256: aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7

| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | failing rules |
|---|---|---|---|---|---|---|---|---|
| risk_scores | row_level | 236 | 236 | 64 | 1 | 4 | 0 | T-3:model_id |
| risk_migration | row_level | 195 | 195 | 15 | 0 | 4 | 0 | - |
| risk_summary | row_level | 12 | 12 | 16 | 0 | 2 | 0 | - |

warehouse statements: 9, elapsed_s: 5.1



/databricks/python/lib/python3.11/site-packages/IPython/core/interactiveshell.py:3585: UserWarning: To exit: use 'exit', 'quit', or Ctrl-D.
  warn("To exit: use 'exit', 'quit', or Ctrl-D.", stacklevel=1)

```

## recon_U4

```text
recon output dir: /tmp/sas_legacy_recon_U4_n0jdiblq
# recon U4 2024-02-29 — PASS
mode: DEGRADED (reference-derived, not SAS-produced); tolerances v1; run_id 89a8b059-475d-4ec1-baf6-4536723ee381
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

## recon_U1

```text
recon output dir: /tmp/sas_legacy_recon_U1_54ffuxes
# recon U1 2024-02-29 — PASS
mode: DEGRADED (reference-derived, not SAS-produced); tolerances v1; run_id 1eea9999-c307-429a-af99-3bde99b9c1db
reference manifest sha256: aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7

| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | failing rules |
|---|---|---|---|---|---|---|---|---|
| cust_accounts_daily | row_level | 466 | 466 | 40 | 0 | 2 | 0 | - |
| acct_exceptions | row_level | 32 | 32 | 12 | 0 | 2 | 1 | - |

warehouse statements: 6, elapsed_s: 3.7


```

## recon_U5

```text
recon output dir: /tmp/sas_legacy_recon_U5_zjrhkl_c
# recon U5 2024-02-29 — FAIL
mode: DEGRADED (reference-derived, not SAS-produced); tolerances v1; run_id 79cdab21-83b9-458a-a011-4dd8d6f5eed6
reference manifest sha256: aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7

| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | failing rules |
|---|---|---|---|---|---|---|---|---|
| archive_batch_history | row_level | 4 | 0 | 9 | 4 | 2 | 0 | T-1, T-2:batch_id,step_num, T-8:step_num |

warehouse statements: 3, elapsed_s: 1.6



/databricks/python/lib/python3.11/site-packages/IPython/core/interactiveshell.py:3585: UserWarning: To exit: use 'exit', 'quit', or Ctrl-D.
  warn("To exit: use 'exit', 'quit', or Ctrl-D.", stacklevel=1)

```

## recon_U5

```text
recon output dir: /tmp/sas_legacy_recon_U5_zjrhkl_c
# recon U5 2024-02-29 — FAIL
mode: DEGRADED (reference-derived, not SAS-produced); tolerances v1; run_id 79cdab21-83b9-458a-a011-4dd8d6f5eed6
reference manifest sha256: aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7

| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | failing rules |
|---|---|---|---|---|---|---|---|---|
| archive_batch_history | row_level | 4 | 0 | 9 | 4 | 2 | 0 | T-1, T-2:batch_id,step_num, T-8:step_num |

warehouse statements: 3, elapsed_s: 1.6



/databricks/python/lib/python3.11/site-packages/IPython/core/interactiveshell.py:3585: UserWarning: To exit: use 'exit', 'quit', or Ctrl-D.
  warn("To exit: use 'exit', 'quit', or Ctrl-D.", stacklevel=1)

```

## recon_U2

```text
recon output dir: /tmp/sas_legacy_recon_U2__s5hfbhj
# recon U2 2024-02-29 — PASS
mode: DEGRADED (reference-derived, not SAS-produced); tolerances v1; run_id 18cd8813-7cb7-4496-914e-648d26938105
reference manifest sha256: aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7

| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | failing rules |
|---|---|---|---|---|---|---|---|---|
| daily_transactions | row_level | 18903 | 18903 | 15 | 0 | 2 | 0 | - |
| running_balances | row_level | 610 | 610 | 8 | 0 | 2 | 0 | - |
| txn_anomalies | row_level | 46 | 46 | 35 | 0 | 2 | 0 | - |
| txn_rejected | row_level | 12 | 12 | 6 | 0 | 2 | 1 | - |

warehouse statements: 12, elapsed_s: 6.5


```

