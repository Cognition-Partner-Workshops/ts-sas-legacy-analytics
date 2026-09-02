# recon U4 2024-01-31 — PASS
mode: DEGRADED (reference-derived, not SAS-produced); tolerances v1; run_id c86d0a51-f7ca-4511-9b2d-5bf3cf337cd9
reference manifest sha256: aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7
xlsx: /Volumes/sas_legacy/sas_bronze/landing/reports/REG_REPORT_202401.xlsx sha256=850d6d21a24f963fe65a1b88f8b5422fed9a7b55d5aa977aef12b5311e2d4e86

| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | failing rules |
|---|---|---|---|---|---|---|---|---|
| monthly_rwa | row_level | 59 | 59 | 16 | 0 | 1 | 0 | - |
| delinquency_aging | row_level | 70 | 70 | 14 | 0 | 2 | 0 | - |
| llp_coverage | row_level | 6 | 6 | 18 | 0 | 2 | 0 | - |
| capital_adequacy | row_level | 1 | 1 | 22 | 0 | 2 | 0 | - |

warehouse statements: 12, elapsed_s: 9.0
