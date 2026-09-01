# Access Checklist

| Capability | Result | Evidence | D10 ref |
|---|---|---|---|
| Databricks workspace auth | WORKS | `[DISCOVERED]` `databricks current-user me` returned the admin identity (groups `users`, `admins`), workspace id `7474651138173478`. | D10-006 |
| Serverless SQL warehouse | WORKS | `[DISCOVERED]` `Serverless Starter Warehouse`, id `565cd2fd713738c4`, was RUNNING; `SELECT current_metastore(), current_user(), 1` succeeded. | D10-006 |
| Metastore | WORKS | `[DISCOVERED]` Metastore `55de74dc-f7c5-4f94-83fd-d79d5c8c473f`; identity holds CREATE CATALOG via admins. | D10-006 |
| Catalog `ow_tp` | BLOCKED | `[DISCOVERED]` `databricks catalogs get ow_tp` → `Catalog 'ow_tp' does not exist`; self-creatable on STOP A. | D10-006 |
| Write path to `ow_tp` | BLOCKED | `[PROPOSED]` Not tested because the catalog is absent; after creation test create/insert/drop of `ow_tp.sas_recon._preflight`. | D10-006 |
| UC volume / file upload path | BLOCKED | `[PROPOSED]` Not tested because the catalog is absent. | D10-006 |
| Jobs API serverless read | WORKS | `[DISCOVERED]` Re-run `databricks jobs list --limit 1 -o json` succeeded and returned job id `220238957207364`; write access remains untested. | D10-006 |
| Legacy SAS runtime | BLOCKED | `[DISCOVERED]` `which sas sas94` was empty; `Data/bootstrap_local_env.sh` requires Base SAS (`Data/README.md:47-56`). | D10-001 |
| Oracle / Teradata | BLOCKED | `[DISCOVERED]` No connectivity and no credentials named for `ORA_DW` or `TERA_DW`. | D10-002 |
| Control-M | BLOCKED | `[DISCOVERED]` No Control-M export exists in the repository. | D10-005 |
| Repo read | WORKS | `[DISCOVERED]` Clone and source files are readable on `migration/00-setup`. | — |
| Repo write | WORKS | `[DISCOVERED]` `git push --dry-run origin migration/00-setup` succeeded and reported the branch update. | — |
| Slack DM | WORKS | `[FACT]` Write access to DM `D0BQP1XGJ07`; read access is not available. | — |
| Token scope | BLOCKED (irrelevant) | `[DISCOVERED]` `/api/2.0/token/list` returned `does not have required scopes: authentication`; irrelevant to migration and recorded for completeness. | — |
