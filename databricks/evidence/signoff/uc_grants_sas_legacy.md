# Unity Catalog grants on `sas_legacy` — read-only listing for STOP E (2026-09-02, warehouse `565cd2fd713738c4`)

| Statement | State | Rows |
|---|---|---|
| `SHOW GRANTS ON CATALOG sas_legacy` | SUCCEEDED | 0 (no explicit grants) |
| `SHOW GRANTS ON SCHEMA sas_legacy.sas_bronze` | SUCCEEDED | 0 |
| `SHOW GRANTS ON SCHEMA sas_legacy.sas_silver` | SUCCEEDED | 0 |
| `SHOW GRANTS ON SCHEMA sas_legacy.sas_gold` | SUCCEEDED | 0 |
| `DESCRIBE CATALOG EXTENDED sas_legacy` | SUCCEEDED | Owner = migration identity (`<requester>`, workspace `admins` group); Catalog Type Regular; Predictive Optimization inherited |

Result: the catalog is owner-only. No consumer, batch, or read-only principal holds any privilege on `sas_legacy` or its schemas. Both jobs run as the same owner identity (`run_as_user_name` scrubbed in `job_*.json`).
