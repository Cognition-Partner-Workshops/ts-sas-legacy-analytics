/*=====================================================================
Snowflake UDF           : DATE_IMPUTE
Original SAS Macro      : date_impute.sas
Purpose                 : Impute partial dates from separate year, month,
                          and day character components.  Returns a JSON
                          object containing the imputed date and metadata.

Original Author         : Scott Bass
Snowflake Conversion    : Auto-converted from SAS macro

Parameters (mirror the original SAS macro interface):
  IN_DATE    DATE      - Input date value (NULL triggers imputation)
  IN_Y       VARCHAR   - Input year  as character string (REQ)
  IN_M       VARCHAR   - Input month as character string (REQ)
  IN_D       VARCHAR   - Input day   as character string (REQ)
  IMP_Y      INT       - Default year  to impute when missing (NULL = no imputation)
  IMP_M      INT       - Default month to impute when missing (default: 1)
  IMP_D      INT       - Default day   to impute when missing (default: 1)
  MONTH_FMT  VARCHAR   - Month format: 'MM' (numeric) or 'MON' (3-letter abbrev)

Returns: VARIANT (JSON object) with keys:
  imputed_date       DATE or NULL
  imputed_flag       BOOLEAN  - TRUE if any component was imputed
  derived_year       INT or NULL
  derived_month      INT or NULL
  derived_day        INT or NULL
  year_error         BOOLEAN  - TRUE if year  could not be parsed
  month_error        BOOLEAN  - TRUE if month could not be parsed
  day_error          BOOLEAN  - TRUE if day   could not be parsed

Design note:
  The SAS macro generates inline data step code and sets multiple output
  variables.  Since Snowflake UDFs return a single value, we return a
  JSON object with all derived fields so the caller can extract whichever
  fields are needed.
=====================================================================*/

CREATE OR REPLACE FUNCTION DATE_IMPUTE(
    IN_DATE    DATE,
    IN_Y       VARCHAR,
    IN_M       VARCHAR,
    IN_D       VARCHAR,
    IMP_Y      INT       DEFAULT NULL,
    IMP_M      INT       DEFAULT 1,
    IMP_D      INT       DEFAULT 1,
    MONTH_FMT  VARCHAR   DEFAULT 'MM'
)
RETURNS VARIANT
LANGUAGE JAVASCRIPT
AS
$$
    // --------------- helper: parse month abbreviation ---------------
    var MONTH_ABBREVS = {
        'JAN':1, 'FEB':2, 'MAR':3, 'APR':4, 'MAY':5, 'JUN':6,
        'JUL':7, 'AUG':8, 'SEP':9, 'OCT':10,'NOV':11,'DEC':12
    };

    function parseMonth(val, fmt) {
        if (val === null || val === undefined) return { value: null, error: true };
        var s = String(val).trim().toUpperCase();
        if (s === '' || s === 'UNK' || s === 'UK' || s === 'NA' || s === '.') {
            return { value: null, error: true };
        }
        if (fmt === 'MON') {
            var abbr = s.substring(0, 3);
            if (MONTH_ABBREVS.hasOwnProperty(abbr)) {
                return { value: MONTH_ABBREVS[abbr], error: false };
            }
            return { value: null, error: true };
        }
        // MM format - numeric
        var n = parseInt(s, 10);
        if (isNaN(n) || n < 1 || n > 12) {
            return { value: null, error: true };
        }
        return { value: n, error: false };
    }

    function parseNumeric(val) {
        if (val === null || val === undefined) return { value: null, error: true };
        var s = String(val).trim().toUpperCase();
        if (s === '' || s === 'UNK' || s === 'UK' || s === 'NA' || s === '.') {
            return { value: null, error: true };
        }
        var n = parseInt(s, 10);
        if (isNaN(n)) {
            return { value: null, error: true };
        }
        return { value: n, error: false };
    }

    // --------------- derive working variables ---------------
    var yParsed = parseNumeric(IN_Y);
    var mParsed = parseMonth(IN_M, (MONTH_FMT || 'MM').toUpperCase());
    var dParsed = parseNumeric(IN_D);

    var derivedY = yParsed.value;
    var derivedM = mParsed.value;
    var derivedD = dParsed.value;

    var yError = yParsed.error;
    var mError = mParsed.error;
    var dError = dParsed.error;

    // Determine imputation flag (at least one component was missing)
    var imputedFlag = (derivedY === null || derivedM === null || derivedD === null);

    // Check whether imputation should be skipped
    // If IN_DATE is provided and not null, no imputation is needed
    var noImpute = (IMP_Y === null && IMP_M === null && IMP_D === null);

    var imputedDate = null;

    if (IN_DATE !== null && IN_DATE !== undefined) {
        // IN_DATE is present: only impute if it is null/missing
        // Since it is not null, return the original date
        imputedDate = IN_DATE;
        imputedFlag = false;
    } else if (!noImpute) {
        // Apply imputation rules
        if (derivedY === null && IMP_Y !== null) derivedY = IMP_Y;
        if (derivedM === null && IMP_M !== null) derivedM = IMP_M;
        if (derivedD === null && IMP_D !== null) derivedD = IMP_D;

        // Derive imputed date if all components are present
        if (derivedY !== null && derivedM !== null && derivedD !== null) {
            try {
                // JavaScript months are 0-indexed
                var dt = new Date(derivedY, derivedM - 1, derivedD);
                // Validate the date components match (catches invalid dates like Feb 30)
                if (dt.getFullYear() === derivedY &&
                    dt.getMonth() === derivedM - 1 &&
                    dt.getDate() === derivedD) {
                    // Format as YYYY-MM-DD string for Snowflake DATE
                    var mm = String(derivedM).padStart(2, '0');
                    var dd = String(derivedD).padStart(2, '0');
                    imputedDate = derivedY + '-' + mm + '-' + dd;
                }
            } catch (e) {
                imputedDate = null;
            }
        }
    }

    return {
        "imputed_date":  imputedDate,
        "imputed_flag":  imputedFlag,
        "derived_year":  derivedY,
        "derived_month": derivedM,
        "derived_day":   derivedD,
        "year_error":    yError,
        "month_error":   mError,
        "day_error":     dError
    };
$$;

COMMENT ON FUNCTION DATE_IMPUTE(DATE, VARCHAR, VARCHAR, VARCHAR, INT, INT, INT, VARCHAR)
IS 'Impute partial dates from character year/month/day components. Converted from SAS macro date_impute.sas.';


/*=====================================================================
Convenience wrapper: DATE_IMPUTE_DATE
Returns only the imputed date as a DATE value (instead of the full
VARIANT object).  Useful when callers only need the resulting date.
=====================================================================*/

CREATE OR REPLACE FUNCTION DATE_IMPUTE_DATE(
    IN_DATE    DATE,
    IN_Y       VARCHAR,
    IN_M       VARCHAR,
    IN_D       VARCHAR,
    IMP_Y      INT       DEFAULT NULL,
    IMP_M      INT       DEFAULT 1,
    IMP_D      INT       DEFAULT 1,
    MONTH_FMT  VARCHAR   DEFAULT 'MM'
)
RETURNS DATE
LANGUAGE SQL
AS
$$
    DATE_IMPUTE(IN_DATE, IN_Y, IN_M, IN_D, IMP_Y, IMP_M, IMP_D, MONTH_FMT):imputed_date::DATE
$$;

COMMENT ON FUNCTION DATE_IMPUTE_DATE(DATE, VARCHAR, VARCHAR, VARCHAR, INT, INT, INT, VARCHAR)
IS 'Convenience wrapper returning only the imputed DATE value.';


/*=====================================================================
Convenience wrapper: DATE_IMPUTE_FLAG
Returns only the imputation flag as a BOOLEAN.
=====================================================================*/

CREATE OR REPLACE FUNCTION DATE_IMPUTE_FLAG(
    IN_DATE    DATE,
    IN_Y       VARCHAR,
    IN_M       VARCHAR,
    IN_D       VARCHAR,
    IMP_Y      INT       DEFAULT NULL,
    IMP_M      INT       DEFAULT 1,
    IMP_D      INT       DEFAULT 1,
    MONTH_FMT  VARCHAR   DEFAULT 'MM'
)
RETURNS BOOLEAN
LANGUAGE SQL
AS
$$
    DATE_IMPUTE(IN_DATE, IN_Y, IN_M, IN_D, IMP_Y, IMP_M, IMP_D, MONTH_FMT):imputed_flag::BOOLEAN
$$;

COMMENT ON FUNCTION DATE_IMPUTE_FLAG(DATE, VARCHAR, VARCHAR, VARCHAR, INT, INT, INT, VARCHAR)
IS 'Convenience wrapper returning only the imputation flag BOOLEAN.';
