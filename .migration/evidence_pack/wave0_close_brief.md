# Wave 0 close brief — P1 banking-core (2026-09-01)

**Landed.** PR #27 (W0-R independent Python reference, 14 tables, 28 self-checks, 13 ambiguities) and PR #28 (W0-A: catalog `sas_legacy`, 5 schemas, volume, 9 bronze tables = manifest, 9 `sas_ref.fmt_*` + registry, `sas_macros` pkg, bundle with `sas_legacy_run_daily_banking` PAUSED + `sas_legacy_recon`, recon harness T-1..12/ML-1..8, CI workflow) merged into `migration/02-analysis-plan`. No legacy source changed; no clusters; no writes outside `sas_legacy`.

**Decided.** D2-001 macro closure mapping implemented as planned. Wave-0 targets registered before load; no collision.

**Broke / implies.** Two children rediscovered the env-var shadowing trap (`DATABRICKS_HOST` vs `_DEMO_`) — added to hand-off preflight. W0-R found five source ambiguities that change output shapes vs the analysis §6 (AMB-01/02/03/07/12) → DEC-015 needed before the wave-1 recon gate; U1 is directly affected (acct_exceptions shape).

**Unproven.** No live recon executed yet (reference absent when harness was built). GitHub Actions produced no check runs on #27/#28 — repo Actions appear disabled/restricted (owner requester; gates verified locally). Repo secrets for CI bundle-validate unknown. `_manifest.sha256` is local-file SHA.

**Cost.** W0-A 10.1 ACU, ~30 short warehouse statements, 0 job runs. W0-R 13.9 ACU, no Databricks usage. Orchestrator ≈ 2 ACU this wave.
