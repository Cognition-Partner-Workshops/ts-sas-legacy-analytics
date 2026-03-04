/*=====================================================================
Snowflake Stored Proc   : SP_COMPARE
Original SAS Macro      : compare.sas
Purpose                 : Compare either two tables or two schemas,
                          reporting on differences in structure and data.
                          Mirrors SAS PROC COMPARE functionality.

Original Author         : Scott Bass
Snowflake Conversion    : Auto-converted from SAS macro

Parameters (mirror the original SAS macro interface):
  BASE          VARCHAR  - Base table or schema (fully qualified) (REQ)
  COMP          VARCHAR  - Compare table or schema (fully qualified) (REQ)
  KEY_COLUMNS   VARCHAR  - Comma-separated key/ID columns for row matching (Opt)
  FILTER_PATTERN VARCHAR - LIKE pattern to filter table names when comparing schemas (Opt)
  MAX_DIFF      INT      - Maximum number of differing rows to report (default 50)
  CRITERION     FLOAT    - Numeric fuzz factor for approximate equality (default 0.000001)
  METHOD        VARCHAR  - Comparison method: EXACT or RELATIVE (default EXACT)

Returns: VARCHAR - A formatted comparison report.

Design notes:
  - The SAS macro supports both dataset and library comparisons.
    In Snowflake, this maps to table-level and schema-level comparisons.
  - Schema comparison: lists tables present in both, only in base, or only
    in comp, then recursively compares matching tables.
  - Table comparison: compares column structure (names, types) and row data.
  - KEY_COLUMNS replaces the SAS BY= parameter for identifying rows.
=====================================================================*/

CREATE OR REPLACE PROCEDURE SP_COMPARE(
    BASE            VARCHAR,
    COMP            VARCHAR,
    KEY_COLUMNS     VARCHAR DEFAULT NULL,
    FILTER_PATTERN  VARCHAR DEFAULT NULL,
    MAX_DIFF        INT     DEFAULT 50,
    CRITERION       FLOAT   DEFAULT 0.000001,
    METHOD          VARCHAR DEFAULT 'EXACT'
)
RETURNS VARCHAR
LANGUAGE JAVASCRIPT
EXECUTE AS CALLER
AS
$$
    // ===================== UTILITY FUNCTIONS =====================

    function execQuery(stmt) {
        var rs = snowflake.execute({ sqlText: stmt });
        return rs;
    }

    function fetchAll(stmt) {
        var rs = execQuery(stmt);
        var cols = [];
        for (var c = 1; c <= rs.getColumnCount(); c++) {
            cols.push(rs.getColumnName(c));
        }
        var rows = [];
        while (rs.next()) {
            var row = {};
            for (var c = 0; c < cols.length; c++) {
                row[cols[c]] = rs.getColumnValue(c + 1);
            }
            rows.push(row);
        }
        return { columns: cols, rows: rows };
    }

    function quoteIdent(name) {
        return '"' + name.replace(/"/g, '""') + '"';
    }

    // Parse a potentially qualified name (db.schema.table or schema.table or table)
    function parseName(name) {
        var parts = name.replace(/"/g, '').split('.');
        return parts;
    }

    // Determine whether the identifier refers to a schema or a table
    function isSchema(name) {
        var parts = parseName(name);
        // Try to query information_schema to see if this is a schema
        try {
            var db = parts.length >= 2 ? parts[0] : null;
            var schema = parts.length >= 2 ? parts[parts.length - 1] : parts[0];
            var sql;
            if (db) {
                sql = "SELECT COUNT(*) AS CNT FROM " + quoteIdent(db) +
                      ".INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '" +
                      schema.toUpperCase() + "'";
            } else {
                sql = "SELECT COUNT(*) AS CNT FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '" +
                      schema.toUpperCase() + "'";
            }
            var result = fetchAll(sql);
            if (result.rows.length > 0 && result.rows[0]['CNT'] > 0) {
                return true;
            }
        } catch (e) {
            // Not a schema, might be a table
        }

        // Check if it's a table
        try {
            var sql = "SELECT COUNT(*) AS CNT FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '" +
                      parts[parts.length - 1].toUpperCase() + "'";
            if (parts.length >= 2) {
                sql += " AND TABLE_SCHEMA = '" + parts[parts.length - 2].toUpperCase() + "'";
            }
            var result = fetchAll(sql);
            if (result.rows.length > 0 && result.rows[0]['CNT'] > 0) {
                return false;
            }
        } catch (e) {
            // Fall through
        }

        // Default: assume table if nothing matched
        return false;
    }

    // ===================== REPORT BUILDER =====================

    var report = [];
    function addLine(line) { report.push(line || ''); }
    function addSeparator() { addLine('=' .repeat(80)); }

    // ===================== SCHEMA COMPARISON =====================

    function compareSchemas(baseName, compName, filterPattern) {
        addSeparator();
        addLine('SCHEMA COMPARISON: ' + baseName + ' vs ' + compName);
        addSeparator();

        var baseParts = parseName(baseName);
        var compParts = parseName(compName);

        var baseDb = baseParts.length >= 2 ? baseParts[0] : null;
        var baseSchema = baseParts.length >= 2 ? baseParts[1] : baseParts[0];
        var compDb = compParts.length >= 2 ? compParts[0] : null;
        var compSchema = compParts.length >= 2 ? compParts[1] : compParts[0];

        // Get tables in base schema
        var baseSql = "SELECT TABLE_NAME, ROW_COUNT FROM " +
            (baseDb ? quoteIdent(baseDb) + "." : "") +
            "INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '" + baseSchema.toUpperCase() + "'";
        if (filterPattern) {
            baseSql += " AND TABLE_NAME LIKE '" + filterPattern.toUpperCase() + "'";
        }
        baseSql += " ORDER BY TABLE_NAME";

        var compSql = "SELECT TABLE_NAME, ROW_COUNT FROM " +
            (compDb ? quoteIdent(compDb) + "." : "") +
            "INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '" + compSchema.toUpperCase() + "'";
        if (filterPattern) {
            compSql += " AND TABLE_NAME LIKE '" + filterPattern.toUpperCase() + "'";
        }
        compSql += " ORDER BY TABLE_NAME";

        var baseTables = {};
        var compTables = {};
        try {
            var baseResult = fetchAll(baseSql);
            for (var i = 0; i < baseResult.rows.length; i++) {
                baseTables[baseResult.rows[i]['TABLE_NAME']] = baseResult.rows[i]['ROW_COUNT'];
            }
        } catch (e) {
            addLine('ERROR querying base schema: ' + e.message);
            return;
        }
        try {
            var compResult = fetchAll(compSql);
            for (var i = 0; i < compResult.rows.length; i++) {
                compTables[compResult.rows[i]['TABLE_NAME']] = compResult.rows[i]['ROW_COUNT'];
            }
        } catch (e) {
            addLine('ERROR querying compare schema: ' + e.message);
            return;
        }

        // Build combined set
        var allTables = {};
        for (var t in baseTables) allTables[t] = true;
        for (var t in compTables) allTables[t] = true;
        var tableNames = Object.keys(allTables).sort();

        addLine('');
        addLine(padRight('TABLE_NAME', 40) + padRight('IN_BASE', 10) +
                padRight('IN_COMP', 10) + padRight('BASE_ROWS', 12) +
                padRight('COMP_ROWS', 12) + 'MATCHED');
        addLine('-'.repeat(94));

        var matchedTables = [];
        for (var i = 0; i < tableNames.length; i++) {
            var t = tableNames[i];
            var inBase = baseTables.hasOwnProperty(t);
            var inComp = compTables.hasOwnProperty(t);
            var matched = inBase && inComp ? 'MATCHED' : 'NO MATCH';
            var baseRows = inBase ? String(baseTables[t] || 0) : '-';
            var compRows = inComp ? String(compTables[t] || 0) : '-';
            addLine(padRight(t, 40) + padRight(inBase ? 'YES' : 'NO', 10) +
                    padRight(inComp ? 'YES' : 'NO', 10) +
                    padRight(baseRows, 12) + padRight(compRows, 12) + matched);
            if (inBase && inComp) {
                matchedTables.push(t);
            }
        }

        addLine('');
        addLine('Tables only in BASE: ' +
            tableNames.filter(function(t) { return baseTables.hasOwnProperty(t) && !compTables.hasOwnProperty(t); }).join(', '));
        addLine('Tables only in COMP: ' +
            tableNames.filter(function(t) { return !baseTables.hasOwnProperty(t) && compTables.hasOwnProperty(t); }).join(', '));
        addLine('');

        // Compare each matched table
        for (var i = 0; i < matchedTables.length; i++) {
            var baseTableFull = baseName + '.' + matchedTables[i];
            var compTableFull = compName + '.' + matchedTables[i];
            compareTables(baseTableFull, compTableFull, KEY_COLUMNS);
        }
    }

    // ===================== TABLE COMPARISON =====================

    function compareTables(baseTable, compTable, keyCols) {
        addSeparator();
        addLine('TABLE COMPARISON: ' + baseTable + ' (base) vs ' + compTable + ' (compare)');
        addSeparator();

        // --- Column comparison ---
        var baseColsSql = "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE, IS_NULLABLE, ORDINAL_POSITION " +
            "FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '" +
            parseName(baseTable).pop().toUpperCase() + "'";
        var baseSchemaName = parseName(baseTable);
        if (baseSchemaName.length >= 2) {
            baseColsSql += " AND TABLE_SCHEMA = '" + baseSchemaName[baseSchemaName.length - 2].toUpperCase() + "'";
        }
        if (baseSchemaName.length >= 3) {
            baseColsSql += " AND TABLE_CATALOG = '" + baseSchemaName[0].toUpperCase() + "'";
        }
        baseColsSql += " ORDER BY ORDINAL_POSITION";

        var compColsSql = "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE, IS_NULLABLE, ORDINAL_POSITION " +
            "FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '" +
            parseName(compTable).pop().toUpperCase() + "'";
        var compSchemaName = parseName(compTable);
        if (compSchemaName.length >= 2) {
            compColsSql += " AND TABLE_SCHEMA = '" + compSchemaName[compSchemaName.length - 2].toUpperCase() + "'";
        }
        if (compSchemaName.length >= 3) {
            compColsSql += " AND TABLE_CATALOG = '" + compSchemaName[0].toUpperCase() + "'";
        }
        compColsSql += " ORDER BY ORDINAL_POSITION";

        var baseCols, compCols;
        try {
            baseCols = fetchAll(baseColsSql);
            compCols = fetchAll(compColsSql);
        } catch (e) {
            addLine('ERROR querying column metadata: ' + e.message);
            return;
        }

        var baseColMap = {};
        for (var i = 0; i < baseCols.rows.length; i++) {
            baseColMap[baseCols.rows[i]['COLUMN_NAME']] = baseCols.rows[i];
        }
        var compColMap = {};
        for (var i = 0; i < compCols.rows.length; i++) {
            compColMap[compCols.rows[i]['COLUMN_NAME']] = compCols.rows[i];
        }

        var allColNames = {};
        for (var c in baseColMap) allColNames[c] = true;
        for (var c in compColMap) allColNames[c] = true;
        var colNames = Object.keys(allColNames).sort();

        // Column structure report
        addLine('');
        addLine('--- Column Structure ---');
        addLine(padRight('COLUMN', 30) + padRight('IN_BASE', 10) + padRight('IN_COMP', 10) +
                padRight('BASE_TYPE', 20) + padRight('COMP_TYPE', 20) + 'TYPE_MATCH');
        addLine('-'.repeat(100));

        var onlyInBase = [];
        var onlyInComp = [];
        var typeMismatches = [];

        for (var i = 0; i < colNames.length; i++) {
            var col = colNames[i];
            var inBase = baseColMap.hasOwnProperty(col);
            var inComp = compColMap.hasOwnProperty(col);
            var baseType = inBase ? baseColMap[col]['DATA_TYPE'] : '-';
            var compType = inComp ? compColMap[col]['DATA_TYPE'] : '-';
            var typeMatch = (inBase && inComp) ? (baseType === compType ? 'YES' : 'NO') : '-';

            addLine(padRight(col, 30) + padRight(inBase ? 'YES' : 'NO', 10) +
                    padRight(inComp ? 'YES' : 'NO', 10) +
                    padRight(baseType, 20) + padRight(compType, 20) + typeMatch);

            if (inBase && !inComp) onlyInBase.push(col);
            if (!inBase && inComp) onlyInComp.push(col);
            if (inBase && inComp && baseType !== compType) typeMismatches.push(col);
        }

        addLine('');
        if (onlyInBase.length > 0) addLine('Columns only in BASE: ' + onlyInBase.join(', '));
        if (onlyInComp.length > 0) addLine('Columns only in COMP: ' + onlyInComp.join(', '));
        if (typeMismatches.length > 0) addLine('Type mismatches: ' + typeMismatches.join(', '));

        // --- Row count comparison ---
        try {
            var baseCount = fetchAll("SELECT COUNT(*) AS CNT FROM " + baseTable);
            var compCount = fetchAll("SELECT COUNT(*) AS CNT FROM " + compTable);
            var bCnt = baseCount.rows[0]['CNT'];
            var cCnt = compCount.rows[0]['CNT'];
            addLine('');
            addLine('Row counts: BASE=' + bCnt + '  COMP=' + cCnt +
                    (bCnt === cCnt ? '  (MATCH)' : '  (DIFFER by ' + Math.abs(bCnt - cCnt) + ')'));
        } catch (e) {
            addLine('ERROR counting rows: ' + e.message);
        }

        // --- Data comparison (common columns only) ---
        var commonCols = colNames.filter(function(c) {
            return baseColMap.hasOwnProperty(c) && compColMap.hasOwnProperty(c);
        });

        if (commonCols.length === 0) {
            addLine('No common columns to compare data.');
            return;
        }

        if (keyCols) {
            var keyArr = keyCols.split(',').map(function(k) { return k.trim().toUpperCase(); });

            // Build value comparison for non-key common columns
            var valueCols = commonCols.filter(function(c) {
                return keyArr.indexOf(c.toUpperCase()) < 0;
            });

            if (valueCols.length === 0) {
                addLine('All common columns are key columns; no value columns to compare.');
                return;
            }

            // Build comparison query using FULL OUTER JOIN on key columns
            var joinCond = keyArr.map(function(k) {
                return 'b.' + quoteIdent(k) + ' = c.' + quoteIdent(k);
            }).join(' AND ');

            var diffConditions = [];
            for (var i = 0; i < valueCols.length; i++) {
                var vc = quoteIdent(valueCols[i]);
                if (METHOD === 'EXACT') {
                    diffConditions.push(
                        '(b.' + vc + ' IS DISTINCT FROM c.' + vc + ')'
                    );
                } else {
                    diffConditions.push(
                        '(CASE WHEN b.' + vc + ' IS NULL AND c.' + vc + ' IS NULL THEN FALSE ' +
                        'WHEN b.' + vc + ' IS NULL OR c.' + vc + ' IS NULL THEN TRUE ' +
                        'WHEN TRY_CAST(b.' + vc + ' AS FLOAT) IS NOT NULL AND TRY_CAST(c.' + vc + ' AS FLOAT) IS NOT NULL ' +
                        'THEN ABS(TRY_CAST(b.' + vc + ' AS FLOAT) - TRY_CAST(c.' + vc + ' AS FLOAT)) > ' + CRITERION + ' ' +
                        'ELSE b.' + vc + '::VARCHAR IS DISTINCT FROM c.' + vc + '::VARCHAR END)'
                    );
                }
            }

            var diffSql = "SELECT " +
                keyArr.map(function(k) { return 'COALESCE(b.' + quoteIdent(k) + ', c.' + quoteIdent(k) + ') AS ' + quoteIdent(k); }).join(', ') + ', ' +
                valueCols.map(function(vc) {
                    return 'b.' + quoteIdent(vc) + ' AS BASE_' + vc + ', c.' + quoteIdent(vc) + ' AS COMP_' + vc;
                }).join(', ') +
                " FROM " + baseTable + " b FULL OUTER JOIN " + compTable + " c ON " + joinCond +
                " WHERE (b." + quoteIdent(keyArr[0]) + " IS NULL OR c." + quoteIdent(keyArr[0]) + " IS NULL OR " +
                diffConditions.join(' OR ') + ")" +
                " LIMIT " + MAX_DIFF;

            try {
                var diffResult = fetchAll(diffSql);
                addLine('');
                addLine('--- Data Differences (up to ' + MAX_DIFF + ' rows) ---');
                if (diffResult.rows.length === 0) {
                    addLine('No differences found in data values.');
                } else {
                    addLine('Found ' + diffResult.rows.length + ' differing row(s):');
                    addLine('');
                    addLine(diffResult.columns.map(function(c) { return padRight(c, 25); }).join(''));
                    addLine('-'.repeat(diffResult.columns.length * 25));
                    for (var r = 0; r < diffResult.rows.length; r++) {
                        var line = '';
                        for (var ci = 0; ci < diffResult.columns.length; ci++) {
                            var val = diffResult.rows[r][diffResult.columns[ci]];
                            line += padRight(val === null ? '<NULL>' : String(val), 25);
                        }
                        addLine(line);
                    }
                }
            } catch (e) {
                addLine('ERROR comparing data: ' + e.message);
            }
        } else {
            // No key columns: compare using MINUS/EXCEPT
            var colList = commonCols.map(function(c) { return quoteIdent(c); }).join(', ');

            addLine('');
            addLine('--- Data Differences (no key columns; using EXCEPT) ---');

            try {
                var onlyBaseSql = "(SELECT " + colList + " FROM " + baseTable +
                    " EXCEPT SELECT " + colList + " FROM " + compTable + ") LIMIT " + MAX_DIFF;
                var onlyBaseResult = fetchAll("SELECT * FROM " + onlyBaseSql);
                addLine('');
                addLine('Rows only in BASE: ' + onlyBaseResult.rows.length);
                if (onlyBaseResult.rows.length > 0) {
                    addLine(onlyBaseResult.columns.map(function(c) { return padRight(c, 25); }).join(''));
                    for (var r = 0; r < onlyBaseResult.rows.length; r++) {
                        var line = '';
                        for (var ci = 0; ci < onlyBaseResult.columns.length; ci++) {
                            var val = onlyBaseResult.rows[r][onlyBaseResult.columns[ci]];
                            line += padRight(val === null ? '<NULL>' : String(val), 25);
                        }
                        addLine(line);
                    }
                }
            } catch (e) {
                addLine('ERROR: ' + e.message);
            }

            try {
                var onlyCompSql = "(SELECT " + colList + " FROM " + compTable +
                    " EXCEPT SELECT " + colList + " FROM " + baseTable + ") LIMIT " + MAX_DIFF;
                var onlyCompResult = fetchAll("SELECT * FROM " + onlyCompSql);
                addLine('');
                addLine('Rows only in COMP: ' + onlyCompResult.rows.length);
                if (onlyCompResult.rows.length > 0) {
                    addLine(onlyCompResult.columns.map(function(c) { return padRight(c, 25); }).join(''));
                    for (var r = 0; r < onlyCompResult.rows.length; r++) {
                        var line = '';
                        for (var ci = 0; ci < onlyCompResult.columns.length; ci++) {
                            var val = onlyCompResult.rows[r][onlyCompResult.columns[ci]];
                            line += padRight(val === null ? '<NULL>' : String(val), 25);
                        }
                        addLine(line);
                    }
                }
            } catch (e) {
                addLine('ERROR: ' + e.message);
            }
        }
    }

    // ===================== HELPERS =====================

    function padRight(str, len) {
        str = String(str || '');
        while (str.length < len) str += ' ';
        return str.substring(0, len);
    }

    // ===================== MAIN =====================

    // Validate inputs
    if (!BASE) return 'ERROR: BASE parameter is required.';
    if (!COMP) return 'ERROR: COMP parameter is required.';

    var methodUpper = (METHOD || 'EXACT').toUpperCase();
    if (methodUpper !== 'EXACT' && methodUpper !== 'RELATIVE' &&
        methodUpper !== 'ABSOLUTE' && methodUpper !== 'PERCENT') {
        return 'ERROR: METHOD must be EXACT, ABSOLUTE, PERCENT, or RELATIVE.';
    }

    var baseIsSchema = isSchema(BASE);
    var compIsSchema = isSchema(COMP);

    if (baseIsSchema && compIsSchema) {
        compareSchemas(BASE, COMP, FILTER_PATTERN);
    } else if (!baseIsSchema && !compIsSchema) {
        compareTables(BASE, COMP, KEY_COLUMNS);
    } else {
        return 'ERROR: Both BASE and COMP must be the same type (both tables or both schemas).';
    }

    return report.join('\n');
$$;

COMMENT ON PROCEDURE SP_COMPARE(VARCHAR, VARCHAR, VARCHAR, VARCHAR, INT, FLOAT, VARCHAR)
IS 'Compare two tables or schemas. Converted from SAS macro compare.sas (PROC COMPARE).';
