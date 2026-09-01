"""Reconciliation harness for the sas_legacy migration.

Compares Databricks target tables against the W0-R reference CSVs
(`docs/migration/recon/reference/`) under the tolerance contract in
`.migration/03_recon_tolerances.md` (v1). Recon mode is DEGRADED:
every verdict carries the caveat "reference-derived, not SAS-produced".
"""

TOLERANCES_VERSION = "v1"
RECON_MODE = "DEGRADED"
CAVEAT = "reference-derived, not SAS-produced"
