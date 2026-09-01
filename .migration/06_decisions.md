# Decision Log

| ID | Date | Decision | Rationale | Status | Approved by |
|---|---|---|---|---|---|
| DEC-001 | 2026-09-01 | Catalog `ow_tp`; schemas `sas_bronze`, `sas_silver`, `sas_gold`, `sas_ref`, `sas_recon`; fixed libref map. | Isolate all migration objects in the pinned catalog while preserving source namespace intent. | PROPOSED | pending STOP A |
| DEC-002 | 2026-09-01 | Serverless only; use Databricks Jobs, not DLT. | Matches the target compute posture and scheduler-shaped legacy estate. | PROPOSED | pending STOP A |
| DEC-003 | 2026-09-01 | Tolerances v1 are PROPOSED; exact-match on PD is not offered because a legacy bit-stability probe is impossible. | No SAS runtime is available; use band exactness, numeric PD tolerance, and rank preservation per `03_recon_tolerances.md`. | PROPOSED | pending STOP A |
| DEC-004 | 2026-09-01 | Recon mode is DEGRADED; R-0 options (a) customer SAS outputs or (b) independent reference implementation remain pending. | Legacy outputs are unavailable; only option (a) permits calling results a legacy match. | PROPOSED | pending STOP A |
| DEC-005 | 2026-09-01 | Estate partition: `credit_risk_scoring` is the only model code; do not re-model. | Preserve the fixed `CRM-2023-Q4-v2` scorer and apply prediction-parity gates only. | PROPOSED | pending STOP A |
| DEC-006 | 2026-09-01 | Exclude `uc-data-migration-sas-to-databricks` and existing `migration/wave1*` / `devin/*` branches as references. | The current repository artifacts and target-state documents are the source of truth for this run. | FACT | pending STOP A |
| DEC-007 | 2026-09-01 | Notification contract: Slack DM `D0BQP1XGJ07` only, for STOPs, halts, and wave closes. | Avoid per-task or per-child notifications and keep the migration control surface centralized. | FACT | pending STOP A |
| DEC-008 | 2026-09-01 | Insurance units and cost-of-funds-dependent report work are convertible but not reconcilable until D10 data arrives. | Insurance seeds, `ORA_DW.COST_OF_FUNDS`, and a legacy baseline are unavailable. | PROPOSED | pending STOP A |
