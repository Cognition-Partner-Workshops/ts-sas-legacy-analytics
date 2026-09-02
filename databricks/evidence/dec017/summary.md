# DEC-017 (a) executed — U3 `MODEL_ID` upper-case (coexistence window)

Change: `databricks/src/jobs/credit_risk_scoring.py` `run()` validates `model_id` with `%parmv` default `_CASE=U`
(was `case="N"`), so the macro default `CRM-2023-Q4-v2` is written as `CRM-2023-Q4-V2`, exactly as the legacy
`%parmv(model_id, _req=1)` does. Scorer constants, rules ML-1..ML-8 and tolerances untouched. Reference fixtures
(`databricks/tests/fixtures/reference/`, `docs/migration/recon/reference*`) untouched — owned by the independent recon session.

Live re-run: ad hoc CLI `python src/jobs/credit_risk_scoring.py --business-date 2024-01-31 --executor warehouse`
(same mechanism as wave 2 `w2_b3`), serverless SQL warehouse `565cd2fd713738c4`, no bundle deploy, no clusters.
Start 2026-09-02T00:52:14Z; score_timestamp 2026-09-02T00:52:18.256Z (single distinct value -> slice fully replaced).

| table | rows before | rows after | checksum ex model_id/score_timestamp before | after | model_id |
|---|---|---|---|---|---|
| sas_silver.risk_scores (2024-01-31) | 236 | 236 | 6697560892 | 6697560892 | `CRM-2023-Q4-v2` -> `CRM-2023-Q4-V2` (only distinct value) |
| sas_silver.risk_migration (2024-01-31) | 195 | 195 | 26208382025 | 26208382025 | n/a (column absent) |
| sas_gold.risk_summary | 12 | 12 | 5113489794 | 5113489794 | n/a (column absent) |

PD/LGD/EAD/EL/rating bit-identical (checksum SQL: `checksum_ex_model_id.sql`; raw outputs `pre_state.txt`, `post_state.txt`, `run.txt`).
`risk_scores_woe_debug` not materialised. Live recon harness NOT run against the reference (expected to FAIL on the
T-3 label until the independent session upper-cases the reference; that re-run is theirs). Local gate: ruff clean, pytest 77 passed.
Cost: 1 job execution (6 statements) + 3 read-only evidence statements on the serverless warehouse; ACUs not visible from the CLI.
