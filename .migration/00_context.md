# Migration Context — ts-sas-legacy-analytics → Databricks

**State:** STOP A APPROVED (2026-09-01, DEC-010). Handed off to `!dbx_migrate_pipeline`; inventory may begin.

## Sources of truth (read in this order)
1. `docs/migration/ts-sas-legacy-analytics_target_state.md` — the target state; every conversion decision cites it.
2. `.migration/01_conventions.md` — Databricks rules distilled for the estate.
3. `.migration/02_glossary.md` — SAS ↔ Databricks term map.
4. `.migration/03_recon_tolerances.md` — THE parity contract; recon reports cite its version.
5. `.migration/04_dependency_register.md` — D1–D10 register; open D10s block work.
6. `.migration/05_progress.md` — pipeline × phase state; updated by every session.
7. `.migration/06_decisions.md` — every decision with date, who, why.
8. `.migration/07_access_checklist.md` — WORKS / BLOCKED per capability, with evidence.

## Intake facts (from the kickoff message and this session's probes)

| Item | Value | Status |
|---|---|---|
| Source | Base SAS 9.4 estate: banking + insurance programs, credit-risk scorecard, PROC FORMAT catalogs, 92 macros, Control-M batch orchestrators | FACT (kickoff, README.md) |
| Languages | SAS Base (DATA step), SAS macro, PROC SQL, PROC FORMAT, PROC MEANS/SORT/APPEND/EXPORT/TRANSPOSE/FREQ. No R, SPSS, Hive, Spark, notebooks. | FACT (`grep -l "proc " Programs/ Macro/`) |
| Code location | This repo, `main`. Runtime paths `/opt/sas/custom` (code) and `/data/sas` (data) per `Config/autoexec.sas`; no SAS server is reachable. | FACT / DISCOVERED |
| Scope | Whole estate, including `Programs/Banking/credit_risk_scoring.sas` | FACT (kickoff) |
| Recon baseline | `Data/csv/*` seed snapshots, business date 31JAN2024 (banking only; insurance has none) | FACT (kickoff, `Data/README.md`) |
| Target | Shared demo workspace `DATABRICKS_DEMO_HOST` / `DATABRICKS_DEMO_TOKEN`, new dedicated catalog `sas_legacy` (renamed from `ow_tp` at STOP A, DEC-009), serverless only | FACT (kickoff + STOP A reply) |
| Excluded reference | `uc-data-migration-sas-to-databricks` — must not be consulted. Pre-existing `migration/*`/`devin/*` branches in this repo are likewise not a reference. | FACT (kickoff) / PROPOSED |
| Notifications | Slack DM to the requester (`D0BQP1XGJ07`) only, for STOPs, halts, wave closes. No channels, no per-task or per-child messages. | FACT (kickoff) |
| Dialect skills attached | `sas-programs` (primary), `prediction-parity` (scorer), `recon-harness`, `dlt-pipelines` (consulted, not adopted — Jobs chosen) | FACT |

## Estate partition (drives inventory workload typing)

| Partition | Units | Profile |
|---|---|---|
| **Data code** | `load_customer_accounts`, `daily_transaction_processing`, `monthly_regulatory_reporting`, `claims_processing`, `policy_valuation`, `customer_profitability`; orchestrators `run_daily_banking`, `run_daily_insurance` | SQL + PIPELINE + ORCHESTRATION, standard recon (T-rows) |
| **Model code** | `credit_risk_scoring` (fixed logistic scorecard `CRM-2023-Q4-v2`; scoring only, no training) | ML-SCORING, prediction-parity gate (ML-rows), D9 consumers |
| **Shared objects (D2, wave 0)** | 92 macros in `Macro/`; format catalogs `Formats/banking_formats.sas` (10 formats), `Formats/insurance_formats.sas` (6); `Config/autoexec*.sas` | converted once, before any program |

## Family defaults applied
- Unit = program + its `%run_step` entry in the batch orchestrator.
- Lineage = SAS parser (`%include`, `libname`, `set`/`merge`/`from`/`out=`) + directory convention + orchestrator order. No scheduler export exists → INFERRED edges expected; Control-M definitions requested (D5).
- Dual-run mechanism: **none live**. Legacy cannot be executed here. Comparison = Databricks output vs. legacy baseline per `03_recon_tolerances.md` §R-0 (customer-supplied SAS outputs preferred; independent reference implementation as fallback). Recon mode DEGRADED.
- Prediction parity: routed to `03_recon_tolerances.md` §ML. Legacy bit-stability probe **not run** (no SAS) → exact match not promised.

## STOP A decision list (all approved 2026-09-01; see 06_decisions.md)

1. **Profiles & layout** — target-state profiles as drafted; catalog `sas_legacy` with schemas `sas_bronze / sas_silver / sas_gold / sas_ref / sas_recon` and the libref map. `sas_legacy` does not exist yet; I create it as the first wave-0 action on approval.
2. **Compute** — serverless SQL warehouse `565cd2fd713738c4` + serverless job compute; Jobs (not DLT).
3. **Tolerances v1** — table rules T-1..T-12 and scorer rules ML-1..ML-8 in `03_recon_tolerances.md`, approved; scorer tolerance owned by the requester (DEC-010).
4. **Legacy baseline (R-0)** — DECIDED: option (b), independent Python reference implementation with caveat (DEC-004).
5. **Access posture** — acknowledged D10s: no SAS runtime; no Oracle/Teradata; no insurance seed; no `ORA_DW.COST_OF_FUNDS` seed; no Control-M export; `sas_legacy` not yet provisioned (self-creatable). Insurance units and cost-of-funds P&L columns are convertible but not reconcilable until data arrives.
6. **Notification contract** — DM only, STOPs/halts/wave closes only. Confirm the same for child sessions.

## Hand-off
STOP A confirmed; `!dbx_migrate_pipeline` invoked with this workspace. Front-door session did no inventory, analysis, or conversion.
