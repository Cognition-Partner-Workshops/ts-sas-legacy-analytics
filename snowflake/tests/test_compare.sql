/*=====================================================================
Test Suite              : test_compare.sql
Tests for              : SP_COMPARE stored procedure
                         (converted from compare.sas)
Purpose                : Validate that the Snowflake SP_COMPARE procedure
                         produces equivalent comparison reports to the
                         original SAS %compare macro (PROC COMPARE).

Test approach:
  1. Create test tables mirroring the SAS test data (sashelp.class)
  2. Run the stored procedure
  3. Verify the output report contains expected comparison results
=====================================================================*/

-- =====================================================================
-- SETUP: Create test tables
-- =====================================================================

-- Base table (mirrors SAS sashelp.class)
CREATE OR REPLACE TEMPORARY TABLE TEST_COMPARE_BASE (
    NAME    VARCHAR(20),
    SEX     VARCHAR(1),
    AGE     INT,
    HEIGHT  FLOAT,
    WEIGHT  FLOAT
);

INSERT INTO TEST_COMPARE_BASE VALUES
    ('Alfred',  'M', 14, 69.0, 112.5),
    ('Alice',   'F', 13, 56.5,  84.0),
    ('Barbara', 'F', 13, 65.3,  98.0),
    ('Carol',   'F', 14, 62.8, 102.5),
    ('Henry',   'M', 14, 63.5, 102.5),
    ('James',   'M', 12, 57.3,  83.0),
    ('Jane',    'F', 12, 59.8,  84.5),
    ('Janet',   'F', 15, 62.5, 112.5),
    ('Jeffrey', 'M', 13, 62.5,  84.0),
    ('John',    'M', 12, 59.0,  99.5),
    ('Joyce',   'F', 11, 51.3,  50.5),
    ('Judy',    'F', 14, 64.3,  90.0),
    ('Louise',  'F', 12, 56.3,  77.0),
    ('Mary',    'F', 15, 66.5, 112.0),
    ('Philip',  'M', 16, 72.0, 150.0),
    ('Robert',  'M', 12, 64.8, 128.0),
    ('Ronald',  'M', 15, 67.0, 133.0),
    ('Thomas',  'M', 11, 57.5,  85.0),
    ('William', 'M', 15, 66.5, 112.0);

-- Compare table: same as base but with modifications
-- SAS: if name="John" then age=99; drop sex; label age="Age";
CREATE OR REPLACE TEMPORARY TABLE TEST_COMPARE_COMP (
    NAME    VARCHAR(20),
    AGE     INT,
    HEIGHT  FLOAT,
    WEIGHT  FLOAT
);

INSERT INTO TEST_COMPARE_COMP
    SELECT NAME, CASE WHEN NAME = 'John' THEN 99 ELSE AGE END, HEIGHT, WEIGHT
    FROM TEST_COMPARE_BASE;

-- =====================================================================
-- TEST 1: Table comparison with key column
-- SAS: %compare(base=base, comp=comp, by=name)
-- Should detect: SEX column only in BASE, AGE difference for John
-- =====================================================================
CALL SP_COMPARE(
    'TEST_COMPARE_BASE',
    'TEST_COMPARE_COMP',
    'NAME',          -- KEY_COLUMNS
    NULL,            -- FILTER_PATTERN
    50,              -- MAX_DIFF
    0.000001,        -- CRITERION
    'EXACT'          -- METHOD
);

-- Verify the output contains expected elements
-- (In practice, the CALL returns a VARCHAR report)
SELECT
    'Test 1: Table comparison with key' AS TEST_NAME,
    CASE
        WHEN result LIKE '%Column Structure%'
         AND result LIKE '%SEX%'
         AND result LIKE '%Data Differences%'
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS
FROM (
    SELECT SP_COMPARE(
        'TEST_COMPARE_BASE', 'TEST_COMPARE_COMP', 'NAME',
        NULL, 50, 0.000001, 'EXACT'
    ) AS result
);

-- =====================================================================
-- TEST 2: Table comparison without key columns (EXCEPT-based)
-- SAS: %compare(base=base, comp=comp) - no BY variable
-- =====================================================================
SELECT
    'Test 2: Table comparison without key (EXCEPT)' AS TEST_NAME,
    CASE
        WHEN result LIKE '%EXCEPT%'
         AND result LIKE '%Row counts%'
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS
FROM (
    SELECT SP_COMPARE(
        'TEST_COMPARE_BASE', 'TEST_COMPARE_COMP', NULL,
        NULL, 50, 0.000001, 'EXACT'
    ) AS result
);

-- =====================================================================
-- TEST 3: Identical tables should show no differences
-- =====================================================================
CREATE OR REPLACE TEMPORARY TABLE TEST_COMPARE_IDENTICAL AS
    SELECT * FROM TEST_COMPARE_BASE;

SELECT
    'Test 3: Identical tables - no differences' AS TEST_NAME,
    CASE
        WHEN result LIKE '%No differences%' OR result LIKE '%MATCH%'
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS
FROM (
    SELECT SP_COMPARE(
        'TEST_COMPARE_BASE', 'TEST_COMPARE_IDENTICAL', 'NAME',
        NULL, 50, 0.000001, 'EXACT'
    ) AS result
);

-- =====================================================================
-- TEST 4: Error handling - mismatched types
-- =====================================================================
SELECT
    'Test 4: Error on non-existent table' AS TEST_NAME,
    CASE
        WHEN result LIKE '%ERROR%'
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS
FROM (
    SELECT SP_COMPARE(
        'NON_EXISTENT_TABLE_ABC', 'NON_EXISTENT_TABLE_DEF', NULL,
        NULL, 50, 0.000001, 'EXACT'
    ) AS result
);

-- =====================================================================
-- TEST 5: Validate parameter checking
-- =====================================================================
SELECT
    'Test 5: Missing BASE parameter' AS TEST_NAME,
    CASE
        WHEN SP_COMPARE(NULL, 'TEST_COMPARE_COMP') LIKE '%ERROR%BASE%'
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS;

SELECT
    'Test 5b: Invalid METHOD' AS TEST_NAME,
    CASE
        WHEN SP_COMPARE('TEST_COMPARE_BASE', 'TEST_COMPARE_COMP',
                         NULL, NULL, 50, 0.000001, 'INVALID') LIKE '%ERROR%METHOD%'
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS;

-- =====================================================================
-- CLEANUP
-- =====================================================================
DROP TABLE IF EXISTS TEST_COMPARE_BASE;
DROP TABLE IF EXISTS TEST_COMPARE_COMP;
DROP TABLE IF EXISTS TEST_COMPARE_IDENTICAL;
