# Reconciliation Tolerances — THE parity contract

**Version:** v1-PROPOSED (2026-09-01). Becomes v1 (FACT) only on explicit STOP A approval. Every recon report cites the version it was judged against.

## Recon mode: DEGRADED (snapshot baseline)

- Legacy inputs are the committed seed snapshots in `Data/csv/` (business date 31JAN2024, deterministic generator `Data/generate_seed_data.py`). Manifest (file, rows excl. header, sha256) is recorded in `05_progress.md` §Baseline manifest before wave 0.
- There is **no executable legacy runtime** in this environment (no SAS binary; `Data/bootstrap_local_env.sh` needs Base SAS). Legacy *outputs* are therefore not available today. See decision R-0 below.
- Consequence stated plainly: sample parity on 487 accounts / 622 feed rows does not extrapolate to the production volumes seen in `Logs/` (847k accounts, 2.3M daily transactions). An in-perimeter recon run by the customer on real SAS output is the entry criterion for STOP E.
- Every recon report header states `mode: DEGRADED, baseline: Data/csv @ <commit>, tolerances: v1`.

## R-0 Legacy-output baseline (decision needed at STOP A)

| Option | What it means | Recommended |
|---|---|---|
| (a) Customer-run SAS outputs | Run `Data/bootstrap_local_env.sh` on any Base SAS 9.4 host, commit `STG_BANK.*`, `CURATED.*`, `REPORTS.*` as CSV under `Data/expected/` (+ the printed row counts). Recon then diffs Databricks tables against genuine SAS output. | **Yes** — the only path that lets us call anything "matches legacy". |
| (b) Independent reference implementation | The recon session (never the migrating child) writes a plain-Python oracle per program straight from the SAS source, runs it on `Data/csv`, and diffs the Databricks output against it. Two independent readings of the code agreeing is evidence, but both can share a misreading. | Fallback only; every report carries the caveat "reference-derived, not SAS-produced". |

**Decision (STOP A, DEC-004): option (b).** Every recon report carries the caveat "reference-derived, not SAS-produced"; option (a) remains open as an upgrade path if SAS outputs are later committed under `Data/expected/`.

## Table-level tolerances (data code: all programs except the scorer)

Population column says what each rate is computed over.

| ID | Data type / check | Tolerance | Population | Status |
|---|---|---|---|---|
| T-1 | Row count per output table (per business_date) | exact (0 difference) | every silver/gold table | PROPOSED |
| T-2 | Business-key set (e.g. `ACCOUNT_ID`, `TXN_ID`, `ACCOUNT_ID+SNAPSHOT_DATE`) | exact set equality, both directions | every keyed table | PROPOSED |
| T-3 | Integers, codes, flags, strings, dates | exact; strings compared after `rtrim` (SAS pads char); case preserved | all columns of those types | PROPOSED |
| T-4 | Currency / balance amounts (`*_BALANCE`, `*_AMOUNT`, `EAD`, `EXPECTED_LOSS`, `RWA`, `CAPITAL_*`) | abs diff ≤ 0.005 per row (i.e. equal at 2 dp) | all rows | PROPOSED |
| T-5 | Ratios / percentages (`UTILIZATION_PCT`, `LTV`, loss ratios, coverage ratios, NIM) | abs diff ≤ 1e-6 | all rows | PROPOSED |
| T-6 | Statistical outputs (z-scores, means, std in `TXN_ANOMALIES`) | abs diff ≤ 1e-6; anomaly *flag* exact | all rows | PROPOSED |
| T-7 | Timestamps generated at run time (`*_TIMESTAMP`, `LOAD_DTTM`, `SCORE_TIMESTAMP`) | excluded from comparison; presence/non-null checked | all rows | PROPOSED |
| T-8 | Aggregates per table (SUM of every numeric column, COUNT DISTINCT of every key) | same tolerances as the column's row rule | every table | PROPOSED |
| T-9 | Reject / exception counts (`TXN_REJECTED` by reject rule, `ACCT_EXCEPTIONS` by `EXCEPTION_TYPE`) | exact | every reject rule / exception type | PROPOSED |
| T-10 | Ordering | none required; tables compared as sets. Legacy `RUNNING_BALANCES` order-dependence is handled by comparing on the explicit `(ACCOUNT_ID, TXN_DATE, TXN_ID)` key. | n/a | PROPOSED |
| T-11 | Rounding rule | Target uses `ROUND(x, n)` with HALF_UP to mirror SAS `ROUND` (half away from zero) for non-negative values; negative-value half cases are flagged in the field dictionary and asserted explicitly. `AVG`: no truncation on either side (SAS `MEAN` and Spark `AVG` are both double). | all rounded columns | PROPOSED |
| T-12 | Excel workbooks (`%export_xlsx`) | not reconciled; the gold table feeding them is. | n/a | PROPOSED |

## ML-SCORING tolerances (credit_risk_scoring.sas → `sas_legacy.sas_silver.risk_scores`, `risk_migration`, `sas_legacy.sas_gold.risk_summary`)

Scorer facts: fixed-coefficient logistic scorecard, deterministic by inspection (no RNG, no training). **Legacy bit-stability probe not run** (no SAS). Per playbook, exact match on `PD` is therefore not accepted as a tolerance; rank/band exactness plus a numeric tolerance is proposed instead.

| ID | Metric | Tolerance | Population | Status |
|---|---|---|---|---|
| ML-1 | `NEW_RISK_RATING` (band 1–7) | exact per account | all scored accounts (types MTG, AUTO, PERS, CC, LOC, HELC) | PROPOSED |
| ML-2 | `PD` | abs diff ≤ 1e-9 per account (covers `exp()` last-ulp differences; a real bin or coefficient error is ≥1e-3) | all scored accounts | PROPOSED |
| ML-3 | `LGD`, `EAD` | `LGD` abs ≤ 1e-9; `EAD` abs ≤ 0.005 | all scored accounts | PROPOSED |
| ML-4 | `EXPECTED_LOSS` | abs ≤ 0.01 per account; SUM over table abs ≤ 0.05 | all scored accounts | PROPOSED |
| ML-5 | Rank order of `PD` | Spearman ρ = 1.0 (ties allowed; scorecard produces discrete PD values) | all scored accounts | PROPOSED |
| ML-6 | `MIGRATION_DIRECTION`, `PREV_RATING`, `CURR_RATING` | exact | all rows of `risk_migration` | PROPOSED |
| ML-7 | Band-edge cases | accounts whose `PD` lies within 1e-9 of a rating edge (0.005, 0.01, 0.03, 0.07, 0.15, 0.30) are listed explicitly in the report; none expected on seed data | scored accounts | PROPOSED |
| ML-8 | Feature parity first | `WOE_*` intermediates (dropped by legacy) are materialised in a debug table on the target side and compared against the reference when any ML-1..ML-6 row fails | scored accounts | PROPOSED |

Business owner for the parity tolerance: **unnamed** — the kickoff named no model owner. STOP A asks the requester to either own ML-1..ML-8 or scope the scorer out until an owner does. No scoring job enters scope without a user-owned tolerance.

## Recon economics

| Item | Value | Status |
|---|---|---|
| Row-diff size tier | Full row-level diff up to 5,000,000 rows per table; above that, keyed stratified sample (1% or 100k rows, whichever larger) + full aggregates. Seed data is entirely below the tier. | PROPOSED |
| Legacy-query concurrency cap | N/A — no live legacy engine. Reference-implementation runs are local. | DISCOVERED |
| Target-side recon compute | serverless SQL warehouse `565cd2fd713738c4` only | FACT |

## Units convertible but NOT reconcilable with today's baseline

| Unit | Missing baseline | Effect |
|---|---|---|
| `claims_processing.sas`, `policy_valuation.sas` | no `RAW_INS.*`, no `TERA_DW.*` seed | D10; unit can be converted with unit tests only, cannot reach RECON_GREEN |
| `customer_profitability.sas` | no `ORA_DW.COST_OF_FUNDS` seed | partial recon only; the P&L columns depending on cost of funds are excluded until seed supplied |
| `monthly_regulatory_reporting.sas` | `%export_xlsx` needs SAS/ACCESS PC Files on the legacy side | table-level recon only (T-12) |

## Amendment procedure

A tolerance changes only by explicit user approval recorded in `06_decisions.md`. The change is written as a new dated version (v2, v3, …) of this file section with the old row preserved and struck through, plus a stated re-verification scope: every unit already RECON_GREEN under the old version is re-run under the new one before the new version is cited by any PR.
