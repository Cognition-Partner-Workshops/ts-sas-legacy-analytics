/*=====================================================================
Test Suite              : test_create_table_or_view.sql
Tests for              : SP_CREATE_TABLE_OR_VIEW stored procedure
                         (converted from CreateTableOrView.sas)
Purpose                : Validate that the Snowflake SP_CREATE_TABLE_OR_VIEW
                         procedure correctly creates tables and views with
                         column selection, filtering, ordering, and renaming.
=====================================================================*/

-- =====================================================================
-- SETUP: Create source test table (mirrors SAS sashelp.shoes)
-- =====================================================================
CREATE OR REPLACE TEMPORARY TABLE TEST_SHOES (
    REGION      VARCHAR(50),
    SUBSIDIARY  VARCHAR(50),
    PRODUCT     VARCHAR(50),
    STORES      INT,
    SALES       FLOAT,
    INVENTORY   FLOAT,
    RETURNS     FLOAT
);

INSERT INTO TEST_SHOES VALUES
    ('United States', 'New York',     'Boot',     22, 1220.00, 4520.00, 235.00),
    ('United States', 'Los Angeles',  'Sandal',   18,  980.00, 3200.00, 122.00),
    ('United States', 'Chicago',      'Slipper',  25,  430.00, 1800.00,  58.00),
    ('Canada',        'Toronto',      'Boot',     15,  890.00, 2900.00, 145.00),
    ('Canada',        'Vancouver',    'Sandal',   12,  560.00, 1900.00,  89.00),
    ('Africa',        'Cairo',        'Boot',      8,  320.00, 1100.00,  42.00),
    ('Europe',        'London',       'Slipper',  30, 1560.00, 5200.00, 278.00),
    ('Europe',        'Paris',        'Boot',     28, 1340.00, 4800.00, 198.00),
    ('Asia',          'Tokyo',        'Sandal',   20,  760.00, 2400.00,  98.00);

-- =====================================================================
-- TEST 1: Basic table creation (all columns)
-- SAS: %CreateTableOrView(data=sashelp.shoes, out=work.shoes)
-- =====================================================================
CALL SP_CREATE_TABLE_OR_VIEW(
    'TEST_SHOES',           -- DATA
    'TEST_OUTPUT_1',        -- OUT
    NULL,                   -- KEEP_COLS
    NULL,                   -- DROP_COLS
    NULL,                   -- ORDER_BY
    NULL,                   -- WHERE_CLAUSE
    NULL,                   -- RENAME_MAP
    'TABLE',                -- OBJ_TYPE
    TRUE                    -- REPLACE_OBJ
);

SELECT
    'Test 1: Basic table creation' AS TEST_NAME,
    CASE
        WHEN (SELECT COUNT(*) FROM TEST_OUTPUT_1) = 9
         AND (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
              WHERE TABLE_NAME = 'TEST_OUTPUT_1') = 7
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS;

-- =====================================================================
-- TEST 2: Table with KEEP (column selection)
-- SAS: %CreateTableOrView(data=sashelp.shoes, out=work.shoes,
--          keep=Region Subsidiary Product Stores Sales)
-- =====================================================================
CALL SP_CREATE_TABLE_OR_VIEW(
    'TEST_SHOES',
    'TEST_OUTPUT_2',
    'REGION,SUBSIDIARY,PRODUCT,STORES,SALES',   -- KEEP_COLS
    NULL, NULL, NULL, NULL, 'TABLE', TRUE
);

SELECT
    'Test 2: KEEP columns' AS TEST_NAME,
    CASE
        WHEN (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
              WHERE TABLE_NAME = 'TEST_OUTPUT_2') = 5
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS;

-- =====================================================================
-- TEST 3: Table with DROP
-- SAS: %CreateTableOrView(data=sashelp.shoes, out=work.shoes,
--          drop=Stores Inventory Returns)
-- =====================================================================
CALL SP_CREATE_TABLE_OR_VIEW(
    'TEST_SHOES',
    'TEST_OUTPUT_3',
    NULL,                                        -- KEEP_COLS
    'STORES,INVENTORY,RETURNS',                  -- DROP_COLS
    NULL, NULL, NULL, 'TABLE', TRUE
);

SELECT
    'Test 3: DROP columns' AS TEST_NAME,
    CASE
        WHEN (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
              WHERE TABLE_NAME = 'TEST_OUTPUT_3') = 4
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS;

-- =====================================================================
-- TEST 4: Table with WHERE filter
-- SAS: %CreateTableOrView(data=sashelp.shoes, out=work.shoes,
--          where=Region in ("United States", "Canada"))
-- =====================================================================
CALL SP_CREATE_TABLE_OR_VIEW(
    'TEST_SHOES',
    'TEST_OUTPUT_4',
    NULL, NULL, NULL,
    'REGION IN (''United States'', ''Canada'')',  -- WHERE_CLAUSE
    NULL, 'TABLE', TRUE
);

SELECT
    'Test 4: WHERE filter' AS TEST_NAME,
    CASE
        WHEN (SELECT COUNT(*) FROM TEST_OUTPUT_4) = 5
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS;

-- =====================================================================
-- TEST 5: Table with ORDER BY (ascending)
-- SAS: %CreateTableOrView(data=sashelp.shoes, out=work.shoes,
--          by=Region Subsidiary Product)
-- =====================================================================
CALL SP_CREATE_TABLE_OR_VIEW(
    'TEST_SHOES',
    'TEST_OUTPUT_5',
    NULL, NULL,
    'REGION,SUBSIDIARY,PRODUCT',                 -- ORDER_BY
    NULL, NULL, 'TABLE', TRUE
);

SELECT
    'Test 5: ORDER BY ascending' AS TEST_NAME,
    CASE
        WHEN (SELECT REGION FROM TEST_OUTPUT_5 LIMIT 1) = 'Africa'
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS;

-- =====================================================================
-- TEST 6: Table with ORDER BY descending (using minus prefix)
-- SAS: %CreateTableOrView(data=sashelp.shoes, out=work.shoes,
--          by=Region Subsidiary -Sales)
-- =====================================================================
CALL SP_CREATE_TABLE_OR_VIEW(
    'TEST_SHOES',
    'TEST_OUTPUT_6',
    'REGION,SUBSIDIARY,SALES',
    NULL,
    'REGION,-SALES',                             -- ORDER_BY (descending on SALES)
    NULL, NULL, 'TABLE', TRUE
);

SELECT
    'Test 6: ORDER BY with descending' AS TEST_NAME,
    CASE
        WHEN (SELECT COUNT(*) FROM TEST_OUTPUT_6) = 9
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS;

-- =====================================================================
-- TEST 7: Table with RENAME
-- SAS: %CreateTableOrView(data=sashelp.shoes, out=work.shoes,
--          rename=Sales=TotalSales Region=Country)
-- =====================================================================
CALL SP_CREATE_TABLE_OR_VIEW(
    'TEST_SHOES',
    'TEST_OUTPUT_7',
    NULL, 'STORES,INVENTORY,RETURNS', NULL, NULL,
    'SALES=TotalSales,REGION=Country',           -- RENAME_MAP
    'TABLE', TRUE
);

SELECT
    'Test 7: RENAME columns' AS TEST_NAME,
    CASE
        WHEN EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                     WHERE TABLE_NAME = 'TEST_OUTPUT_7' AND COLUMN_NAME = 'TotalSales')
         AND EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                     WHERE TABLE_NAME = 'TEST_OUTPUT_7' AND COLUMN_NAME = 'Country')
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS;

-- =====================================================================
-- TEST 8: VIEW creation
-- SAS: %CreateTableOrView(data=sashelp.shoes, out=work.v_shoes, type=view)
-- =====================================================================
CALL SP_CREATE_TABLE_OR_VIEW(
    'TEST_SHOES',
    'TEST_OUTPUT_VIEW_8',
    NULL, NULL, NULL, NULL, NULL,
    'VIEW',                                      -- OBJ_TYPE
    TRUE
);

SELECT
    'Test 8: VIEW creation' AS TEST_NAME,
    CASE
        WHEN (SELECT COUNT(*) FROM TEST_OUTPUT_VIEW_8) = 9
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS;

-- =====================================================================
-- TEST 9: Combined WHERE + KEEP + ORDER BY + RENAME
-- SAS: %CreateTableOrView(data=sashelp.shoes, out=work.shoes,
--          keep=Region Subsidiary Product Sales,
--          where=Region in ("United States", "Canada"),
--          by=Region Subsidiary -Sales,
--          rename=Sales=TotalSales Region=Country)
-- =====================================================================
CALL SP_CREATE_TABLE_OR_VIEW(
    'TEST_SHOES',
    'TEST_OUTPUT_9',
    'REGION,SUBSIDIARY,PRODUCT,SALES',           -- KEEP_COLS
    NULL,
    'REGION,-SALES',                             -- ORDER_BY
    'REGION IN (''United States'', ''Canada'')',  -- WHERE_CLAUSE
    'SALES=TotalSales,REGION=Country',           -- RENAME_MAP
    'TABLE', TRUE
);

SELECT
    'Test 9: Combined operations' AS TEST_NAME,
    CASE
        WHEN (SELECT COUNT(*) FROM TEST_OUTPUT_9) = 5
         AND EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
                     WHERE TABLE_NAME = 'TEST_OUTPUT_9' AND COLUMN_NAME = 'TotalSales')
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS;

-- =====================================================================
-- TEST 10: Error handling - missing DATA parameter
-- =====================================================================
SELECT
    'Test 10: Missing DATA parameter' AS TEST_NAME,
    CASE
        WHEN SP_CREATE_TABLE_OR_VIEW(NULL, 'TEST_OUTPUT') LIKE '%ERROR%DATA%'
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS;

-- =====================================================================
-- TEST 11: Error handling - invalid OBJ_TYPE
-- =====================================================================
SELECT
    'Test 11: Invalid OBJ_TYPE' AS TEST_NAME,
    CASE
        WHEN SP_CREATE_TABLE_OR_VIEW('TEST_SHOES', 'TEST_OUTPUT', NULL, NULL,
                                      NULL, NULL, NULL, 'INDEX', FALSE) LIKE '%ERROR%OBJ_TYPE%'
        THEN 'PASS'
        ELSE 'FAIL'
    END AS STATUS;

-- =====================================================================
-- CLEANUP
-- =====================================================================
DROP TABLE IF EXISTS TEST_SHOES;
DROP TABLE IF EXISTS TEST_OUTPUT_1;
DROP TABLE IF EXISTS TEST_OUTPUT_2;
DROP TABLE IF EXISTS TEST_OUTPUT_3;
DROP TABLE IF EXISTS TEST_OUTPUT_4;
DROP TABLE IF EXISTS TEST_OUTPUT_5;
DROP TABLE IF EXISTS TEST_OUTPUT_6;
DROP TABLE IF EXISTS TEST_OUTPUT_7;
DROP VIEW  IF EXISTS TEST_OUTPUT_VIEW_8;
DROP TABLE IF EXISTS TEST_OUTPUT_9;
