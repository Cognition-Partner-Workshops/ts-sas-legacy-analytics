CREATE OR REPLACE TABLE sas_legacy.sas_bronze.cust_accounts AS
SELECT
  CAST(ACCOUNT_ID AS STRING) AS account_id,
  CAST(CUSTOMER_ID AS STRING) AS customer_id,
  CAST(ACCOUNT_TYPE AS STRING) AS account_type,
  CAST(ACCOUNT_STATUS AS STRING) AS account_status,
  TO_DATE(NULLIF(OPEN_DATE, ''), 'ddMMMyyyy') AS open_date,
  TO_DATE(NULLIF(CLOSE_DATE, ''), 'ddMMMyyyy') AS close_date,
  CAST(NULLIF(CURRENT_BALANCE, '') AS DECIMAL(18, 2)) AS current_balance,
  CAST(NULLIF(AVAILABLE_BALANCE, '') AS DECIMAL(18, 2)) AS available_balance,
  CAST(NULLIF(CREDIT_LIMIT, '') AS DECIMAL(18, 2)) AS credit_limit,
  CAST(NULLIF(INTEREST_RATE, '') AS DOUBLE) AS interest_rate,
  CAST(BRANCH_ID AS STRING) AS branch_id,
  CAST(OFFICER_ID AS STRING) AS officer_id,
  TO_DATE(NULLIF(LAST_ACTIVITY_DATE, ''), 'ddMMMyyyy') AS last_activity_date
FROM READ_FILES(
  '/Volumes/sas_legacy/sas_bronze/landing/seed/CUST_ACCOUNTS.csv',
  FORMAT => 'csv',
  HEADER => true,
  inferSchema => false,
  NULLVALUE => ''
);

CREATE OR REPLACE TABLE sas_legacy.sas_bronze.cust_demographics AS
SELECT
  CAST(CUSTOMER_ID AS STRING) AS customer_id,
  CAST(FIRST_NAME AS STRING) AS first_name,
  CAST(LAST_NAME AS STRING) AS last_name,
  CAST(SSN_HASH AS STRING) AS ssn_hash,
  TO_DATE(NULLIF(DATE_OF_BIRTH, ''), 'ddMMMyyyy') AS date_of_birth,
  CAST(CUSTOMER_SEGMENT AS STRING) AS customer_segment,
  CAST(NULLIF(RISK_RATING, '') AS INT) AS risk_rating,
  CAST(REGION_CODE AS STRING) AS region_code,
  CAST(PRIMARY_EMAIL AS STRING) AS primary_email,
  CAST(PHONE_NUMBER AS STRING) AS phone_number
FROM READ_FILES(
  '/Volumes/sas_legacy/sas_bronze/landing/seed/CUST_DEMOGRAPHICS.csv',
  FORMAT => 'csv',
  HEADER => true,
  inferSchema => false,
  NULLVALUE => ''
);

CREATE OR REPLACE TABLE sas_legacy.sas_bronze.bureau_scores AS
SELECT
  CAST(CUSTOMER_ID AS STRING) AS customer_id,
  TO_DATE(NULLIF(SCORE_DATE, ''), 'ddMMMyyyy') AS score_date,
  CAST(NULLIF(FICO_SCORE, '') AS INT) AS fico_score,
  CAST(NULLIF(VANTAGE_SCORE, '') AS INT) AS vantage_score,
  CAST(NULLIF(BUREAU_INQS_6MO, '') AS INT) AS bureau_inqs_6mo,
  CAST(NULLIF(BUREAU_TRADES_OPEN, '') AS INT) AS bureau_trades_open,
  CAST(NULLIF(BUREAU_DEROGS, '') AS INT) AS bureau_derogs,
  CAST(NULLIF(BUREAU_UTIL_PCT, '') AS DOUBLE) AS bureau_util_pct,
  CAST(NULLIF(BUREAU_OLDEST_TRADE_MO, '') AS INT) AS bureau_oldest_trade_mo
FROM READ_FILES(
  '/Volumes/sas_legacy/sas_bronze/landing/seed/BUREAU_SCORES.csv',
  FORMAT => 'csv',
  HEADER => true,
  inferSchema => false,
  NULLVALUE => ''
);

CREATE OR REPLACE TABLE sas_legacy.sas_bronze.payment_history AS
SELECT
  CAST(ACCOUNT_ID AS STRING) AS account_id,
  CAST(NULLIF(PMT_ONTIME_12MO, '') AS INT) AS pmt_ontime_12mo,
  CAST(NULLIF(PMT_LATE_30_12MO, '') AS INT) AS pmt_late_30_12mo,
  CAST(NULLIF(PMT_LATE_60_12MO, '') AS INT) AS pmt_late_60_12mo,
  CAST(NULLIF(PMT_LATE_90_12MO, '') AS INT) AS pmt_late_90_12mo,
  CAST(NULLIF(MAX_DAYS_PAST_DUE_EVER, '') AS INT) AS max_days_past_due_ever,
  CAST(NULLIF(MONTHS_SINCE_LAST_DPD, '') AS INT) AS months_since_last_dpd,
  CAST(NULLIF(AVG_PMT_RATIO_12MO, '') AS DOUBLE) AS avg_pmt_ratio_12mo
FROM READ_FILES(
  '/Volumes/sas_legacy/sas_bronze/landing/seed/PAYMENT_HISTORY.csv',
  FORMAT => 'csv',
  HEADER => true,
  inferSchema => false,
  NULLVALUE => ''
);

CREATE OR REPLACE TABLE sas_legacy.sas_bronze.collateral AS
SELECT
  CAST(ACCOUNT_ID AS STRING) AS account_id,
  CAST(NULLIF(COLLATERAL_VALUE, '') AS DECIMAL(18, 2)) AS collateral_value,
  TO_DATE(NULLIF(LAST_APPRAISAL_DATE, ''), 'ddMMMyyyy') AS last_appraisal_date
FROM READ_FILES(
  '/Volumes/sas_legacy/sas_bronze/landing/seed/COLLATERAL.csv',
  FORMAT => 'csv',
  HEADER => true,
  inferSchema => false,
  NULLVALUE => ''
);

CREATE OR REPLACE TABLE sas_legacy.sas_bronze.loan_details AS
SELECT
  CAST(ACCOUNT_ID AS STRING) AS account_id,
  CAST(LOAN_PURPOSE AS STRING) AS loan_purpose,
  CAST(NULLIF(ORIG_AMOUNT, '') AS DECIMAL(18, 2)) AS orig_amount,
  TO_DATE(NULLIF(ORIG_DATE, ''), 'ddMMMyyyy') AS orig_date,
  CAST(NULLIF(TERM_MONTHS, '') AS INT) AS term_months,
  CAST(NULLIF(LTV, '') AS DOUBLE) AS ltv,
  CAST(NULLIF(DAYS_PAST_DUE, '') AS INT) AS days_past_due,
  CAST(NULLIF(PAST_DUE_AMOUNT, '') AS DECIMAL(18, 2)) AS past_due_amount,
  CAST(NULLIF(ALLOWANCE_AMT, '') AS DECIMAL(18, 2)) AS allowance_amt
FROM READ_FILES(
  '/Volumes/sas_legacy/sas_bronze/landing/seed/LOAN_DETAILS.csv',
  FORMAT => 'csv',
  HEADER => true,
  inferSchema => false,
  NULLVALUE => ''
);

CREATE OR REPLACE TABLE sas_legacy.sas_bronze.daily_rates AS
SELECT
  TO_DATE(NULLIF(RATE_DATE, ''), 'ddMMMyyyy') AS rate_date,
  CAST(RATE_TYPE AS STRING) AS rate_type,
  CAST(NULLIF(RATE_VALUE, '') AS DOUBLE) AS rate_value
FROM READ_FILES(
  '/Volumes/sas_legacy/sas_bronze/landing/seed/DAILY_RATES.csv',
  FORMAT => 'csv',
  HEADER => true,
  inferSchema => false,
  NULLVALUE => ''
);

CREATE OR REPLACE TABLE sas_legacy.sas_bronze.txn_feed_20240131 AS
SELECT
  CAST(TRANSACTION_ID AS STRING) AS transaction_id,
  CAST(ACCOUNT_ID AS STRING) AS account_id,
  TO_DATE(NULLIF(TRANSACTION_DATE, ''), 'ddMMMyyyy') AS transaction_date,
  CAST(TRANSACTION_TYPE AS STRING) AS transaction_type,
  CAST(NULLIF(TRANSACTION_AMOUNT, '') AS DECIMAL(18, 2)) AS transaction_amount,
  CAST(CHANNEL AS STRING) AS channel,
  CAST(MERCHANT_CATEGORY AS STRING) AS merchant_category,
  CAST(DESCRIPTION AS STRING) AS description,
  TO_DATE(NULLIF(POST_DATE, ''), 'ddMMMyyyy') AS post_date,
  CAST(CURRENCY_CODE AS STRING) AS currency_code
FROM READ_FILES(
  '/Volumes/sas_legacy/sas_bronze/landing/seed/TXN_FEED_20240131.csv',
  FORMAT => 'csv',
  HEADER => true,
  inferSchema => false,
  NULLVALUE => ''
);

CREATE OR REPLACE TABLE sas_legacy.sas_bronze.daily_transactions_hist AS
SELECT
  CAST(TRANSACTION_ID AS STRING) AS transaction_id,
  CAST(ACCOUNT_ID AS STRING) AS account_id,
  TO_DATE(NULLIF(TRANSACTION_DATE, ''), 'ddMMMyyyy') AS transaction_date,
  CAST(TRANSACTION_TYPE AS STRING) AS transaction_type,
  CAST(NULLIF(TRANSACTION_AMOUNT, '') AS DECIMAL(18, 2)) AS transaction_amount,
  CAST(CHANNEL AS STRING) AS channel,
  CAST(MERCHANT_CATEGORY AS STRING) AS merchant_category,
  CAST(DESCRIPTION AS STRING) AS description,
  TO_DATE(NULLIF(POST_DATE, ''), 'ddMMMyyyy') AS post_date,
  CAST(CURRENCY_CODE AS STRING) AS currency_code
FROM READ_FILES(
  '/Volumes/sas_legacy/sas_bronze/landing/seed/DAILY_TRANSACTIONS.csv',
  FORMAT => 'csv',
  HEADER => true,
  inferSchema => false,
  NULLVALUE => ''
);

CREATE OR REPLACE TABLE sas_legacy.sas_bronze._manifest (
  file STRING,
  rows BIGINT,
  sha256 STRING,
  business_date DATE,
  source_commit STRING,
  loaded_at TIMESTAMP
);
