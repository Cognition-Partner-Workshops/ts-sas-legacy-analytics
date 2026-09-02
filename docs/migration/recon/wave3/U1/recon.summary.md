# recon U1 2024-01-31 — PASS
mode: DEGRADED (reference-derived, not SAS-produced); tolerances v1; run_id 25d71806-5130-487d-b96a-a9f7e07d82bf
reference manifest sha256: aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7

| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | failing rules |
|---|---|---|---|---|---|---|---|---|
| cust_accounts_daily | row_level | 466 | 466 | 40 | 0 | 2 | 0 | - |
| acct_exceptions | row_level | 32 | 32 | 12 | 0 | 2 | 1 | - |

warehouse statements: 6, elapsed_s: 11.6
