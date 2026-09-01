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
