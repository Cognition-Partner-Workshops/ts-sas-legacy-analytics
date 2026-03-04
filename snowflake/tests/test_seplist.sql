/*=====================================================================
Test Suite              : test_seplist.sql
Tests for              : SEPLIST UDF (converted from seplist.sas)
Purpose                : Validate that the Snowflake SEPLIST UDF produces
                         the same output as the original SAS %seplist macro.

Each test case mirrors a usage example from the original SAS macro header.
=====================================================================*/

-- =====================================================================
-- SETUP: Create the UDF (idempotent)
-- =====================================================================
-- Run snowflake/udfs/seplist.sql first to create the function.

-- =====================================================================
-- TEST 1: Basic comma-separated list (default delimiter)
-- SAS:    %put %seplist(Hello World);
-- Result: Hello,World
-- =====================================================================
SELECT
    'Test 1: Basic comma-separated' AS TEST_NAME,
    SEPLIST('Hello World') AS RESULT,
    'Hello,World' AS EXPECTED,
    CASE WHEN SEPLIST('Hello World') = 'Hello,World' THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- =====================================================================
-- TEST 2: Double-quoted nesting
-- SAS:    %put %seplist(Hello World,nest=QQ);
-- Result: "Hello","World"
-- =====================================================================
SELECT
    'Test 2: Double-quoted nesting' AS TEST_NAME,
    SEPLIST('Hello World', ' ', ',', '', 'QQ', '', TRUE) AS RESULT,
    '"Hello","World"' AS EXPECTED,
    CASE WHEN SEPLIST('Hello World', ' ', ',', '', 'QQ', '', TRUE) = '"Hello","World"'
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- =====================================================================
-- TEST 3: Single-quoted nesting with caret delimiter, no trim
-- SAS:    %put %seplist(Hello   ^   World   ,nest=Q,indlm=^,trim=N);
-- Result: 'Hello   ','   World   '
-- Note:   SAS trims trailing but preserves internal; Snowflake preserves as-is with trim=false
-- =====================================================================
SELECT
    'Test 3: Single-quoted, caret delim, no trim' AS TEST_NAME,
    SEPLIST('Hello   ^   World   ', '^', ',', '', 'Q', '', FALSE) AS RESULT,
    '''Hello   '',''   World   ''' AS EXPECTED,
    CASE WHEN SEPLIST('Hello   ^   World   ', '^', ',', '', 'Q', '', FALSE)
              = '''Hello   '',''   World   '''
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- =====================================================================
-- TEST 4: Single-quoted nesting with caret delimiter, with trim
-- SAS:    %put %seplist(Hello   ^   World   ,nest=Q,indlm=^,trim=Y);
-- Result: 'Hello','World'
-- =====================================================================
SELECT
    'Test 4: Single-quoted, caret delim, with trim' AS TEST_NAME,
    SEPLIST('Hello   ^   World   ', '^', ',', '', 'Q', '', TRUE) AS RESULT,
    '''Hello'',''World''' AS EXPECTED,
    CASE WHEN SEPLIST('Hello   ^   World   ', '^', ',', '', 'Q', '', TRUE)
              = '''Hello'',''World'''
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- =====================================================================
-- TEST 5: Double-quoted nesting with custom output delimiter
-- SAS:    %put %seplist(Hello   ^   World   ,nest=QQ,indlm=^,dlm=~,trim=Y);
-- Result: "Hello"~"World"
-- =====================================================================
SELECT
    'Test 5: Double-quoted, tilde delimiter' AS TEST_NAME,
    SEPLIST('Hello   ^   World   ', '^', '~', '', 'QQ', '', TRUE) AS RESULT,
    '"Hello"~"World"' AS EXPECTED,
    CASE WHEN SEPLIST('Hello   ^   World   ', '^', '~', '', 'QQ', '', TRUE)
              = '"Hello"~"World"'
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- =====================================================================
-- TEST 6: Prefix and suffix
-- SAS:    %put %seplist(A B C,prefix=PREFIX_,suffix=_suffix);
-- Result: PREFIX_A_suffix,PREFIX_B_suffix,PREFIX_C_suffix
-- =====================================================================
SELECT
    'Test 6: Prefix and suffix' AS TEST_NAME,
    SEPLIST('A B C', ' ', ',', 'PREFIX_', '', '_suffix', TRUE) AS RESULT,
    'PREFIX_A_suffix,PREFIX_B_suffix,PREFIX_C_suffix' AS EXPECTED,
    CASE WHEN SEPLIST('A B C', ' ', ',', 'PREFIX_', '', '_suffix', TRUE)
              = 'PREFIX_A_suffix,PREFIX_B_suffix,PREFIX_C_suffix'
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- =====================================================================
-- TEST 7: Empty input
-- =====================================================================
SELECT
    'Test 7: Empty input' AS TEST_NAME,
    SEPLIST('') AS RESULT,
    '' AS EXPECTED,
    CASE WHEN SEPLIST('') = '' THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- =====================================================================
-- TEST 8: Single item (no delimiter needed)
-- =====================================================================
SELECT
    'Test 8: Single item' AS TEST_NAME,
    SEPLIST('OnlyOne') AS RESULT,
    'OnlyOne' AS EXPECTED,
    CASE WHEN SEPLIST('OnlyOne') = 'OnlyOne' THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- =====================================================================
-- TEST 9: Parenthesis nesting
-- =====================================================================
SELECT
    'Test 9: Parenthesis nesting' AS TEST_NAME,
    SEPLIST('X Y Z', ' ', ',', '', 'P', '', TRUE) AS RESULT,
    '(X),(Y),(Z)' AS EXPECTED,
    CASE WHEN SEPLIST('X Y Z', ' ', ',', '', 'P', '', TRUE) = '(X),(Y),(Z)'
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- =====================================================================
-- TEST 10: Curly brace nesting
-- =====================================================================
SELECT
    'Test 10: Curly brace nesting' AS TEST_NAME,
    SEPLIST('X Y Z', ' ', ',', '', 'C', '', TRUE) AS RESULT,
    '{X},{Y},{Z}' AS EXPECTED,
    CASE WHEN SEPLIST('X Y Z', ' ', ',', '', 'C', '', TRUE) = '{X},{Y},{Z}'
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- =====================================================================
-- TEST 11: Bracket nesting
-- =====================================================================
SELECT
    'Test 11: Bracket nesting' AS TEST_NAME,
    SEPLIST('X Y Z', ' ', ',', '', 'B', '', TRUE) AS RESULT,
    '[X],[Y],[Z]' AS EXPECTED,
    CASE WHEN SEPLIST('X Y Z', ' ', ',', '', 'B', '', TRUE) = '[X],[Y],[Z]'
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- =====================================================================
-- TEST 12: Space delimiter output (useful for SQL IN clauses)
-- =====================================================================
SELECT
    'Test 12: Space output delimiter' AS TEST_NAME,
    SEPLIST('A B C', ' ', ' ', '', '', '', TRUE) AS RESULT,
    'A B C' AS EXPECTED,
    CASE WHEN SEPLIST('A B C', ' ', ' ', '', '', '', TRUE) = 'A B C'
         THEN 'PASS' ELSE 'FAIL' END AS STATUS;

-- =====================================================================
-- SUMMARY: Run all tests together
-- =====================================================================
SELECT 'SEPLIST Test Summary' AS SUITE,
       COUNT(*) AS TOTAL_TESTS,
       SUM(CASE WHEN STATUS = 'PASS' THEN 1 ELSE 0 END) AS PASSED,
       SUM(CASE WHEN STATUS = 'FAIL' THEN 1 ELSE 0 END) AS FAILED
FROM (
    SELECT CASE WHEN SEPLIST('Hello World') = 'Hello,World' THEN 'PASS' ELSE 'FAIL' END AS STATUS
    UNION ALL
    SELECT CASE WHEN SEPLIST('Hello World', ' ', ',', '', 'QQ', '', TRUE) = '"Hello","World"' THEN 'PASS' ELSE 'FAIL' END
    UNION ALL
    SELECT CASE WHEN SEPLIST('Hello   ^   World   ', '^', ',', '', 'Q', '', TRUE) = '''Hello'',''World''' THEN 'PASS' ELSE 'FAIL' END
    UNION ALL
    SELECT CASE WHEN SEPLIST('Hello   ^   World   ', '^', '~', '', 'QQ', '', TRUE) = '"Hello"~"World"' THEN 'PASS' ELSE 'FAIL' END
    UNION ALL
    SELECT CASE WHEN SEPLIST('A B C', ' ', ',', 'PREFIX_', '', '_suffix', TRUE) = 'PREFIX_A_suffix,PREFIX_B_suffix,PREFIX_C_suffix' THEN 'PASS' ELSE 'FAIL' END
    UNION ALL
    SELECT CASE WHEN SEPLIST('') = '' THEN 'PASS' ELSE 'FAIL' END
    UNION ALL
    SELECT CASE WHEN SEPLIST('OnlyOne') = 'OnlyOne' THEN 'PASS' ELSE 'FAIL' END
    UNION ALL
    SELECT CASE WHEN SEPLIST('X Y Z', ' ', ',', '', 'P', '', TRUE) = '(X),(Y),(Z)' THEN 'PASS' ELSE 'FAIL' END
    UNION ALL
    SELECT CASE WHEN SEPLIST('X Y Z', ' ', ',', '', 'C', '', TRUE) = '{X},{Y},{Z}' THEN 'PASS' ELSE 'FAIL' END
    UNION ALL
    SELECT CASE WHEN SEPLIST('X Y Z', ' ', ',', '', 'B', '', TRUE) = '[X],[Y],[Z]' THEN 'PASS' ELSE 'FAIL' END
    UNION ALL
    SELECT CASE WHEN SEPLIST('A B C', ' ', ' ', '', '', '', TRUE) = 'A B C' THEN 'PASS' ELSE 'FAIL' END
);
