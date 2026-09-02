# recon U4 2024-01-31 — PASS
mode: DEGRADED (reference-derived, not SAS-produced); tolerances v1; run_id 2a8c6f9e-7724-49d9-9593-79b07f6e34ee
reference manifest sha256: aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7

| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | failing rules |
|---|---|---|---|---|---|---|---|---|
| monthly_rwa | row_level | 59 | 59 | 16 | 0 | 1 | 0 | - |
| delinquency_aging | row_level | 70 | 70 | 14 | 0 | 2 | 0 | - |
| llp_coverage | row_level | 6 | 6 | 18 | 0 | 2 | 0 | - |
| capital_adequacy | row_level | 1 | 1 | 22 | 0 | 2 | 0 | - |

warehouse statements: 12, elapsed_s: 9.0
