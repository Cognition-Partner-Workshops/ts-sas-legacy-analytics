## recon_U3

```text
recon output dir: /tmp/sas_legacy_recon_U3_hidalx3c
# recon U3 2024-01-31 — FAIL
mode: DEGRADED (reference-derived, not SAS-produced); tolerances v1; run_id aec2067f-dbfd-460e-9889-25bfd89e1e85
reference manifest sha256: aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7

| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | failing rules |
|---|---|---|---|---|---|---|---|---|
| risk_scores | row_level | 236 | 236 | 64 | 1 | 4 | 0 | T-3:model_id |
| risk_migration | row_level | 195 | 195 | 15 | 0 | 4 | 0 | - |
| risk_summary | row_level | 12 | 12 | 16 | 0 | 2 | 0 | - |

warehouse statements: 9, elapsed_s: 4.7



/databricks/python/lib/python3.11/site-packages/IPython/core/interactiveshell.py:3585: UserWarning: To exit: use 'exit', 'quit', or Ctrl-D.
  warn("To exit: use 'exit', 'quit', or Ctrl-D.", stacklevel=1)

```

## recon_U4

```text
recon output dir: /tmp/sas_legacy_recon_U4_02rsqpui
# recon U4 2024-01-31 — PASS
mode: DEGRADED (reference-derived, not SAS-produced); tolerances v1; run_id 70d1e7c3-75b2-491b-b85d-6158fe0b4a09
reference manifest sha256: aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7
xlsx: /Volumes/sas_legacy/sas_bronze/landing/reports/REG_REPORT_202401.xlsx sha256=850d6d21a24f963fe65a1b88f8b5422fed9a7b55d5aa977aef12b5311e2d4e86

| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | failing rules |
|---|---|---|---|---|---|---|---|---|
| monthly_rwa | row_level | 59 | 59 | 16 | 0 | 1 | 0 | - |
| delinquency_aging | row_level | 70 | 70 | 14 | 0 | 2 | 0 | - |
| llp_coverage | row_level | 6 | 6 | 18 | 0 | 2 | 0 | - |
| capital_adequacy | row_level | 1 | 1 | 22 | 0 | 2 | 0 | - |

warehouse statements: 12, elapsed_s: 5.9


```

## recon_U1

```text
recon output dir: /tmp/sas_legacy_recon_U1_0e61uii6
# recon U1 2024-01-31 — PASS
mode: DEGRADED (reference-derived, not SAS-produced); tolerances v1; run_id 4badda69-66ac-442d-be95-17aed3a39423
reference manifest sha256: aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7

| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | failing rules |
|---|---|---|---|---|---|---|---|---|
| cust_accounts_daily | row_level | 466 | 466 | 40 | 0 | 2 | 0 | - |
| acct_exceptions | row_level | 32 | 32 | 12 | 0 | 2 | 1 | - |

warehouse statements: 6, elapsed_s: 3.2


```

## recon_U5

```text
recon output dir: /tmp/recon/U5
# recon U5 2024-01-31 — PASS
mode: DEGRADED (reference-derived, not SAS-produced); tolerances v1; run_id 7012e182-34eb-40cf-8caa-449741208b1e
reference manifest sha256: aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7

| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | failing rules |
|---|---|---|---|---|---|---|---|---|
| archive_batch_history | row_level | 4 | 4 | 13 | 0 | 2 | 0 | - |

warehouse statements: 3, elapsed_s: 1.7


```

## recon_U2

```text
recon output dir: /tmp/sas_legacy_recon_U2_7q_tixy2
# recon U2 2024-01-31 — PASS
mode: DEGRADED (reference-derived, not SAS-produced); tolerances v1; run_id 1ff41dd6-4bbe-42f4-ae03-a81b87e66120
reference manifest sha256: aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7

| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | failing rules |
|---|---|---|---|---|---|---|---|---|
| daily_transactions | row_level | 18903 | 18903 | 15 | 0 | 2 | 0 | - |
| running_balances | row_level | 610 | 610 | 8 | 0 | 2 | 0 | - |
| txn_anomalies | row_level | 46 | 46 | 35 | 0 | 2 | 0 | - |
| txn_rejected | row_level | 12 | 12 | 6 | 0 | 2 | 1 | - |

warehouse statements: 12, elapsed_s: 6.3


```

