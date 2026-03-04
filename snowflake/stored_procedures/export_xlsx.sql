/*=====================================================================
Snowflake Stored Proc   : SP_EXPORT_XLSX
Original SAS Macro      : export_xlsx.sas
Purpose                 : Export a Snowflake table or query result to a
                          staged file in CSV or Parquet format (the closest
                          Snowflake equivalent to SAS PROC EXPORT DBMS=XLSX).

                          In SAS, the macro wraps PROC EXPORT to write an
                          XLSX file.  Snowflake does not natively export to
                          XLSX, but can COPY INTO a stage as CSV (easily
                          opened in Excel) or Parquet.  This procedure
                          supports both, with CSV as the default since it
                          is the most Excel-compatible.

Original Author         : Scott Bass
Snowflake Conversion    : Auto-converted from SAS macro

Parameters (mirror the original SAS macro interface):
  DATA          VARCHAR  - Source table or (query) to export (REQ).
                           Supports dataset options in SAS parlance;
                           in Snowflake, pass a fully-qualified table name
                           or a subquery wrapped in parentheses.
  STAGE_PATH    VARCHAR  - Destination stage path (REQ).
                           e.g. '@my_stage/exports/filename.csv'
  FILE_FORMAT   VARCHAR  - Output format: CSV or PARQUET (default: CSV)
  REPLACE       BOOLEAN  - Overwrite existing file (default: FALSE).
                           Maps to SAS REPLACE=Y/N.
  USE_HEADER    BOOLEAN  - Include column headers in CSV (default: TRUE).
                           Maps to SAS LABEL=N (names) or LABEL=Y (labels).
  FIELD_DELIMITER VARCHAR - Field delimiter for CSV (default: comma)
  COMPRESSION   VARCHAR  - Compression: NONE, GZIP, BZ2, etc. (default: NONE)
  SINGLE_FILE   BOOLEAN  - Output a single file (default: TRUE)
  MAX_FILE_SIZE INT      - Max file size in bytes (default: 5368709120 = 5GB)

Returns: VARCHAR - Summary of the export operation.

Design notes:
  SAS PROC EXPORT creates a local file.  In Snowflake, data is exported
  to a stage (internal or external).  Users can then GET the file from
  the stage to their local machine, or access it from cloud storage.
=====================================================================*/

CREATE OR REPLACE PROCEDURE SP_EXPORT_XLSX(
    DATA            VARCHAR,
    STAGE_PATH      VARCHAR,
    FILE_FORMAT     VARCHAR DEFAULT 'CSV',
    REPLACE         BOOLEAN DEFAULT FALSE,
    USE_HEADER      BOOLEAN DEFAULT TRUE,
    FIELD_DELIMITER VARCHAR DEFAULT ',',
    COMPRESSION     VARCHAR DEFAULT 'NONE',
    SINGLE_FILE     BOOLEAN DEFAULT TRUE,
    MAX_FILE_SIZE   INT     DEFAULT 5368709120
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

    // ===================== VALIDATE INPUTS =====================

    if (!DATA || DATA.trim() === '') {
        return 'ERROR: DATA parameter is required.';
    }
    if (!STAGE_PATH || STAGE_PATH.trim() === '') {
        return 'ERROR: STAGE_PATH parameter is required.';
    }

    var fmt = (FILE_FORMAT || 'CSV').toUpperCase();
    if (fmt !== 'CSV' && fmt !== 'PARQUET') {
        return 'ERROR: FILE_FORMAT must be CSV or PARQUET. Got: ' + fmt;
    }

    var compression = (COMPRESSION || 'NONE').toUpperCase();

    // ===================== CHECK IF FILE EXISTS =====================

    if (!REPLACE) {
        try {
            var listSql = "LIST " + STAGE_PATH;
            var listResult = fetchAll(listSql);
            if (listResult.rows.length > 0) {
                return 'ERROR: File already exists at ' + STAGE_PATH +
                       '. Specify REPLACE=TRUE to overwrite.';
            }
        } catch (e) {
            // File does not exist or stage path is a directory - OK to proceed
        }
    }

    // ===================== REMOVE EXISTING FILE IF REPLACE =====================

    if (REPLACE) {
        try {
            execQuery("REMOVE " + STAGE_PATH);
        } catch (e) {
            // Ignore if file doesn't exist
        }
    }

    // ===================== BUILD COPY INTO STATEMENT =====================

    var sourceExpr;
    // Determine if DATA is a subquery (starts with parenthesis or SELECT)
    var trimmedData = DATA.trim();
    if (trimmedData.charAt(0) === '(' ||
        trimmedData.toUpperCase().indexOf('SELECT') === 0) {
        sourceExpr = '(' + trimmedData.replace(/^\(/, '').replace(/\)$/, '') + ')';
    } else {
        sourceExpr = trimmedData;
    }

    var copyParts = [];
    copyParts.push("COPY INTO " + STAGE_PATH);
    copyParts.push("FROM " + sourceExpr);

    // Build file format options inline
    var formatOpts = [];
    formatOpts.push("TYPE = '" + fmt + "'");

    if (fmt === 'CSV') {
        formatOpts.push("FIELD_DELIMITER = '" + (FIELD_DELIMITER || ',') + "'");
        formatOpts.push("FIELD_OPTIONALLY_ENCLOSED_BY = '\"'");
        if (USE_HEADER) {
            formatOpts.push("HEADER = TRUE");
        }
    }
    formatOpts.push("COMPRESSION = '" + compression + "'");

    copyParts.push("FILE_FORMAT = (" + formatOpts.join(' ') + ")");

    if (SINGLE_FILE) {
        copyParts.push("SINGLE = TRUE");
    }

    copyParts.push("MAX_FILE_SIZE = " + (MAX_FILE_SIZE || 5368709120));
    copyParts.push("OVERWRITE = " + (REPLACE ? "TRUE" : "FALSE"));

    var copySql = copyParts.join('\n');

    // ===================== EXECUTE EXPORT =====================

    try {
        var result = fetchAll(copySql);
        var rowsUnloaded = 0;
        if (result.rows.length > 0) {
            // COPY INTO ... unload returns rows_unloaded
            rowsUnloaded = result.rows[0]['rows_unloaded'] ||
                          result.rows[0]['ROWS_UNLOADED'] || 0;
        }

        return 'SUCCESS: Exported ' + rowsUnloaded + ' rows from ' + DATA +
               ' to ' + STAGE_PATH + ' as ' + fmt + '.' +
               '\n\nGenerated SQL:\n' + copySql;
    } catch (e) {
        return 'ERROR exporting data: ' + e.message +
               '\n\nAttempted SQL:\n' + copySql;
    }
$$;

COMMENT ON PROCEDURE SP_EXPORT_XLSX(VARCHAR, VARCHAR, VARCHAR, BOOLEAN, BOOLEAN, VARCHAR, VARCHAR, BOOLEAN, INT)
IS 'Export a table/query to a staged file (CSV/Parquet). Converted from SAS macro export_xlsx.sas (PROC EXPORT wrapper).';
