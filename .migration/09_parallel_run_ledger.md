# Parallel-run ledger — P1 banking-core coexistence window (`!dbx_parallel_run`)

| Field | Value |
|---|---|
| Window state | **OPEN — GREEN clock started 2026-09-02T01:12:17Z, 1/5** (cycle 4, first run against the DEC-017 (a)-corrected reference, PR #37) |
| Tier | `snapshot` (STOP C approved): no live legacy runtime exists; the scheduled recon re-runs the reference battery daily against the current `sas_legacy` silver/gold state |
| Mode | DEGRADED — every verdict is **reference-derived, not SAS-produced** (reference manifest `docs/migration/recon/reference/manifest.json`, sha256 `39cca40c…c3ed` since PR #37 — cycles 1–3 ran against `aea7c04a…25cc7`; tolerances v1) |
| Recon job | `sas_legacy_recon`, job id `1058116656072070`, bundle target `dev`, 5 independent serverless tasks `recon_U1`..`recon_U5` (no `depends_on`, `max_concurrent_runs: 1`) |
| Cadence | `0 15 6 * * ?` UTC (06:15 daily), `UNPAUSED`; reads silver/gold, writes only `sas_recon.run_log` |
| Legacy trigger authority | Control-M; `sas_legacy_run_daily_banking` (job `216001923865775`) stays `PAUSED` until STOP E |
| STOP E | DEFERRED 2026-09-02 (DEC-018): continue coexistence until REQ-05 SAS-produced recon PASS and GREEN clock 5/5 |
| Exit criterion | 5 consecutive GREEN cycles **and** REQ-05 SAS-produced recon (upgrade from `snapshot` tier), or user acceptance at STOP E |
| Cost per cycle (observed) | ~5.3–6.1 serverless task-minutes (5 tasks x ~60–70 s) + 42 warehouse statements on `565cd2fd713738c4` (45 when a task retries) |
| Alerting | WEBHOOK: NOT WIRED (creating a notification destination needs workspace-admin; `notification-destinations list` is empty). Remediation is carried by the daily Devin automation "sas_legacy P1 coexistence: recon ledger + remediation" (D5-004) |
| Run history | 6 job runs total: 2 infra shakedowns (below) + 4 recon cycles; GREEN clock counts recon cycles from cycle 4 only |
| Evidence | `databricks/evidence/coexistence/` (run JSON + per-task outputs, scrubbed to `<requester>`) |

Verdict semantics: GREEN = 5/5 tasks SUCCESS (every unit PASS); RED = any task FAILED (`run_recon.py` exits 1 on any FAIL verdict). Staged reds are marked `STAGED — expected`.

Note on the staged red: `business_date` only parameterises the `{yyyymmdd}` batch-id prefix used by U5 (`archive_batch_history` latest-batch filter); U1–U4 tables are date-agnostic snapshots, so an override to a date with no data reds U5 only. This proves the fail path and task independence (a red task never hides another), not a whole-job red.

## Cycles

| UTC timestamp | run_id | verdict | detail | triage | PR |
|---|---|---|---|---|---|
| 2026-09-02T00:47:33Z | 1084922540695680 | FAILED — shakedown (infra) | U2/U3/U4 "Workload failed" at task entry (not a recon FAIL); U1 retried SUCCESS, U5 SUCCESS | deploy shakedown, entry-point path fix; recorded per audit F-4 | #38 |
| 2026-09-02T00:50:32Z | 698984939827672 | FAILED — shakedown (infra) | U2/U3/U4 "Workload failed" at task entry (not a recon FAIL) | deploy shakedown; recorded per audit F-4 | #38 |
| 2026-09-02T00:53:00Z | 876111316294946 | RED (4/5) | U3 `T-3:model_id` `CRM-2023-Q4-V2` vs reference `-v2`; U1/U2/U4/U5 PASS | (a) baseline drift — approved conversion change DEC-017 (a); reference correction pending, independent recon session | #36 |
| 2026-09-02T01:01:57Z | 1063912159259719 | RED (3/5) — STAGED, expected | `business_date=2024-02-29` override: U5 `T-1` (0 target rows vs 4 ref), `T-2:batch_id,step_num`, `T-8:step_num`; U3 `T-3:model_id` (as above); U1/U2/U4 PASS (date-agnostic) | staged red; fail path + independence proven; webhook not wired (see header) | #38 |
| 2026-09-02T01:04:00Z | 737965062575783 | RED (4/5) | U3 `T-3:model_id` only; U1/U2/U4/U5 PASS — recovery from the staged red confirmed | (a) baseline drift — DEC-017 (a), same as cycle 1 | #36 |
| 2026-09-02T01:12:17Z | 371352986351516 | GREEN (5/5) | U1/U2/U3/U4/U5 PASS, 0 FAIL; manifest `39cca40c…` in every task output; 5.3 task-min + 42 statements | none — GREEN 1/5 | this PR |
