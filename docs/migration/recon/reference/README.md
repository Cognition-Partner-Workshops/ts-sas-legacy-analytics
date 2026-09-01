# P1 banking-core reference outputs (W0-R)

**Caveat: reference-derived, not SAS-produced.** No SAS runtime exists in this environment
(recon mode DEGRADED, DEC-004 option b). These 14 CSVs were computed by an independent, literal
Python re-expression of the SAS programs (`../reference_impl/`), written from the SAS source only,
against the pinned seed snapshot `Data/csv/**` (9 files, sha256 in `manifest.json`, verified against
`.migration/05_progress.md`). Results describe the snapshot, not production. Tolerance record: v1.

## Regenerate

```bash
pip install pandas pytest            # stdlib + pandas only
cd docs/migration/recon
python -m reference_impl.run_all --business-date 2024-01-31 --report-month 202401
python -m pytest reference_impl/tests -q
```

Regeneration is byte-identical (checked by the tests). Business date `31JAN2024`, `PREV_YM=202401`,
`region=ALL`, model `CRM-2023-Q4-v2`, batch id sentinel `BANK_20240131_000000`.

## Conventions

- One CSV per table in analysis §6, lower_snake column names (SAS names lower-cased), ISO dates,
  missing = empty field, integral numbers without decimals, other numbers as shortest round-trip repr.
- Run-time columns (`load_timestamp`, `score_timestamp`, `start_time`, `end_time`) = `2024-01-31T00:00:00`,
  `duration` = `0`; exception rows keep the literal missing `snapshot_date`/`load_timestamp` (AMB-05).
- Rows sorted by the §6 T-2 key (`monthly_rwa` adds `risk_weight`, AMB-07).
- `manifest.json`: per-file rows + sha256, input manifest, source commit, generator command, caveat.

## Ambiguities (13, see `../reference_impl/AMBIGUITIES.md`)

The reference always implements the literal Base SAS reading. Three of them change table shapes and
need a decision before the recon gate can use T-9: the `DROP` statement in a multi-output DATA step
removes `EXCEPTION_CODE`/`EXCEPTION_DESC` and `REJECT_REASON` from the exception/reject tables
(AMB-01/02), and `PROC APPEND … FORCE` keeps `daily_transactions` at the 10 history columns (AMB-03).
The intended-reading variants are in `alternates/` (not part of the 14 reference tables). Also
notable: SAS missing sorts low, so `. < 0` is true (orphan accounts → `OVERDRAFT`, AMB-06); MTG loans
with missing LTV take risk weight 1.00 (AMB-07); anomaly statistics use pre-append history with
sample std (AMB-13). `alternates/risk_scores__woe_debug.csv` holds the ML-8 `woe_*` features.
