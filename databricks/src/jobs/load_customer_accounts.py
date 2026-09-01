"""U1 — conversion of Programs/Banking/load_customer_accounts.sas (%load_customer_accounts).

PIPELINE/SQL profile: Spark SQL over sas_legacy.sas_bronze.{cust_accounts,cust_demographics}
writing sas_legacy.sas_silver.{cust_accounts_daily,acct_exceptions}.

Literal Base SAS semantics are the parity target (DEC-015 (a)):
- ``intck('month', OPEN_DATE, run_date)`` is a calendar-boundary month count.
- ``ACCT_AGE_MONTHS`` / ``DAYS_INACTIVE`` / ``UTILIZATION_PCT`` propagate missing.
- SAS missing compares low: ``. < 0`` and ``. <= date`` are TRUE, ``. > x`` is FALSE.
- Exception rows are ``OUTPUT`` before ``SNAPSHOT_DATE`` / ``LOAD_TIMESTAMP`` are assigned
  (AMB-05) so both are NULL on ``acct_exceptions``; an account can emit up to three rows.
- ``drop EXCEPTION_CODE EXCEPTION_DESC`` is a DATA-step statement and applies to every
  OUTPUT data set (AMB-01), so both targets share the same 29 columns.

Idempotency: ``cust_accounts_daily`` is replaced for ``snapshot_date = business_date``
(Delta ``REPLACE WHERE``). ``acct_exceptions`` carries no business-date discriminator in the
literal schema (snapshot_date is NULL, AMB-05) and is overwritten wholesale.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Callable
from datetime import date


def _src_root() -> str:
    """databricks/src, whether imported, run as a script, or exec'd by a serverless
    spark_python_task (which defines neither __file__ nor a package context)."""
    candidates = [globals().get("__file__"), sys.argv[0] if sys.argv else None, os.getcwd()]
    for c in candidates:
        if not c:
            continue
        p = os.path.abspath(c)
        if os.path.isfile(p):
            p = os.path.dirname(p)
        for _ in range(3):
            if os.path.isdir(os.path.join(p, "sas_macros")):
                return p
            p = os.path.dirname(p)
    return os.path.join(os.getcwd(), "..")


_SRC = _src_root()
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from sas_macros.parmv import validate_param

CATALOG = os.environ.get("SAS_LEGACY_CATALOG", "sas_legacy")
BRONZE = "sas_bronze"
SILVER = "sas_silver"

COLUMNS: tuple[tuple[str, str], ...] = (
    ("account_id", "STRING"),
    ("customer_id", "STRING"),
    ("account_type", "STRING"),
    ("account_status", "STRING"),
    ("open_date", "DATE"),
    ("close_date", "DATE"),
    ("current_balance", "DECIMAL(18,2)"),
    ("available_balance", "DECIMAL(18,2)"),
    ("credit_limit", "DECIMAL(18,2)"),
    ("interest_rate", "DOUBLE"),
    ("branch_id", "STRING"),
    ("officer_id", "STRING"),
    ("last_activity_date", "DATE"),
    ("first_name", "STRING"),
    ("last_name", "STRING"),
    ("ssn_hash", "STRING"),
    ("date_of_birth", "DATE"),
    ("customer_segment", "STRING"),
    ("risk_rating", "INT"),
    ("region_code", "STRING"),
    ("primary_email", "STRING"),
    ("phone_number", "STRING"),
    ("acct_age_months", "INT"),
    ("days_inactive", "INT"),
    ("utilization_pct", "DOUBLE"),
    ("dormancy_flag", "STRING"),
    ("high_balance_flag", "STRING"),
    ("snapshot_date", "DATE"),
    ("load_timestamp", "TIMESTAMP"),
)
COLUMN_NAMES = tuple(c for c, _ in COLUMNS)
_SOURCE_COLUMNS = COLUMN_NAMES[:22]
_DERIVED = ("acct_age_months", "days_inactive", "utilization_pct", "dormancy_flag", "high_balance_flag")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

DEPOSIT_TYPES = ("CHK", "SAV", "MMA", "CD")
CREDIT_TYPES = ("CC", "LOC", "HELC")
EXCLUDED_STATUSES = ("W", "C")
REGIONS = "ALL NE SE MW SW W NW"  # %parmv(region, _val=...)


def _sql_list(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


def parse_business_date(value: str) -> date:
    if not _DATE_RE.match(value):
        raise ValueError(f"business_date must be YYYY-MM-DD, got {value!r}")
    return date.fromisoformat(value)


def ddl(catalog: str = CATALOG) -> list[str]:
    cols = ",\n  ".join(f"{c} {t}" for c, t in COLUMNS)
    return [
        f"CREATE TABLE IF NOT EXISTS {catalog}.{SILVER}.cust_accounts_daily (\n  {cols}\n) USING DELTA",
        f"CREATE TABLE IF NOT EXISTS {catalog}.{SILVER}.acct_exceptions (\n  {cols}\n) USING DELTA",
    ]


def base_cte(business_date: date, region: str, catalog: str = CATALOG) -> str:
    """WORK.ACCT_RAW join/filter plus the DATA-step derived columns (before any OUTPUT)."""
    d = f"DATE'{business_date.isoformat()}'"
    region_filter = "" if region == "ALL" else f"\n    AND d.region_code = '{region}'"
    src_cols = ",\n      ".join(
        f"{'a' if i < 13 else 'd'}.{c}" for i, c in enumerate(_SOURCE_COLUMNS)
    )
    return f"""
WITH acct_raw AS (
  SELECT
      {src_cols}
  FROM {catalog}.{BRONZE}.cust_accounts a
  INNER JOIN {catalog}.{BRONZE}.cust_demographics d
    ON a.customer_id = d.customer_id
  WHERE (a.account_status IS NULL OR a.account_status NOT IN ({_sql_list(EXCLUDED_STATUSES)}))
    AND (a.open_date IS NULL OR a.open_date <= {d}){region_filter}
),
derived AS (
  SELECT
      r.*,
      CAST((YEAR({d}) * 12 + MONTH({d})) - (YEAR(open_date) * 12 + MONTH(open_date)) AS INT)
        AS acct_age_months,
      CAST(DATEDIFF({d}, last_activity_date) AS INT) AS days_inactive,
      CASE
        WHEN account_type IN ({_sql_list(CREDIT_TYPES)}) AND credit_limit > 0
          THEN (CAST(current_balance AS DOUBLE) / CAST(credit_limit AS DOUBLE)) * 100
        ELSE CAST(NULL AS DOUBLE)
      END AS utilization_pct,
      CASE
        WHEN DATEDIFF({d}, last_activity_date) > 365 AND account_status = 'A' THEN 'Y'
        ELSE 'N'
      END AS dormancy_flag,
      CASE WHEN current_balance >= 250000 THEN 'Y' ELSE 'N' END AS high_balance_flag
  FROM acct_raw r
)"""


def snapshot_sql(business_date: date, region: str, catalog: str = CATALOG) -> str:
    """STG_BANK.CUST_ACCOUNTS_DAILY: every derived row, stamped at run time; replaces the
    business-date slice."""
    cols = ",\n      ".join(_SOURCE_COLUMNS + _DERIVED)
    return f"""INSERT INTO {catalog}.{SILVER}.cust_accounts_daily
REPLACE WHERE snapshot_date = DATE'{business_date.isoformat()}'
{base_cte(business_date, region, catalog)}
SELECT
      {cols},
      DATE'{business_date.isoformat()}' AS snapshot_date,
      CURRENT_TIMESTAMP() AS load_timestamp
FROM derived"""


def exceptions_sql(business_date: date, region: str, catalog: str = CATALOG) -> str:
    """WORK.ACCT_EXCEPTIONS: one full row per triggered rule, OUTPUT before the snapshot
    columns are assigned (AMB-05), exception code/desc dropped (AMB-01)."""
    cols = ",\n      ".join(_SOURCE_COLUMNS + _DERIVED)
    select = f"""SELECT
      {cols},
      CAST(NULL AS DATE) AS snapshot_date,
      CAST(NULL AS TIMESTAMP) AS load_timestamp
FROM derived"""
    rules = (
        # NEG_BAL: SAS `. < 0` is TRUE
        (f"account_type IN ({_sql_list(DEPOSIT_TYPES)}) "
         "AND (current_balance IS NULL OR current_balance < 0)"),
        # HIGH_UTIL: SAS `. > 95` is FALSE
        "utilization_pct > 95",
        # NO_RISK
        "risk_rating IS NULL",
    )
    body = "\nUNION ALL\n".join(f"{select}\nWHERE {r}" for r in rules)
    return (
        f"INSERT OVERWRITE {catalog}.{SILVER}.acct_exceptions\n"
        f"{base_cte(business_date, region, catalog)}\n{body}"
    )


def raw_count_sql(business_date: date, region: str, catalog: str = CATALOG) -> str:
    """%nobs(WORK.ACCT_RAW): the macro exits before Step 2 when the extract is empty."""
    return f"{base_cte(business_date, region, catalog)}\nSELECT COUNT(*) AS n FROM acct_raw"


def statements(business_date: date, region: str, catalog: str = CATALOG) -> list[str]:
    return ddl(catalog) + [
        snapshot_sql(business_date, region, catalog),
        exceptions_sql(business_date, region, catalog),
    ]


def _scalar(result: object) -> int:
    """First cell of a spark DataFrame, a list of dicts (Statement API) or a list of tuples."""
    rows = result.collect() if hasattr(result, "collect") else result
    first = rows[0]
    cell = next(iter(first.values())) if isinstance(first, dict) else first[0]
    return int(cell)


def run(execute: Callable[[str], object], business_date: str, region: str = "ALL",
        catalog: str = CATALOG) -> list[str]:
    bd = parse_business_date(validate_param("run_date", business_date, required=True))
    rg = validate_param("region", region, allowed=REGIONS, default="ALL")
    if _scalar(execute(raw_count_sql(bd, rg, catalog))) == 0:
        print("WARNING: No records extracted. Aborting.")
        return []
    sqls = statements(bd, rg, catalog)
    for s in sqls:
        execute(s)
    return sqls


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--business-date", required=True)
    ap.add_argument("--region", default="ALL")
    ap.add_argument("--executor", choices=["spark", "warehouse"], default="spark",
                    help="warehouse: Statement Execution API (ad hoc CLI run, no cluster)")
    ap.add_argument("--warehouse-id", default=os.environ.get("RECON_WAREHOUSE_ID", "565cd2fd713738c4"))
    # bundle passes the shared parameter set; the ones below are not used by U1
    ap.add_argument("--report-month", default=None)
    ap.add_argument("--abort-on-err", default="Y")
    ns, _unknown = ap.parse_known_args(argv)
    return ns


def main(argv: list[str] | None = None) -> int:
    a = _parse_args(argv)
    if a.executor == "warehouse":
        sys.path.insert(0, os.path.join(_SRC, ".."))
        from recon.warehouse import Warehouse

        wh = Warehouse(a.warehouse_id)
        execute = wh.query
    else:
        from pyspark.sql import SparkSession

        spark = SparkSession.builder.getOrCreate()
        execute = spark.sql
    n = len(run(execute, a.business_date, a.region))
    print(f"load_customer_accounts: {n} statements, business_date={a.business_date} region={a.region}")
    return 0


if __name__ == "__main__":
    _rc = main()
    if _rc:  # serverless spark_python_task reports any SystemExit (even 0) as a failure
        raise SystemExit(_rc)
