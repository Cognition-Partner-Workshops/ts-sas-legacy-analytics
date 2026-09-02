# P1 banking-core — consumer cutover rehearsal plan and rollback runbook

Status: DRAFT for STOP E (2026-09-02). Nothing in this runbook is executed until STOP E is approved with the sentence recorded in `.migration/evidence_pack/stop_e_brief.md`. Steps marked **REHEARSAL: DESK-CHECK ONLY** cannot be executed in this engagement (no live Control-M, no SAS runtime, no production consumers reachable); they were walked through on paper against the artifacts cited.

Principals:
- **Cutover principal** — customer-held identity with (a) edit rights on the Control-M `BANK_MASTER` job definition and (b) `CAN MANAGE` on job `sas_legacy_run_daily_banking` (`216001923865775`). **Devin never holds, requests, or is granted this principal** (`AGENTS.md` guardrail 5; plan §6). Every step tagged `[CUTOVER PRINCIPAL]` is performed by the customer.
- **Migration identity** — owner of `sas_legacy` and `run_as` of both jobs; used only for read-only verification below.
- Requester = the customer contact per DEC-007 (no names in this document).

Legacy is never modified: rollback is "stop pointing at the new thing", which is why it is instant.

---

## 1. Registered consumers (cutover order)

Consumers per analysis §5-6 / plan §1 (D4, D9). REQ-02 (consumer names) is unanswered, so rows 1-3 are the *classes* the code proves exist; the customer fills the concrete systems before the flip (pre-flight P-1).

| # | Consumer | Legacy contract | Target contract | Flip order rationale |
|---|---|---|---|---|
| C1 | Control-M `BANK_MASTER` (trigger, D5-001) | fires `BatchJobs/run_daily_banking.sas` 05:45 daily | fires nothing; `sas_legacy_run_daily_banking` schedule `0 45 5 * * ?` UTC becomes the trigger | first — it is the switch; everything else follows the first Databricks-produced business date |
| C2 | Downstream `CURATED.*` / `STG_BANK.*` readers (D9-001/002): P2 `customer_profitability` (reads `CURATED.RISK_SCORES`, `CUST_ACCOUNTS_DAILY`, `DAILY_TRANSACTIONS`); any other silver readers named by REQ-02 | SAS datasets `CURATED.RISK_SCORES`, `CURATED.DAILY_TRANSACTIONS`, `STG_BANK.CUST_ACCOUNTS_DAILY` | `sas_legacy.sas_silver.risk_scores`, `daily_transactions`, `cust_accounts_daily` (stable contracts, plan §1) | second — silver is written by tasks 1-3; verify before gold readers |
| C3 | `REPORTS.*` readers (D4-001): risk summary, monthly RWA, delinquency aging, LLP coverage, capital adequacy | SAS datasets `REPORTS.*` | `sas_legacy.sas_gold.*` | third — gold depends on silver |
| C4 | `REG_REPORT_<yyyymm>.xlsx` recipients (D4-002; regulator-facing) | file at `&REPORT_PATH` on the SAS server | `/Volumes/sas_legacy/sas_bronze/landing/reports/REG_REPORT_<yyyymm>.xlsx` (3 sheets; content NOT reconciled beyond T-12 existence + sheet names) | last, and only at the first month-end after C1-C3 are verified |
| C5 | On-call / DL e-mail recipients (`%sendmail`, D4-003) | SMTP from SAS | Jobs `on_failure` notification → destination TBD (REQ-02) | wired before C1, not after (a silent failure after the flip is the worst case) |

## 2. Pre-flight checks (all before the flip; any FAIL = do not flip)

| # | Check | How | Who | Rehearsal status |
|---|---|---|---|---|
| P-1 | STOP E approved with the exact sentence; DEC-016 decided; consumers C2-C4 named (REQ-02 answer) | `06_decisions.md` row + DM record | Requester | DESK-CHECK ONLY (approval outstanding) |
| P-2 | GREEN clock: ≥ 5 consecutive GREEN `sas_legacy_recon` cycles, or explicit DEGRADED acceptance | `09_parallel_run_ledger.md` | Devin (read) | executable now → currently **1/5** |
| P-3 | REQ-05 SAS-produced recon PASS, or explicit DEGRADED acceptance | `Data/expected/` + recon re-run | Requester / recon session | **NOT AVAILABLE** |
| P-4 | Job state: `sas_legacy_run_daily_banking` PAUSED, 5 tasks, `max_concurrent_runs 1`, dependencies pinned | `databricks jobs get 216001923865775` (read-only) | migration identity | executable — verified 2026-09-02 (`databricks/evidence/signoff/job_216001923865775.json`) |
| P-5 | Alerting: `on_failure` webhook/e-mail wired on `sas_legacy_run_daily_banking` and `sas_legacy_recon` | `databricks notification-destinations list` non-empty; job JSON shows `on_failure` | Customer (workspace-admin) | **GAP** — list is `[]` |
| P-6 | Grants: read-only consumer group has `USE CATALOG`, `USE SCHEMA`, `SELECT` on `sas_gold` (+ `sas_silver` for C2); job run-as principal set | `SHOW GRANTS ON CATALOG sas_legacy` non-empty | Customer | **GAP** — 0 grants (G-3) |
| P-7 | Bronze feed for the cutover business date present: `sas_bronze.txn_feed_<yyyymmdd>` and refreshed Oracle snapshots (REQ-01 path) | `SELECT COUNT(*)` per bronze table vs source counts | Customer source DBA + Devin | DESK-CHECK ONLY — only the 20240131 seed exists |
| P-8 | Control-M: the `BANK_MASTER` definition is exported and version-controlled so it can be restored byte-identically (REQ-03) | export in the customer's scheduler repo | Customer scheduler team | DESK-CHECK ONLY — no export received |
| P-9 | Capital constants 50M/65M/80M confirmed as production values | requester statement recorded in `06_decisions.md` | Requester | outstanding |
| P-10 | Rollback rehearsed on paper (section 5) and the rollback operator identified | this document signed off | Requester | DESK-CHECK ONLY |

## 3. The flip

Order: C5 (alerting) → C1 (trigger) → wait one scheduled run → C2 → C3 → C4 (first month-end).

| Step | Action | Who | Rehearsal status |
|---|---|---|---|
| F-0 | Freeze: no bundle deploy to target `dev`, no code merge to the release branch, from T-24h until post-flip verification completes. Record freeze start in `05_progress.md`. | Devin (records) / Requester (enforces) | executable (procedural) |
| F-1 | Wire alerting (C5): create the notification destination, add `on_failure` to both jobs via the bundle (`databricks/resources/jobs.yml`), deploy once, verify with `jobs get`. | Customer workspace-admin (destination) + Devin (bundle PR, reviewed) | DESK-CHECK ONLY (needs workspace-admin destination) |
| F-2 | **Control-M repoint** `[CUTOVER PRINCIPAL]`: in the `BANK_MASTER` job definition, replace the SAS command step with a REST call `POST /api/2.2/jobs/run-now {"job_id": 216001923865775}` using a Control-M-held Databricks service-principal token — *or*, if the requester chose "Workflows schedule is sole trigger" (plan §1 D5 row), disable `BANK_MASTER` and rely on the job's own `0 45 5 * * ?` UTC schedule. Do not delete the legacy definition; disable it. Confirm the 05:45 timezone before this step (plan flags UTC as a placeholder). | Customer cutover principal | **DESK-CHECK ONLY** (no Control-M) |
| F-3 | **Unpause** `[CUTOVER PRINCIPAL]`: set `schedule.pause_status = UNPAUSED` on job `216001923865775` (UI or `databricks jobs update`). Only needed in the "Workflows schedule is sole trigger" variant; in the Control-M-fires variant the job stays PAUSED and Control-M's `run-now` is the only trigger. | Customer cutover principal | **DESK-CHECK ONLY** — Devin never performs this |
| F-4 | Record: flip timestamp, variant chosen (F-2), operator role (not name), job JSON after the change (scrubbed) → `databricks/evidence/cutover/`. | Devin | executable after the fact |
| F-5 | Wait for the first scheduled/Control-M-fired run; do not trigger manually. | — | — |

## 4. Post-flip verification (per consumer; all read-only; warehouse `565cd2fd713738c4`)

Run within 2 h of the first production-shaped run. `<bd>` = the cutover business date, `<ym>` = its `yyyymm`.

| Consumer | Verification | Expected | Rehearsal status |
|---|---|---|---|
| C1 trigger | `databricks jobs list-runs --job-id 216001923865775 --limit 1` → `trigger` is `PERIODIC` (schedule) or `ONE_TIME` from the Control-M SP (`run_as`/creator = SP, not a person) and `state.result_state = SUCCESS`, 5/5 tasks | first non-manual SUCCESS run | DESK-CHECK ONLY |
| C1 audit | `SELECT batch_id, step_num, status FROM sas_legacy.sas_silver.archive_batch_history WHERE batch_id LIKE 'BANK_<bd>_%' ORDER BY step_num` | 4 rows, all PASS, one batch_id | executable pattern (seed proven: 4 latest-batch rows) |
| C2 silver | `SELECT 'cust_accounts_daily', COUNT(*) FROM sas_legacy.sas_silver.cust_accounts_daily WHERE snapshot_date = DATE '<bd>' UNION ALL SELECT 'daily_transactions', COUNT(*) FROM sas_legacy.sas_silver.daily_transactions WHERE txn_date = DATE '<bd>' UNION ALL SELECT 'risk_scores', COUNT(*) FROM sas_legacy.sas_silver.risk_scores WHERE score_date = DATE '<bd>'` | counts within the D3 source volumes; then the day's `sas_legacy_recon` cycle GREEN (with REQ-05 baseline if available, else snapshot tier) | executable pattern |
| C2 readers | each named silver reader (REQ-02) runs its own query against `sas_legacy.sas_silver.*` and confirms row count = what it received from `CURATED.*` on the last SAS day, ± the day's delta | reader sign-off recorded | DESK-CHECK ONLY (readers unnamed) |
| C3 gold | `SELECT 'monthly_rwa', COUNT(*) FROM sas_legacy.sas_gold.monthly_rwa WHERE report_month = '<ym>' UNION ALL SELECT 'delinquency_aging', COUNT(*) FROM sas_legacy.sas_gold.delinquency_aging WHERE report_month = '<ym>' UNION ALL SELECT 'llp_coverage', COUNT(*) FROM sas_legacy.sas_gold.llp_coverage WHERE report_month = '<ym>' UNION ALL SELECT 'capital_adequacy', COUNT(*) FROM sas_legacy.sas_gold.capital_adequacy WHERE report_month = '<ym>' UNION ALL SELECT 'risk_summary', COUNT(*) FROM sas_legacy.sas_gold.risk_summary` | non-zero; `capital_adequacy` = 1 row; ratios non-NULL unless a denominator is zero | executable pattern |
| C4 xlsx | `databricks fs ls dbfs:/Volumes/sas_legacy/sas_bronze/landing/reports/` shows `REG_REPORT_<ym>.xlsx`; recipient opens it and confirms 3 sheets and the `capital_adequacy` figures match C3 | recipient sign-off | DESK-CHECK ONLY (recipients unnamed; content not in the recon gate) |
| C5 alerting | force nothing; confirm the destination received the run-success or has `on_failure` armed (`jobs get` shows the destination id) | armed | DESK-CHECK ONLY |
| Recon | the 06:15 `sas_legacy_recon` cycle after the run is GREEN 5/5; ledger row added | GREEN | executable once a run exists |

Any FAIL → section 5 immediately; do not wait for the next cycle.

## 5. Rollback (instant; legacy untouched)

The SAS estate, its datasets, and the Control-M definition were never modified, so rollback is only "point the trigger back".

| Step | Action | Who | Time |
|---|---|---|---|
| R-1 | `[CUTOVER PRINCIPAL]` Re-pause `sas_legacy_run_daily_banking` (`pause_status = PAUSED`); cancel any in-flight run (`databricks jobs cancel-run`). | Customer cutover principal | < 2 min |
| R-2 | `[CUTOVER PRINCIPAL]` Control-M: re-enable the original `BANK_MASTER` SAS step (restore from the P-8 export); disable the REST step. | Customer cutover principal | < 10 min |
| R-3 | If a SAS run for `<bd>` was skipped, run it via Control-M's normal "order now" — SAS inputs (Oracle/RAW_BANK) were never consumed destructively by Databricks. | Customer | per SAS runtime |
| R-4 | Consumers C2-C4 revert to `CURATED.*` / `REPORTS.*` / `&REPORT_PATH` (they were only re-pointed, never migrated). | Consumer owners | immediate |
| R-5 | Databricks side: leave `sas_legacy` as-is (evidence); do not delete the day's rows — the recon session will use them for triage. `sas_legacy_recon` stays UNPAUSED. | Devin | 0 |
| R-6 | Record: rollback timestamp, cause, run ids → `09_parallel_run_ledger.md` (new cycle row marked `ROLLBACK`) and `05_progress.md`; open a DEC row proposing the fix; notify the requester once (halt event). | Devin | same day |

Rollback needs no Devin action to be effective; Devin's part is bookkeeping.

## 6. Decommission clock

Starts only after **2 clean cutover cycles** (plan §1: D3 "legacy feed retired after 2 clean cutover cycles", D5 "Control-M job disabled after 2 clean cycles"), i.e. two consecutive scheduled production runs SUCCESS with GREEN recon and no rollback.

| Clock | Condition | Action at expiry | Owner |
|---|---|---|---|
| DC-1 | 2 clean cycles | Control-M `BANK_MASTER` SAS step deleted (not just disabled) | Customer scheduler team |
| DC-2 | 2 clean cycles + first month-end xlsx accepted by regulator recipients | legacy `&REPORT_PATH` writer stopped | Customer |
| DC-3 | 30 calendar days after DC-1 with no rollback | SAS `run_daily_banking` program and P1 datasets archived (read-only), not deleted — target-state marks decommission criteria N/A-for-demo, so this is a proposal | Customer |
| DC-4 | with DC-3 | `sas_legacy_recon` switches from daily snapshot tier to a monthly REQ-05-style spot check, or is paused by decision | Requester (DEC) |

## 7. Bookkeeping after the flip

1. `.migration/09_parallel_run_ledger.md`: window state → `CUTOVER <timestamp>`; each post-flip run a cycle row; decommission clock rows DC-1..4.
2. `.migration/05_progress.md`: P1 rows' `Cutover` column → `DONE <date>` (or `ROLLED BACK <date>`); freeze start/end.
3. `.migration/06_decisions.md`: DEC-018 "STOP E approved — cutover authorized" (or "deferred"), with the approval sentence verbatim and the variant chosen in F-2; DEC-016 resolution.
4. `.migration/04_dependency_register.md`: D5-001/002/D10-005 → CLOSED (trigger authority moved) or unchanged on rollback; D4-001/002/003 → CLOSED as consumers are verified; G-3 → CLOSED when grants exist.
5. `databricks/evidence/cutover/`: scrubbed job JSON before/after, run ids, verification query results.
6. One requester notification per event (cutover done / rollback / decommission clock start), per DEC-007.
