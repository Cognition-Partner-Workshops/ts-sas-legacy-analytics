# SKILL FEEDBACK harvest (per wave)

Systematic findings reported by children. Status: OPEN until promoted into the plugin skill (external repo `dbx-migration-plugin`) or into a child hand-off preflight line.

| Wave | Skill | Finding | Promotion |
|---|---|---|---|
| 0 | databricks-auth-cli | Pre-set `DATABRICKS_HOST/TOKEN` in the env shadow the `DATABRICKS_DEMO_*` names; `bundle validate` 403s until the mapping is exported explicitly. | Added to every P1 hand-off preflight (wave 1+). Skill PR: OPEN. |
| 0 | unity-catalog-conventions | `databricks fs cp` needs `dbfs:/Volumes/...`; SQL uses `/Volumes/...`. | Hand-off preflight (wave 1+). Skill PR: OPEN. |
| 0 | data-reconciliation | No fixture-mode pattern when reference outputs do not exist yet; harness now exits 2 "reference missing". | Resolved by W0-R landing; pattern noted. Skill PR: OPEN. |
| 0 | data-reconciliation | DROP/KEEP *statements* apply to every OUTPUT set of a multi-output DATA step; only `(drop=)` data-set options are per-target. `PROC APPEND FORCE` truncates to BASE schema. | Hand-off for U1/U2 (wave 1-2). Skill PR: OPEN. |
| 0 | data-reconciliation | SAS `. < x` is TRUE in DATA-step/CASE logic (not only sort order); classification chains diverge from Spark NULL semantics. Check declared keys against the SAS GROUP BY. | Hand-off for U2/U4. Skill PR: OPEN. |
| 0 | prediction-parity | PROC MEANS `N=` without var list = non-missing count of first VAR, not `_FREQ_`; `std` is sample (n-1); anomaly stats from pre-append history. | Hand-off for U2/U3. Skill PR: OPEN. |
| 1 | asset-bundles / sas-programs | Serverless `spark_python_task` exec()s the file: no `__file__`; any `SystemExit` (even 0) is reported FAILED and auto-retried. Resolve paths via `sys.argv[0]` fallback; never `raise SystemExit(0)`. | Wave-2 hand-off preflight. Skill PR: OPEN. |
| 1 | asset-bundles | Non-stdlib imports (e.g. `openpyxl` via `sas_macros`) need `environments[].spec.dependencies`; `bundle validate` does not catch the omission. | Wave-2 hand-off preflight. Skill PR: OPEN. |
| 1 | data-reconciliation | Statement Execution API DDL results carry no `manifest.schema`; harness must not assume result columns (fixed in `recon/warehouse.py`). | Fixed in harness (PR #29). Skill PR: OPEN. |
| 1 | data-reconciliation | Full-row multiset tables: pre-state per-column rule classes in the hand-off (T-3 vs T-5 numerics, literally-null run-time columns = T-3 not T-7) or the live-recon cap is spent on harness spec, not code. | Wave-2 hand-off (U2 `txn_rejected`). |
| 1 | sas-programs | Skill directory absent under the plugin's `skills/`; children derive DATA-step semantics from the hand-off preflight only. | Owner plugin maintainers. OPEN. |
