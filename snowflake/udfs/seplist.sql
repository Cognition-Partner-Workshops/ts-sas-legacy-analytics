/*=====================================================================
Snowflake UDF           : SEPLIST
Original SAS Macro      : seplist.sas
Purpose                 : Emit a list of words separated by a delimiter.
                          Converts a space-delimited (or custom-delimited)
                          list of items into a string with configurable
                          delimiter, prefix, suffix, and nesting characters.

Original Author         : Richard Devenezia / Scott Bass
Snowflake Conversion    : Auto-converted from SAS macro

Parameters (mirror the original SAS macro interface):
  ITEMS    VARCHAR  - The input list of items (REQ)
  INDLM    VARCHAR  - Input delimiter between items (default: space)
  DLM      VARCHAR  - Output delimiter between items (default: comma)
  PREFIX   VARCHAR  - String to place before each item (default: empty)
  NEST     VARCHAR  - Nesting shortcut: Q (single quotes), QQ (double
                      quotes), P (parentheses), C (curly braces),
                      B (brackets).  Overrides PREFIX/SUFFIX.
  SUFFIX   VARCHAR  - String to place after each item (default: empty)
  TRIM_FLAG BOOLEAN - Whether to trim whitespace from each item (default: TRUE)

Returns: VARCHAR - The formatted, delimited list.
=====================================================================*/

CREATE OR REPLACE FUNCTION SEPLIST(
    ITEMS       VARCHAR,
    INDLM       VARCHAR DEFAULT ' ',
    DLM         VARCHAR DEFAULT ',',
    PREFIX      VARCHAR DEFAULT '',
    NEST        VARCHAR DEFAULT '',
    SUFFIX      VARCHAR DEFAULT '',
    TRIM_FLAG   BOOLEAN DEFAULT TRUE
)
RETURNS VARCHAR
LANGUAGE JAVASCRIPT
STRICT
AS
$$
    // Validate required parameter
    if (ITEMS === null || ITEMS === undefined || ITEMS === '') {
        return '';
    }

    var prefix = PREFIX || '';
    var suffix = SUFFIX || '';
    var indlm  = INDLM || ' ';
    var dlm    = DLM || ',';
    var nest   = (NEST || '').toUpperCase();

    // Apply nesting shortcuts (overrides prefix/suffix)
    switch (nest) {
        case 'Q':
            prefix = prefix + "'";
            suffix = "'" + suffix;
            break;
        case 'QQ':
            prefix = prefix + '"';
            suffix = '"' + suffix;
            break;
        case 'P':
            prefix = prefix + '(';
            suffix = ')' + suffix;
            break;
        case 'C':
            prefix = prefix + '{';
            suffix = '}' + suffix;
            break;
        case 'B':
            prefix = prefix + '[';
            suffix = ']' + suffix;
            break;
        default:
            break;
    }

    // Split items by the input delimiter
    var parts = ITEMS.split(indlm);

    // Optionally trim each item and filter out empty items
    var result = [];
    for (var i = 0; i < parts.length; i++) {
        var item = parts[i];
        if (TRIM_FLAG) {
            item = item.trim();
        }
        if (item !== '') {
            result.push(prefix + item + suffix);
        }
    }

    return result.join(dlm);
$$;

COMMENT ON FUNCTION SEPLIST(VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, BOOLEAN)
IS 'Emit a list of words separated by a delimiter. Converted from SAS macro seplist.sas.';
