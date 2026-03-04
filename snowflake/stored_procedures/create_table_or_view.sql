/*=====================================================================
Snowflake Stored Proc   : SP_CREATE_TABLE_OR_VIEW
Original SAS Macro      : CreateTableOrView.sas
Purpose                 : Create a table or view from a source table,
                          with optional column selection, filtering,
                          renaming, and ordering.  Mirrors the SAS macro
                          that builds data step / SQL code from parameters
                          and metadata.

Original Author         : Scott Bass
Snowflake Conversion    : Auto-converted from SAS macro

Parameters (mirror the original SAS macro interface):
  DATA            VARCHAR - Source table (fully qualified) (REQ)
  OUT             VARCHAR - Output table/view name (fully qualified) (REQ)
  KEEP_COLS       VARCHAR - Comma-separated list of columns to keep (Opt)
  DROP_COLS       VARCHAR - Comma-separated list of columns to drop (Opt).
                            If both DROP and KEEP are specified, DROP takes precedence.
  ORDER_BY        VARCHAR - Comma-separated list of columns to sort by (Opt).
                            Prefix with '-' for descending order (e.g. '-SALES').
  WHERE_CLAUSE    VARCHAR - Filter condition (without WHERE keyword) (Opt)
  RENAME_MAP      VARCHAR - Comma-separated rename pairs: old=new,old2=new2 (Opt)
  OBJ_TYPE        VARCHAR - TABLE or VIEW (default: TABLE)
  REPLACE_OBJ     BOOLEAN - Drop existing object first (default: FALSE)

Returns: VARCHAR - Summary of the DDL operation performed.

Design notes:
  The original SAS macro supports SAS data step, SQL, metadata datasets,
  shell datasets, code generation to files, indexes, and more.  This
  Snowflake conversion focuses on the core SQL-equivalent functionality:
  creating a table or view with column selection, filtering, ordering,
  and renaming.
=====================================================================*/

CREATE OR REPLACE PROCEDURE SP_CREATE_TABLE_OR_VIEW(
    DATA            VARCHAR,
    OUT             VARCHAR,
    KEEP_COLS       VARCHAR DEFAULT NULL,
    DROP_COLS       VARCHAR DEFAULT NULL,
    ORDER_BY        VARCHAR DEFAULT NULL,
    WHERE_CLAUSE    VARCHAR DEFAULT NULL,
    RENAME_MAP      VARCHAR DEFAULT NULL,
    OBJ_TYPE        VARCHAR DEFAULT 'TABLE',
    REPLACE_OBJ     BOOLEAN DEFAULT FALSE
)
RETURNS VARCHAR
LANGUAGE JAVASCRIPT
EXECUTE AS CALLER
AS
$$
    // ===================== UTILITY FUNCTIONS =====================

    function execQuery(stmt) {
        return snowflake.execute({ sqlText: stmt });
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
        return '"' + name.replace(/"/g, '""').trim() + '"';
    }

    function splitTrim(str, sep) {
        if (!str || str.trim() === '') return [];
        return str.split(sep || ',').map(function(s) { return s.trim(); }).filter(function(s) { return s !== ''; });
    }

    // ===================== VALIDATE INPUTS =====================

    if (!DATA || DATA.trim() === '') return 'ERROR: DATA parameter is required.';
    if (!OUT  || OUT.trim()  === '') return 'ERROR: OUT parameter is required.';

    var objType = (OBJ_TYPE || 'TABLE').toUpperCase();
    if (objType !== 'TABLE' && objType !== 'VIEW') {
        return 'ERROR: OBJ_TYPE must be TABLE or VIEW. Got: ' + objType;
    }

    // ===================== PARSE RENAME MAP =====================

    var renameMap = {};  // { UPPER_OLD: newName }
    if (RENAME_MAP && RENAME_MAP.trim() !== '') {
        var pairs = splitTrim(RENAME_MAP, ',');
        for (var i = 0; i < pairs.length; i++) {
            var eqPos = pairs[i].indexOf('=');
            if (eqPos > 0) {
                var oldName = pairs[i].substring(0, eqPos).trim().toUpperCase();
                var newName = pairs[i].substring(eqPos + 1).trim();
                renameMap[oldName] = newName;
            }
        }
    }

    // ===================== GET SOURCE COLUMNS =====================

    // Parse the source table name to extract catalog, schema, table
    var dataParts = DATA.replace(/"/g, '').split('.');
    var srcTable = dataParts[dataParts.length - 1].toUpperCase();
    var srcSchema = dataParts.length >= 2 ? dataParts[dataParts.length - 2].toUpperCase() : null;
    var srcCatalog = dataParts.length >= 3 ? dataParts[0].toUpperCase() : null;

    var colQuery = "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '" + srcTable + "'";
    if (srcSchema)  colQuery += " AND TABLE_SCHEMA = '" + srcSchema + "'";
    if (srcCatalog) colQuery += " AND TABLE_CATALOG = '" + srcCatalog + "'";
    colQuery += " ORDER BY ORDINAL_POSITION";

    var allColumns;
    try {
        allColumns = fetchAll(colQuery).rows.map(function(r) { return r['COLUMN_NAME']; });
    } catch (e) {
        return 'ERROR: Could not retrieve columns from ' + DATA + ': ' + e.message;
    }

    if (allColumns.length === 0) {
        return 'ERROR: Source table ' + DATA + ' has no columns or does not exist.';
    }

    // ===================== APPLY KEEP / DROP =====================

    var selectedColumns = allColumns.slice();  // copy

    if (DROP_COLS && DROP_COLS.trim() !== '') {
        var dropList = splitTrim(DROP_COLS, ',').map(function(c) { return c.toUpperCase(); });
        selectedColumns = selectedColumns.filter(function(c) {
            return dropList.indexOf(c.toUpperCase()) < 0;
        });
    } else if (KEEP_COLS && KEEP_COLS.trim() !== '') {
        var keepList = splitTrim(KEEP_COLS, ',').map(function(c) { return c.toUpperCase(); });
        selectedColumns = selectedColumns.filter(function(c) {
            return keepList.indexOf(c.toUpperCase()) >= 0;
        });
        // Preserve the order specified in KEEP_COLS
        selectedColumns.sort(function(a, b) {
            return keepList.indexOf(a.toUpperCase()) - keepList.indexOf(b.toUpperCase());
        });
    }

    if (selectedColumns.length === 0) {
        return 'ERROR: No columns remain after applying KEEP/DROP filters.';
    }

    // ===================== BUILD SELECT LIST =====================

    var selectParts = [];
    for (var i = 0; i < selectedColumns.length; i++) {
        var col = selectedColumns[i];
        var alias = renameMap[col.toUpperCase()];
        if (alias) {
            selectParts.push(quoteIdent(col) + ' AS ' + quoteIdent(alias));
        } else {
            selectParts.push(quoteIdent(col));
        }
    }

    // ===================== BUILD ORDER BY =====================

    var orderByClause = '';
    if (ORDER_BY && ORDER_BY.trim() !== '') {
        var orderParts = splitTrim(ORDER_BY, ',');
        var orderClauses = [];
        for (var i = 0; i < orderParts.length; i++) {
            var ob = orderParts[i].trim();
            if (ob.charAt(0) === '-') {
                orderClauses.push(quoteIdent(ob.substring(1).trim()) + ' DESC');
            } else {
                orderClauses.push(quoteIdent(ob) + ' ASC');
            }
        }
        orderByClause = ' ORDER BY ' + orderClauses.join(', ');
    }

    // ===================== BUILD WHERE =====================

    var whereClause = '';
    if (WHERE_CLAUSE && WHERE_CLAUSE.trim() !== '') {
        whereClause = ' WHERE ' + WHERE_CLAUSE;
    }

    // ===================== BUILD AND EXECUTE DDL =====================

    var createOrReplace = REPLACE_OBJ ? 'CREATE OR REPLACE ' : 'CREATE ';
    var sql = createOrReplace + objType + ' ' + OUT + ' AS\n' +
              'SELECT\n  ' + selectParts.join(',\n  ') + '\n' +
              'FROM ' + DATA +
              whereClause +
              orderByClause;

    try {
        execQuery(sql);
        return 'SUCCESS: Created ' + objType + ' ' + OUT + ' from ' + DATA +
               ' with ' + selectedColumns.length + ' column(s).' +
               '\n\nGenerated SQL:\n' + sql;
    } catch (e) {
        return 'ERROR creating ' + objType + ': ' + e.message +
               '\n\nAttempted SQL:\n' + sql;
    }
$$;

COMMENT ON PROCEDURE SP_CREATE_TABLE_OR_VIEW(VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, BOOLEAN)
IS 'Create a table or view from a source table with column selection, filtering, ordering, and renaming. Converted from SAS macro CreateTableOrView.sas.';
