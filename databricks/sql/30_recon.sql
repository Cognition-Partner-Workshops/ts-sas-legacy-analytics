CREATE TABLE IF NOT EXISTS sas_legacy.sas_recon.run_log (
  run_id                    STRING,
  run_ts                    TIMESTAMP,
  unit                      STRING,
  business_date             DATE,
  mode                      STRING,
  tolerances_version        STRING,
  reference_manifest_sha256 STRING,
  overall                   STRING,
  n_pass                    INT,
  n_fail                    INT,
  n_na                      INT,
  statements                INT,
  elapsed_s                 DOUBLE,
  summary                   STRING
) USING DELTA
COMMENT 'Recon harness run log (databricks/recon/run_recon.py). mode is always DEGRADED until SAS-produced references exist.';
