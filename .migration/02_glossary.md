# SAS ↔ Databricks Glossary

| Status | SAS term | Databricks term / conversion rule |
|---|---|---|
| PROPOSED | libref / library | Unity Catalog schema; use the fixed map in `01_conventions.md`. |
| PROPOSED | dataset / member | Delta table. |
| PROPOSED | DATA step | PySpark or Databricks SQL, choosing SQL for set-based logic. |
| PROPOSED | PROC SQL | Databricks SQL. |
| PROPOSED | PROC FORMAT value / informat | Reference-table join to `sas_legacy.sas_ref`. |
| PROPOSED | macro | Python function in `dbx/sas_macros/`. |
| PROPOSED | macro variable | Job parameter or widget. |
| PROPOSED | `%include` | Python/module import or explicit task dependency. |
| PROPOSED | `RETAIN` / BY-group | Window function first; PySpark state only when a window is insufficient. |
| PROPOSED | hash object | Broadcast join. |
| PROPOSED | PROC APPEND | `MERGE INTO`. |
| PROPOSED | PROC MEANS / SUMMARY | `GROUP BY`. |
| PROPOSED | PROC TRANSPOSE | `PIVOT`. |
| PROPOSED | PROC EXPORT / `%export_xlsx` | Downstream openpyxl task; reconcile the feeding gold table, not the workbook. |
| PROPOSED | `%sendmail` | Databricks job notification. |
| PROPOSED | `%lock` | Delta ACID; conversion is a no-op. |
| PROPOSED | `%nobs` | A `run_log` row recording the observed count. |
| PROPOSED | SAS missing numeric `.` / blank | `NULL`; SAS numeric missing sorts low. |
| FACT | SAS blank character | `''`, not `NULL`; this is a conversion rule that must remain distinct from numeric missing. |
| PROPOSED | SAS date numeric | `DATE`. |
| PROPOSED | SAS datetime numeric | `TIMESTAMP`. |
| PROPOSED | `"..."d` literal | Databricks `DATE '...'` literal. |
| PROPOSED | `&CURR_DT` | `business_date` job parameter. |
| PROPOSED | Control-M job | Databricks Workflow / Job. |
| PROPOSED | WORK library | Temporary views or task-scoped temporary relations. |
| PROPOSED | autoexec | Bundle variables and job parameters. |
| FACT | PD | Probability of Default; fixed scorecard output and ML parity metric. |
| FACT | LGD | Loss Given Default; fixed scorecard output. |
| FACT | EAD | Exposure at Default; fixed scorecard output. |
| FACT | EL | Expected Loss, typically derived from PD × LGD × EAD. |
| FACT | WOE / WoE | Weight of Evidence feature transformation; materialize debug intermediates when ML parity fails. |
| FACT | risk rating | Discrete 1–7 scorecard band and migration input/output. |
| FACT | scorecard | Fixed logistic model `CRM-2023-Q4-v2`; scoring only, no re-modeling. |
| FACT | risk migration | Change between previous and current risk ratings (`NEW`, `UPGRADE`, `DOWNGRADE`). |
