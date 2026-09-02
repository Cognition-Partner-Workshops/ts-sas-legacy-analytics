CREATE CATALOG IF NOT EXISTS sas_legacy;
CREATE SCHEMA IF NOT EXISTS sas_legacy.sas_bronze;
CREATE SCHEMA IF NOT EXISTS sas_legacy.sas_silver;
CREATE SCHEMA IF NOT EXISTS sas_legacy.sas_gold;
CREATE SCHEMA IF NOT EXISTS sas_legacy.sas_ref;
CREATE SCHEMA IF NOT EXISTS sas_legacy.sas_recon;
CREATE VOLUME IF NOT EXISTS sas_legacy.sas_bronze.landing;
