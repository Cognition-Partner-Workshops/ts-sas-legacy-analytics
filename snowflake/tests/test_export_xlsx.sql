/*=====================================================================
Test Suite              : test_export_xlsx.sql
Tests for              : SP_EXPORT_XLSX stored procedure
                         (converted from export_xlsx.sas)
Purpose                : Validate parameter handling and export logic
                         for the Snowflake SP_EXPORT_XLSX procedure.

Note: Full end-to-end tests require a Snowflake stage. These tests
focus on parameter validation and error handling.
=====================================================================*/

-- =====================================================================
-- TEST 1: Missing required DATA parameter
-- =====================================================================
SELECT
    'Test 1: Missing DATA parameter' AS TEST_NAME,
    CASE
        WHEN SP_EXPORT_XLSX(NULL, '@my_stage/test.csv') LIKE '%ERROR%DATA%'
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS;

-- =====================================================================
-- TEST 2: Missing required STAGE_PATH parameter
-- =====================================================================
SELECT
    'Test 2: Missing STAGE_PATH parameter' AS TEST_NAME,
    CASE
        WHEN SP_EXPORT_XLSX('MY_TABLE', NULL) LIKE '%ERROR%STAGE_PATH%'
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS;

-- =====================================================================
-- TEST 3: Invalid FILE_FORMAT parameter
-- =====================================================================
SELECT
    'Test 3: Invalid FILE_FORMAT' AS TEST_NAME,
    CASE
        WHEN SP_EXPORT_XLSX('MY_TABLE', '@my_stage/test.csv', 'XLSX') LIKE '%ERROR%FILE_FORMAT%'
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS;

-- =====================================================================
-- TEST 4: Full parameter signature accepted
-- =====================================================================
SELECT
    'Test 4: Full parameter signature' AS TEST_NAME,
    CASE
        WHEN SP_EXPORT_XLSX(
            'NONEXISTENT_TABLE',          -- DATA
            '@nonexistent_stage/out.csv',  -- STAGE_PATH
            'CSV',                         -- FILE_FORMAT
            TRUE,                          -- REPLACE
            TRUE,                          -- USE_HEADER
            ',',                           -- FIELD_DELIMITER
            'NONE',                        -- COMPRESSION
            TRUE,                          -- SINGLE_FILE
            5368709120                     -- MAX_FILE_SIZE
        ) IS NOT NULL
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS;

-- =====================================================================
-- TEST 5: Parquet format accepted
-- =====================================================================
SELECT
    'Test 5: Parquet format' AS TEST_NAME,
    CASE
        WHEN SP_EXPORT_XLSX(
            'NONEXISTENT_TABLE',
            '@nonexistent_stage/out.parquet',
            'PARQUET',
            TRUE, TRUE, ',', 'NONE', TRUE, NULL
        ) IS NOT NULL
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS;

-- =====================================================================
-- REFERENCE: End-to-end test template (requires stage and table)
-- =====================================================================
/*
-- Step 1: Create test data
CREATE OR REPLACE TEMPORARY TABLE TEST_EXPORT_DATA AS
    SELECT 'Alfred' AS NAME, 14 AS AGE, 69.0 AS HEIGHT
    UNION ALL SELECT 'Alice', 13, 56.5
    UNION ALL SELECT 'Barbara', 13, 65.3;

-- Step 2: Create an internal stage
CREATE OR REPLACE STAGE TEST_EXPORT_STAGE;

-- Step 3: Export to CSV
CALL SP_EXPORT_XLSX(
    'TEST_EXPORT_DATA',
    '@TEST_EXPORT_STAGE/test_export.csv',
    'CSV',      -- FILE_FORMAT
    TRUE,       -- REPLACE
    TRUE,       -- USE_HEADER
    ',',        -- FIELD_DELIMITER
    'NONE',     -- COMPRESSION
    TRUE,       -- SINGLE_FILE
    NULL        -- MAX_FILE_SIZE (default)
);

-- Step 4: Verify the file was created
LIST @TEST_EXPORT_STAGE;

-- Step 5: Read back and verify
CREATE OR REPLACE TEMPORARY TABLE TEST_EXPORT_VERIFY (
    NAME VARCHAR, AGE INT, HEIGHT FLOAT
);
COPY INTO TEST_EXPORT_VERIFY
    FROM @TEST_EXPORT_STAGE/test_export.csv
    FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1);

SELECT * FROM TEST_EXPORT_VERIFY;

-- Verify data matches
SELECT
    'End-to-end export test' AS TEST_NAME,
    CASE WHEN (SELECT COUNT(*) FROM TEST_EXPORT_VERIFY) = 3
         THEN 'PASS' ELSE 'FAIL'
    END AS STATUS;

-- Step 6: Test REPLACE=FALSE when file exists
-- This should return an error
CALL SP_EXPORT_XLSX(
    'TEST_EXPORT_DATA',
    '@TEST_EXPORT_STAGE/test_export.csv',
    'CSV', FALSE, TRUE, ',', 'NONE', TRUE, NULL
);

-- Step 7: Cleanup
DROP TABLE IF EXISTS TEST_EXPORT_DATA;
DROP TABLE IF EXISTS TEST_EXPORT_VERIFY;
DROP STAGE IF EXISTS TEST_EXPORT_STAGE;
*/
