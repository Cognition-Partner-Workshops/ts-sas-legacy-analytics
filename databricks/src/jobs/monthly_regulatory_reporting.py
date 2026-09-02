"""U4 — conversion of Programs/Banking/monthly_regulatory_reporting.sas."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
from calendar import monthrange
from collections.abc import Callable, Iterable, Mapping
from datetime import date
from pathlib import Path


def _src_root() -> str:
    """Find databricks/src when imported, scripted, or run by a Spark task."""
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

from sas_macros.export_xlsx import export_xlsx
from sas_macros.parmv import validate_param

CATALOG = os.environ.get("SAS_LEGACY_CATALOG", "sas_legacy")
GOLD = f"{CATALOG}.sas_gold"
LOAN_TYPES = ("MTG", "AUTO", "PERS", "CC", "LOC", "HELC")
WORKBOOK_SHEETS = (
    ("monthly_rwa", "RWA"),
    ("delinquency_aging", "Delinquency"),
    ("llp_coverage", "LLP_Coverage"),
)

_REPORT_MONTH_RE = re.compile(r"^\d{6}$")
_REPORT_COLUMNS: dict[str, tuple[str, ...]] = {
    "monthly_rwa": (
        "report_month", "account_type", "customer_segment", "risk_weight",
        "n_accounts", "total_exposure", "rwa",
    ),
    "delinquency_aging": (
        "report_month", "account_type", "region_code", "delinq_bucket",
        "n_accounts", "total_balance", "total_past_due",
    ),
    "llp_coverage": (
        "report_month", "account_type", "n_loans", "gross_loans",
        "total_allowance", "coverage_pct", "npl_balance", "npl_coverage_pct",
    ),
    "capital_adequacy": (
        "report_month", "total_rwa", "cet1_capital", "tier1_capital",
        "total_capital", "cet1_ratio", "tier1_ratio", "total_capital_ratio",
        "cet1_status", "tier1_status", "total_capital_status",
    ),
}


def parse_report_month(value: str) -> tuple[str, date]:
    """Validate YYYYMM and return it with the month's final calendar date."""
    if not isinstance(value, str) or not _REPORT_MONTH_RE.fullmatch(value):
        raise ValueError(f"report_month must be 6 digits YYYYMM, got {value!r}")
    try:
        year, month = int(value[:4]), int(value[4:])
        month_end = date(year, month, monthrange(year, month)[1])
    except ValueError as exc:
        raise ValueError(f"report_month must be 6 digits YYYYMM, got {value!r}") from exc
    return value, month_end


def _date_text(value: date | str) -> str:
    return value.isoformat() if isinstance(value, date) else str(value)


def ddl() -> list[str]:
    definitions = {
        "monthly_rwa": """
  report_month STRING,
  account_type STRING,
  customer_segment STRING,
  risk_weight DECIMAL(4,2),
  n_accounts BIGINT,
  total_exposure DECIMAL(28,2),
  rwa DECIMAL(28,4)""",
        "delinquency_aging": """
  report_month STRING,
  account_type STRING,
  region_code STRING,
  delinq_bucket STRING,
  n_accounts BIGINT,
  total_balance DECIMAL(28,2),
  total_past_due DECIMAL(28,2)""",
        "llp_coverage": """
  report_month STRING,
  account_type STRING,
  n_loans BIGINT,
  gross_loans DECIMAL(28,2),
  total_allowance DECIMAL(28,2),
  coverage_pct DOUBLE,
  npl_balance DECIMAL(28,2),
  npl_coverage_pct DOUBLE""",
        "capital_adequacy": """
  report_month STRING,
  total_rwa DECIMAL(28,4),
  cet1_capital DECIMAL(18,2),
  tier1_capital DECIMAL(18,2),
  total_capital DECIMAL(18,2),
  cet1_ratio DOUBLE,
  tier1_ratio DOUBLE,
  total_capital_ratio DOUBLE,
  cet1_status STRING,
  tier1_status STRING,
  total_capital_status STRING""",
    }
    return [
        f"CREATE TABLE IF NOT EXISTS {GOLD}.{table} ({columns}\n) USING DELTA"
        for table, columns in definitions.items()
    ]


def rwa_sql(report_month: str, month_end: date | str) -> str:
    rm, end = report_month, _date_text(month_end)
    return f"""INSERT INTO {GOLD}.monthly_rwa
REPLACE WHERE report_month = '{rm}'
WITH scored AS (
  SELECT
    a.account_type,
    a.customer_segment,
    a.current_balance,
    CASE
      WHEN a.account_type IN ('CHK','SAV','MMA') THEN 0.00
      WHEN a.account_type = 'CD' THEN 0.00
      WHEN a.account_type = 'MTG' AND l.ltv <= 0.80 THEN 0.35
      WHEN a.account_type = 'MTG' AND l.ltv > 0.80 THEN 0.50
      WHEN a.account_type = 'HELC' THEN 0.50
      WHEN a.account_type IN ('AUTO','PERS') THEN 0.75
      WHEN a.account_type = 'CC' THEN 0.75
      WHEN a.account_type = 'LOC' THEN 1.00
      ELSE 1.00
    END AS risk_weight
  FROM {CATALOG}.sas_silver.cust_accounts_daily a
  LEFT JOIN {CATALOG}.sas_bronze.loan_details l
    ON a.account_id = l.account_id
  WHERE a.snapshot_date = DATE'{end}'
)
SELECT
  '{rm}' AS report_month,
  account_type,
  customer_segment,
  risk_weight,
  COUNT(*) AS n_accounts,
  SUM(current_balance) AS total_exposure,
  SUM(current_balance * risk_weight) AS rwa
FROM scored
GROUP BY account_type, customer_segment, risk_weight"""


def delinquency_sql(report_month: str, month_end: date | str) -> str:
    rm, end = report_month, _date_text(month_end)
    types = ", ".join(f"'{kind}'" for kind in LOAN_TYPES)
    return f"""INSERT INTO {GOLD}.delinquency_aging
REPLACE WHERE report_month = '{rm}'
WITH scored AS (
  SELECT
    a.account_type,
    a.region_code,
    a.current_balance,
    l.past_due_amount,
    CASE
      WHEN l.days_past_due = 0 THEN 'Current'
      WHEN l.days_past_due BETWEEN 1 AND 29 THEN '1-29'
      WHEN l.days_past_due BETWEEN 30 AND 59 THEN '30-59'
      WHEN l.days_past_due BETWEEN 60 AND 89 THEN '60-89'
      WHEN l.days_past_due BETWEEN 90 AND 119 THEN '90-119'
      WHEN l.days_past_due BETWEEN 120 AND 179 THEN '120-179'
      WHEN l.days_past_due >= 180 THEN '180+'
      ELSE 'Unknown'
    END AS delinq_bucket
  FROM {CATALOG}.sas_silver.cust_accounts_daily a
  LEFT JOIN {CATALOG}.sas_bronze.loan_details l
    ON a.account_id = l.account_id
  WHERE a.snapshot_date = DATE'{end}'
    AND a.account_type IN ({types})
)
SELECT
  '{rm}' AS report_month,
  account_type,
  region_code,
  delinq_bucket,
  COUNT(*) AS n_accounts,
  SUM(current_balance) AS total_balance,
  SUM(past_due_amount) AS total_past_due
FROM scored
GROUP BY account_type, region_code, delinq_bucket"""


def llp_sql(report_month: str, month_end: date | str) -> str:
    rm, end = report_month, _date_text(month_end)
    types = ", ".join(f"'{kind}'" for kind in LOAN_TYPES)
    return f"""INSERT INTO {GOLD}.llp_coverage
REPLACE WHERE report_month = '{rm}'
WITH agg AS (
  SELECT
    a.account_type,
    COUNT(*) AS n_loans,
    SUM(a.current_balance) AS gross_loans,
    SUM(l.allowance_amt) AS total_allowance,
    SUM(CASE WHEN l.days_past_due >= 90 THEN a.current_balance ELSE 0 END) AS npl_balance
  FROM {CATALOG}.sas_silver.cust_accounts_daily a
  INNER JOIN {CATALOG}.sas_bronze.loan_details l
    ON a.account_id = l.account_id
  WHERE a.snapshot_date = DATE'{end}'
    AND a.account_type IN ({types})
  GROUP BY a.account_type
)
SELECT
  '{rm}' AS report_month,
  account_type,
  n_loans,
  gross_loans,
  total_allowance,
  CASE WHEN gross_loans > 0
    THEN CAST(total_allowance AS DOUBLE) / CAST(gross_loans AS DOUBLE) * 100
    ELSE 0
  END AS coverage_pct,
  npl_balance,
  CASE WHEN npl_balance > 0
    THEN CAST(total_allowance AS DOUBLE) / CAST(npl_balance AS DOUBLE) * 100
    ELSE 0
  END AS npl_coverage_pct
FROM agg"""


def capital_sql(report_month: str) -> str:
    rm = report_month
    return f"""INSERT INTO {GOLD}.capital_adequacy
REPLACE WHERE report_month = '{rm}'
WITH t AS (
  SELECT SUM(rwa) AS total_rwa
  FROM {GOLD}.monthly_rwa
  WHERE report_month = '{rm}'
)
SELECT
  '{rm}' AS report_month,
  total_rwa,
  50000000 AS cet1_capital,
  65000000 AS tier1_capital,
  80000000 AS total_capital,
  CASE WHEN total_rwa > 0
    THEN 50000000 / CAST(total_rwa AS DOUBLE) * 100
    ELSE CAST(NULL AS DOUBLE)
  END AS cet1_ratio,
  CASE WHEN total_rwa > 0
    THEN 65000000 / CAST(total_rwa AS DOUBLE) * 100
    ELSE CAST(NULL AS DOUBLE)
  END AS tier1_ratio,
  CASE WHEN total_rwa > 0
    THEN 80000000 / CAST(total_rwa AS DOUBLE) * 100
    ELSE CAST(NULL AS DOUBLE)
  END AS total_capital_ratio,
  CASE WHEN total_rwa = 0 THEN 'PASS'
    WHEN 50000000 / CAST(total_rwa AS DOUBLE) * 100 >= 4.5 THEN 'PASS'
    ELSE 'FAIL'
  END AS cet1_status,
  CASE WHEN total_rwa = 0 THEN 'PASS'
    WHEN 65000000 / CAST(total_rwa AS DOUBLE) * 100 >= 6.0 THEN 'PASS'
    ELSE 'FAIL'
  END AS tier1_status,
  CASE WHEN total_rwa = 0 THEN 'PASS'
    WHEN 80000000 / CAST(total_rwa AS DOUBLE) * 100 >= 8.0 THEN 'PASS'
    ELSE 'FAIL'
  END AS total_capital_status
FROM t"""


def export_sql(table: str, report_month: str) -> str:
    order = {
        "monthly_rwa": "account_type, customer_segment, risk_weight",
        "delinquency_aging": "account_type, region_code, delinq_bucket",
        "llp_coverage": "account_type",
    }[table]
    columns = ", ".join(_REPORT_COLUMNS[table])
    return (
        f"SELECT {columns} FROM {GOLD}.{table} "
        f"WHERE report_month='{report_month}' ORDER BY {order}"
    )


def _publish_local(src: str, dst: str) -> None:
    destination = Path(dst)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    shutil.copyfile(src, destination)


def run(
    execute: Callable[[str], object],
    fetch: Callable[[str], Iterable[Mapping[str, object]]],
    report_month: str,
    business_date: date | str,
    workbook_path: str,
    write_sheet: Callable[[Iterable[Mapping[str, object]], str, str], str] = export_xlsx,
    publish: Callable[[str, str], None] = _publish_local,
) -> dict[str, object]:
    rm, month_end = parse_report_month(
        validate_param("report_month", report_month, required=True)
    )
    bd = validate_param("business_date", _date_text(business_date), required=True)
    date.fromisoformat(bd)
    statements = ddl()
    for statement in statements:
        execute(statement)
    execute(rwa_sql(rm, month_end))
    execute(delinquency_sql(rm, month_end))
    execute(llp_sql(rm, month_end))

    sheets_written: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        local = Path(tmp) / Path(workbook_path).name
        for table, sheet in WORKBOOK_SHEETS:
            rows = fetch(export_sql(table, rm))
            write_sheet(rows, str(local), sheet)
            sheets_written.append(sheet)
        publish(str(local), workbook_path)

    execute(capital_sql(rm))
    return {
        "statements_run": len(statements) + 4,
        "sheets_written": sheets_written,
        "path": workbook_path,
    }


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--business-date", required=True)
    ap.add_argument("--report-month", required=True)
    ap.add_argument("--region", default="ALL")
    ap.add_argument("--abort-on-err", default="Y")
    ap.add_argument("--executor", choices=["spark", "warehouse"], default="spark")
    ap.add_argument(
        "--warehouse-id",
        default=os.environ.get("RECON_WAREHOUSE_ID", "565cd2fd713738c4"),
    )
    ap.add_argument("--report-path", default=None, help="directory for the report workbook")
    ns, _unknown = ap.parse_known_args(argv)
    return ns


def _report_path(report_month: str, report_dir: str | None) -> str:
    directory = report_dir or f"/Volumes/{CATALOG}/sas_bronze/landing/reports"
    return str(Path(directory) / f"REG_REPORT_{report_month}.xlsx")


def main(argv: list[str] | None = None) -> int:
    a = _parse_args(argv)
    report_month, _month_end = parse_report_month(
        validate_param("report_month", a.report_month, required=True)
    )
    business_date = date.fromisoformat(
        validate_param("business_date", a.business_date, required=True)
    )
    region = validate_param("region", a.region, allowed="ALL NE SE MW SW W NW", default="ALL")
    validate_param("abort_on_err", a.abort_on_err)
    del region

    if a.executor == "warehouse":
        sys.path.insert(0, os.path.join(_SRC, ".."))
        from recon.warehouse import Warehouse

        wh = Warehouse(a.warehouse_id)
        remote_path = _report_path(report_month, a.report_path)
        result = run(
            wh.query,
            wh.fetch,
            report_month,
            business_date,
            remote_path,
            publish=wh.upload_file,
        )
    else:
        from pyspark.sql import SparkSession

        spark = SparkSession.builder.getOrCreate()

        def fetch(sql: str) -> list[dict[str, object]]:
            return [row.asDict(recursive=True) for row in spark.sql(sql).collect()]

        result = run(
            spark.sql,
            fetch,
            report_month,
            business_date,
            _report_path(report_month, a.report_path),
        )
    print(
        f"monthly_regulatory_reporting: {result['statements_run']} statements, "
        f"sheets={result['sheets_written']} path={result['path']}"
    )
    return 0


if __name__ == "__main__":
    _rc = main()
    if _rc:
        raise SystemExit(_rc)
