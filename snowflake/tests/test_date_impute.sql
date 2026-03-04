/*=====================================================================
Test Suite              : test_date_impute.sql
Tests for              : DATE_IMPUTE, DATE_IMPUTE_DATE, DATE_IMPUTE_FLAG UDFs
                         (converted from date_impute.sas)
Purpose                : Validate that the Snowflake DATE_IMPUTE UDF produces
                         the same output as the original SAS %date_impute macro.

Each test mirrors a scenario from the original SAS macro's test data.
=====================================================================*/

-- =====================================================================
-- SETUP: Create the UDFs (idempotent)
-- =====================================================================
-- Run snowflake/udfs/date_impute.sql first to create the functions.

-- =====================================================================
-- TEST SET 1: MM (numeric) month format with imputation rules
-- Mirrors the SAS data step:
--   %date_impute(in_date=date, in_y=y, in_m=m, in_d=d,
--                out_date=date_imputed, out_flag=date_imputed_flag,
--                imp_y=2026, imp_m=1, imp_d=1, month_fmt=mm)
-- =====================================================================

-- Test 1a: Full date present - no imputation needed
-- SAS input: date=20100728, y='2010', m='07', d='28'
SELECT
    'Test 1a: Full date present (MM fmt)' AS TEST_NAME,
    DATE_IMPUTE('2010-07-28'::DATE, '2010', '07', '28', 2026, 1, 1, 'MM') AS RESULT,
    FALSE AS EXPECTED_FLAG,
    CASE WHEN RESULT:imputed_flag::BOOLEAN = FALSE
          AND RESULT:imputed_date::DATE = '2010-07-28'::DATE
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- Test 1b: Date missing, all components present - imputation flag but components parse
-- SAS input: date=., y='2010', m='07', d='28'
SELECT
    'Test 1b: Date missing, components present (MM fmt)' AS TEST_NAME,
    DATE_IMPUTE(NULL, '2010', '07', '28', 2026, 1, 1, 'MM') AS RESULT,
    '2010-07-28' AS EXPECTED_DATE,
    FALSE AS EXPECTED_FLAG,
    CASE WHEN RESULT:imputed_date::VARCHAR = '2010-07-28'
          AND RESULT:imputed_flag::BOOLEAN = FALSE
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- Test 1c: Date missing, day unknown - impute day
-- SAS input: date=., y='2010', m='07', d='UK'
SELECT
    'Test 1c: Day unknown, impute to 1 (MM fmt)' AS TEST_NAME,
    DATE_IMPUTE(NULL, '2010', '07', 'UK', 2026, 1, 1, 'MM') AS RESULT,
    '2010-07-01' AS EXPECTED_DATE,
    CASE WHEN RESULT:imputed_date::VARCHAR = '2010-07-01'
          AND RESULT:imputed_flag::BOOLEAN = TRUE
          AND RESULT:day_error::BOOLEAN = TRUE
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- Test 1d: Date missing, month unknown - impute month
-- SAS input: date=., y='2010', m='UNK', d='28'
SELECT
    'Test 1d: Month unknown, impute to 1 (MM fmt)' AS TEST_NAME,
    DATE_IMPUTE(NULL, '2010', 'UNK', '28', 2026, 1, 1, 'MM') AS RESULT,
    '2010-01-28' AS EXPECTED_DATE,
    CASE WHEN RESULT:imputed_date::VARCHAR = '2010-01-28'
          AND RESULT:imputed_flag::BOOLEAN = TRUE
          AND RESULT:month_error::BOOLEAN = TRUE
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- Test 1e: Date missing, month and day unknown - impute both
-- SAS input: date=., y='2010', m='UK', d='UNK'
SELECT
    'Test 1e: Month+Day unknown (MM fmt)' AS TEST_NAME,
    DATE_IMPUTE(NULL, '2010', 'UK', 'UNK', 2026, 1, 1, 'MM') AS RESULT,
    '2010-01-01' AS EXPECTED_DATE,
    CASE WHEN RESULT:imputed_date::VARCHAR = '2010-01-01'
          AND RESULT:imputed_flag::BOOLEAN = TRUE
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- Test 1f: Year unknown - impute year with provided value
-- SAS input: date=., y='UNK', m='07', d='28'
SELECT
    'Test 1f: Year unknown, impute to 2026 (MM fmt)' AS TEST_NAME,
    DATE_IMPUTE(NULL, 'UNK', '07', '28', 2026, 1, 1, 'MM') AS RESULT,
    '2026-07-28' AS EXPECTED_DATE,
    CASE WHEN RESULT:imputed_date::VARCHAR = '2026-07-28'
          AND RESULT:imputed_flag::BOOLEAN = TRUE
          AND RESULT:year_error::BOOLEAN = TRUE
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- Test 1g: All unknown - impute everything
-- SAS input: date=., y='UNK', m='UNK', d='UNK'
SELECT
    'Test 1g: All unknown, impute all (MM fmt)' AS TEST_NAME,
    DATE_IMPUTE(NULL, 'UNK', 'UNK', 'UNK', 2026, 1, 1, 'MM') AS RESULT,
    '2026-01-01' AS EXPECTED_DATE,
    CASE WHEN RESULT:imputed_date::VARCHAR = '2026-01-01'
          AND RESULT:imputed_flag::BOOLEAN = TRUE
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- Test 1h: Year unknown, no year imputation rule (IMP_Y=NULL)
-- SAS default: imp_y=. means no imputation if year is missing
SELECT
    'Test 1h: Year unknown, no year imputation' AS TEST_NAME,
    DATE_IMPUTE(NULL, 'UNK', '07', '28', NULL, 1, 1, 'MM') AS RESULT,
    CASE WHEN RESULT:imputed_date IS NULL
          AND RESULT:imputed_flag::BOOLEAN = TRUE
          AND RESULT:year_error::BOOLEAN = TRUE
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- =====================================================================
-- TEST SET 2: MON (abbreviation) month format
-- Mirrors the SAS data step with month_fmt=mon
-- =====================================================================

-- Test 2a: Full date with MON format
SELECT
    'Test 2a: Full date (MON fmt)' AS TEST_NAME,
    DATE_IMPUTE(NULL, '2010', 'JUL', '28', 2026, 1, 1, 'MON') AS RESULT,
    '2010-07-28' AS EXPECTED_DATE,
    CASE WHEN RESULT:imputed_date::VARCHAR = '2010-07-28'
          AND RESULT:derived_month::INT = 7
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- Test 2b: Day unknown with MON format
SELECT
    'Test 2b: Day unknown (MON fmt)' AS TEST_NAME,
    DATE_IMPUTE(NULL, '2010', 'JUL', 'UK', 2026, 1, 1, 'MON') AS RESULT,
    '2010-07-01' AS EXPECTED_DATE,
    CASE WHEN RESULT:imputed_date::VARCHAR = '2010-07-01'
          AND RESULT:day_error::BOOLEAN = TRUE
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- Test 2c: Month unknown with MON format
SELECT
    'Test 2c: Month unknown (MON fmt)' AS TEST_NAME,
    DATE_IMPUTE(NULL, '2010', 'UNK', '28', 2026, 1, 1, 'MON') AS RESULT,
    '2010-01-28' AS EXPECTED_DATE,
    CASE WHEN RESULT:imputed_date::VARCHAR = '2010-01-28'
          AND RESULT:month_error::BOOLEAN = TRUE
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- Test 2d: Case-insensitive month abbreviation
SELECT
    'Test 2d: Lowercase month abbreviation' AS TEST_NAME,
    DATE_IMPUTE(NULL, '2010', 'jul', '28', 2026, 1, 1, 'MON') AS RESULT,
    '2010-07-28' AS EXPECTED_DATE,
    CASE WHEN RESULT:imputed_date::VARCHAR = '2010-07-28'
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- =====================================================================
-- TEST SET 3: Convenience wrapper functions
-- =====================================================================

-- Test 3a: DATE_IMPUTE_DATE returns DATE type
SELECT
    'Test 3a: DATE_IMPUTE_DATE wrapper' AS TEST_NAME,
    DATE_IMPUTE_DATE(NULL, '2010', '07', '28', 2026, 1, 1, 'MM') AS RESULT,
    '2010-07-28'::DATE AS EXPECTED,
    CASE WHEN DATE_IMPUTE_DATE(NULL, '2010', '07', '28', 2026, 1, 1, 'MM') = '2010-07-28'::DATE
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- Test 3b: DATE_IMPUTE_FLAG returns BOOLEAN
SELECT
    'Test 3b: DATE_IMPUTE_FLAG wrapper - no imputation' AS TEST_NAME,
    DATE_IMPUTE_FLAG('2010-07-28'::DATE, '2010', '07', '28', 2026, 1, 1, 'MM') AS RESULT,
    FALSE AS EXPECTED,
    CASE WHEN DATE_IMPUTE_FLAG('2010-07-28'::DATE, '2010', '07', '28', 2026, 1, 1, 'MM') = FALSE
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- Test 3c: DATE_IMPUTE_FLAG when imputation happens
SELECT
    'Test 3c: DATE_IMPUTE_FLAG wrapper - with imputation' AS TEST_NAME,
    DATE_IMPUTE_FLAG(NULL, '2010', 'UNK', '28', 2026, 1, 1, 'MM') AS RESULT,
    TRUE AS EXPECTED,
    CASE WHEN DATE_IMPUTE_FLAG(NULL, '2010', 'UNK', '28', 2026, 1, 1, 'MM') = TRUE
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- =====================================================================
-- TEST SET 4: Edge cases
-- =====================================================================

-- Test 4a: Invalid day (Feb 30)
SELECT
    'Test 4a: Invalid date (Feb 30)' AS TEST_NAME,
    DATE_IMPUTE(NULL, '2010', '02', '30', NULL, 1, 1, 'MM') AS RESULT,
    CASE WHEN RESULT:imputed_date IS NULL
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- Test 4b: Leap year date (Feb 29, 2020)
SELECT
    'Test 4b: Leap year (Feb 29)' AS TEST_NAME,
    DATE_IMPUTE(NULL, '2020', '02', '29', NULL, 1, 1, 'MM') AS RESULT,
    '2020-02-29' AS EXPECTED_DATE,
    CASE WHEN RESULT:imputed_date::VARCHAR = '2020-02-29'
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- =====================================================================
-- SUMMARY
-- =====================================================================
SELECT 'DATE_IMPUTE Test Summary' AS SUITE,
       COUNT(*) AS TOTAL_TESTS,
       SUM(CASE WHEN STATUS = 'PASS' THEN 1 ELSE 0 END) AS PASSED,
       SUM(CASE WHEN STATUS = 'FAIL' THEN 1 ELSE 0 END) AS FAILED
FROM (
    SELECT CASE WHEN DATE_IMPUTE('2010-07-28'::DATE, '2010', '07', '28', 2026, 1, 1, 'MM'):imputed_flag::BOOLEAN = FALSE THEN 'PASS' ELSE 'FAIL' END AS STATUS
    UNION ALL SELECT CASE WHEN DATE_IMPUTE(NULL, '2010', '07', '28', 2026, 1, 1, 'MM'):imputed_date::VARCHAR = '2010-07-28' THEN 'PASS' ELSE 'FAIL' END
    UNION ALL SELECT CASE WHEN DATE_IMPUTE(NULL, '2010', '07', 'UK', 2026, 1, 1, 'MM'):imputed_date::VARCHAR = '2010-07-01' THEN 'PASS' ELSE 'FAIL' END
    UNION ALL SELECT CASE WHEN DATE_IMPUTE(NULL, '2010', 'UNK', '28', 2026, 1, 1, 'MM'):imputed_date::VARCHAR = '2010-01-28' THEN 'PASS' ELSE 'FAIL' END
    UNION ALL SELECT CASE WHEN DATE_IMPUTE(NULL, '2010', 'UK', 'UNK', 2026, 1, 1, 'MM'):imputed_date::VARCHAR = '2010-01-01' THEN 'PASS' ELSE 'FAIL' END
    UNION ALL SELECT CASE WHEN DATE_IMPUTE(NULL, 'UNK', '07', '28', 2026, 1, 1, 'MM'):imputed_date::VARCHAR = '2026-07-28' THEN 'PASS' ELSE 'FAIL' END
    UNION ALL SELECT CASE WHEN DATE_IMPUTE(NULL, 'UNK', 'UNK', 'UNK', 2026, 1, 1, 'MM'):imputed_date::VARCHAR = '2026-01-01' THEN 'PASS' ELSE 'FAIL' END
    UNION ALL SELECT CASE WHEN DATE_IMPUTE(NULL, 'UNK', '07', '28', NULL, 1, 1, 'MM'):imputed_date IS NULL THEN 'PASS' ELSE 'FAIL' END
    UNION ALL SELECT CASE WHEN DATE_IMPUTE(NULL, '2010', 'JUL', '28', 2026, 1, 1, 'MON'):imputed_date::VARCHAR = '2010-07-28' THEN 'PASS' ELSE 'FAIL' END
    UNION ALL SELECT CASE WHEN DATE_IMPUTE(NULL, '2010', 'JUL', 'UK', 2026, 1, 1, 'MON'):imputed_date::VARCHAR = '2010-07-01' THEN 'PASS' ELSE 'FAIL' END
    UNION ALL SELECT CASE WHEN DATE_IMPUTE(NULL, '2020', '02', '29', NULL, 1, 1, 'MM'):imputed_date::VARCHAR = '2020-02-29' THEN 'PASS' ELSE 'FAIL' END
);
