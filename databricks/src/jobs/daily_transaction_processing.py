"""U2 — conversion of Programs/Banking/daily_transaction_processing.sas.

PIPELINE/SQL profile: Spark SQL over
sas_legacy.sas_bronze.txn_feed_YYYYMMDD and sas_legacy.sas_silver.cust_accounts_daily
writing sas_legacy.sas_silver.daily_transactions, running_balances, txn_anomalies, and
txn_rejected.

Literal Base SAS semantics are the parity target:
- ``REJECT_REASON`` is dropped from both validation outputs (AMB-02).
- ``PROC APPEND FORCE`` targets the ten-column base schema (AMB-03).
- SAS missing values compare low for overdraft and withdrawal checks (AMB-06).
- ``HAVING ANOMALY_TYPE ne ''`` is a row filter (AMB-09).
- Anomaly statistics use the pre-append history, excluding the current feed on reruns
  (AMB-13).
- ``txn_rejected`` is wholesale-overwritten without a date discriminator (DEC-016).

Idempotency: history is seeded only when ``daily_transactions`` is empty and valid feed
rows are inserted with an insert-only ``MERGE``. ``running_balances`` and ``txn_anomalies``
replace the business-date slice, while ``txn_rejected`` is wholesale-overwritten.
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

FEED_COLUMNS: tuple[tuple[str, str], ...] = (
    ("transaction_id", "STRING"),
    ("account_id", "STRING"),
    ("transaction_date", "DATE"),
    ("transaction_type", "STRING"),
    ("transaction_amount", "DECIMAL(18,2)"),
    ("channel", "STRING"),
    ("merchant_category", "STRING"),
    ("description", "STRING"),
    ("post_date", "DATE"),
    ("currency_code", "STRING"),
)
FEED_COLUMN_NAMES = tuple(c for c, _ in FEED_COLUMNS)
ENRICH_COLUMNS: tuple[tuple[str, str], ...] = (
    ("account_type", "STRING"),
    ("customer_id", "STRING"),
    ("customer_segment", "STRING"),
    ("region_code", "STRING"),
    ("branch_id", "STRING"),
    ("pre_txn_balance", "DECIMAL(18,2)"),
    ("post_txn_balance", "DECIMAL(18,2)"),
    ("risk_rating", "INT"),
    ("running_balance", "DECIMAL(18,2)"),
    ("avg_txn_amt", "DOUBLE"),
    ("std_txn_amt", "DOUBLE"),
    ("z_score", "DOUBLE"),
    ("anomaly_type", "STRING"),
)
ENRICH_COLUMN_NAMES = tuple(c for c, _ in ENRICH_COLUMNS)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

VALID_TYPES = ("DEP", "WDR", "TRF", "PMT", "FEE", "INT", "ADJ", "REV", "CHG", "REF")
CREDIT_TYPES = ("DEP", "INT", "REF", "REV")
DEBIT_TYPES = ("WDR", "PMT", "FEE", "CHG")
TRANSFER_TYPES = ("TRF", "ADJ")
REJECT_PREDICATE = """(transaction_id IS NULL OR TRIM(transaction_id) = '')
OR (account_id IS NULL OR TRIM(account_id) = '')
OR transaction_amount IS NULL
OR ABS(transaction_amount) > 10000000
OR transaction_type IS NULL OR transaction_type NOT IN ({valid_types})
OR transaction_date > {d}"""


class FeedMissingError(RuntimeError):
    """Raised when the business-date transaction feed is unavailable."""


def _sql_list(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


def parse_business_date(value: str) -> date:
    if not _DATE_RE.match(value):
        raise ValueError(f"business_date must be YYYY-MM-DD, got {value!r}")
    return date.fromisoformat(value)


def _feed_columns_sql(prefix: str = "") -> str:
    return ", ".join(f"{prefix}{c}" for c in FEED_COLUMN_NAMES)


def feed_table(business_date: date, catalog: str = CATALOG) -> str:
    return f"{catalog}.{BRONZE}.txn_feed_{business_date:%Y%m%d}"


def _reject_predicate(business_date: date) -> str:
    return REJECT_PREDICATE.format(
        valid_types=_sql_list(VALID_TYPES),
        d=f"DATE'{business_date.isoformat()}'",
    )


def ddl(catalog: str = CATALOG) -> list[str]:
    feed_cols = ",\n  ".join(f"{c} {t}" for c, t in FEED_COLUMNS)
    anomaly_cols = ",\n  ".join(
        f"{c} {t}" for c, t in FEED_COLUMNS + ENRICH_COLUMNS
    )
    running_cols = ",\n  ".join(
        f"{c} {t}"
        for c, t in (
            ("account_id", "STRING"),
            ("transaction_date", "DATE"),
            ("transaction_id", "STRING"),
            ("running_balance", "DECIMAL(18,2)"),
        )
    )
    return [
        (
            f"CREATE TABLE IF NOT EXISTS {catalog}.{SILVER}.daily_transactions (\n  "
            f"{feed_cols}\n) USING DELTA"
        ),
        (
            f"CREATE TABLE IF NOT EXISTS {catalog}.{SILVER}.running_balances (\n  "
            f"{running_cols}\n) USING DELTA"
        ),
        (
            f"CREATE TABLE IF NOT EXISTS {catalog}.{SILVER}.txn_anomalies (\n  "
            f"{anomaly_cols}\n) USING DELTA"
        ),
        (
            f"CREATE TABLE IF NOT EXISTS {catalog}.{SILVER}.txn_rejected (\n  "
            f"{feed_cols}\n) USING DELTA"
        ),
    ]


def feed_exists_sql(business_date: date, catalog: str = CATALOG) -> str:
    return (
        f"SELECT COUNT(*) AS n FROM {catalog}.information_schema.tables "
        "WHERE table_schema = 'sas_bronze' "
        f"AND table_name = 'txn_feed_{business_date:%Y%m%d}'"
    )


def silver_count_sql(catalog: str = CATALOG) -> str:
    return f"SELECT COUNT(*) AS n FROM {catalog}.{SILVER}.daily_transactions"


def seed_history_sql(catalog: str = CATALOG) -> str:
    cols = _feed_columns_sql()
    return (
        f"INSERT INTO {catalog}.{SILVER}.daily_transactions ({cols}) "
        f"SELECT {cols} FROM {catalog}.{BRONZE}.daily_transactions_hist"
    )


def base_cte(business_date: date, catalog: str = CATALOG) -> str:
    d = f"DATE'{business_date.isoformat()}'"
    feed = feed_table(business_date, catalog)
    return f"""WITH validated AS (
  SELECT {_feed_columns_sql()} FROM {feed} WHERE NOT ({_reject_predicate(business_date)})
),
enriched AS (
  SELECT t.*, a.account_type, a.customer_id, a.customer_segment, a.region_code, a.branch_id,
         a.current_balance AS pre_txn_balance,
         CASE WHEN t.transaction_type IN ({_sql_list(CREDIT_TYPES)}) THEN a.current_balance + t.transaction_amount
              WHEN t.transaction_type IN ({_sql_list(DEBIT_TYPES)}) THEN a.current_balance - ABS(t.transaction_amount)
              WHEN t.transaction_type IN ({_sql_list(TRANSFER_TYPES)}) THEN a.current_balance + t.transaction_amount
              ELSE a.current_balance END AS post_txn_balance,
         a.risk_rating,
         CASE WHEN t.transaction_type IN ({_sql_list(CREDIT_TYPES)}) THEN t.transaction_amount
              WHEN t.transaction_type IN ({_sql_list(DEBIT_TYPES)}) THEN -ABS(t.transaction_amount)
              WHEN t.transaction_type IN ({_sql_list(TRANSFER_TYPES)}) THEN t.transaction_amount
              ELSE CAST(0 AS DECIMAL(18,2)) END AS signed_amount
  FROM validated t
  LEFT JOIN {catalog}.{SILVER}.cust_accounts_daily a
    ON t.account_id = a.account_id AND a.snapshot_date = {d}
),
with_balance AS (
  SELECT e.*,
         e.pre_txn_balance + SUM(e.signed_amount) OVER (PARTITION BY e.account_id ORDER BY e.transaction_date, e.transaction_id ROWS UNBOUNDED PRECEDING) AS running_balance
  FROM enriched e
)"""


def stats_cte(business_date: date, catalog: str = CATALOG) -> str:
    d = f"DATE'{business_date.isoformat()}'"
    feed_cols = _feed_columns_sql("e.")
    z_expr = (
        "CASE WHEN s.std_txn_amt > 0 "
        "THEN (CAST(ABS(e.transaction_amount) AS DOUBLE) - s.avg_txn_amt) / s.std_txn_amt "
        "ELSE CAST(NULL AS DOUBLE) END"
    )
    return f""",
txn_stats AS (
  SELECT account_id,
         AVG(CAST(ABS(transaction_amount) AS DOUBLE)) AS avg_txn_amt,
         STDDEV_SAMP(CAST(ABS(transaction_amount) AS DOUBLE)) AS std_txn_amt,
         COUNT(*) AS txn_count
  FROM {catalog}.{SILVER}.daily_transactions h
  WHERE h.transaction_date >= DATE_SUB({d}, 90)
    AND NOT EXISTS (SELECT 1 FROM validated v WHERE v.transaction_id = h.transaction_id)
  GROUP BY account_id
),
anomalies AS (
  SELECT {feed_cols}, e.account_type, e.customer_id, e.customer_segment, e.region_code, e.branch_id,
         CAST(e.pre_txn_balance AS DECIMAL(18,2)) AS pre_txn_balance,
         CAST(e.post_txn_balance AS DECIMAL(18,2)) AS post_txn_balance,
         e.risk_rating, CAST(e.running_balance AS DECIMAL(18,2)) AS running_balance,
         s.avg_txn_amt, s.std_txn_amt,
         {z_expr} AS z_score,
         CASE WHEN ({z_expr}) > 3 THEN 'HIGH_AMOUNT'
              WHEN e.running_balance IS NULL OR e.running_balance < 0 THEN 'OVERDRAFT'
              WHEN e.transaction_type = 'WDR'
                AND (e.pre_txn_balance IS NULL OR ABS(e.transaction_amount) > e.pre_txn_balance * 0.9) THEN 'LARGE_WITHDRAWAL'
              WHEN e.customer_id IS NULL THEN 'ORPHAN_ACCOUNT'
              ELSE '' END AS anomaly_type
  FROM with_balance e LEFT JOIN txn_stats s ON e.account_id = s.account_id
)"""


def running_balances_sql(business_date: date, catalog: str = CATALOG) -> str:
    d = f"DATE'{business_date.isoformat()}'"
    return (
        f"INSERT INTO {catalog}.{SILVER}.running_balances\n"
        f"REPLACE WHERE transaction_date = {d}\n"
        f"{base_cte(business_date, catalog)}\n"
        "SELECT account_id, transaction_date, transaction_id, "
        "CAST(running_balance AS DECIMAL(18,2)) AS running_balance FROM with_balance"
    )


def anomalies_sql(business_date: date, catalog: str = CATALOG) -> str:
    d = f"DATE'{business_date.isoformat()}'"
    cols = ", ".join(FEED_COLUMN_NAMES + ENRICH_COLUMN_NAMES)
    return (
        f"INSERT INTO {catalog}.{SILVER}.txn_anomalies\n"
        f"REPLACE WHERE transaction_date = {d}\n"
        f"{base_cte(business_date, catalog)}{stats_cte(business_date, catalog)}\n"
        f"SELECT {cols} FROM anomalies WHERE anomaly_type <> ''"
    )


def append_sql(business_date: date, catalog: str = CATALOG) -> str:
    cols = _feed_columns_sql()
    source_cols = _feed_columns_sql("s.")
    return (
        f"MERGE INTO {catalog}.{SILVER}.daily_transactions b\n"
        f"USING (\n{base_cte(business_date, catalog)}\n"
        f"SELECT {cols} FROM with_balance) s\n"
        "ON b.transaction_id = s.transaction_id\n"
        f"WHEN NOT MATCHED THEN INSERT ({cols}) VALUES ({source_cols})"
    )


def rejected_sql(business_date: date, catalog: str = CATALOG) -> str:
    return (
        f"INSERT OVERWRITE {catalog}.{SILVER}.txn_rejected\n"
        f"SELECT {_feed_columns_sql()} FROM {feed_table(business_date, catalog)} "
        f"WHERE {_reject_predicate(business_date)}"
    )


def statements(business_date: date, catalog: str = CATALOG) -> list[str]:
    return [
        running_balances_sql(business_date, catalog),
        anomalies_sql(business_date, catalog),
        append_sql(business_date, catalog),
        rejected_sql(business_date, catalog),
    ]


def _scalar(result: object) -> int:
    rows = result.collect() if hasattr(result, "collect") else result
    first = rows[0]
    cell = next(iter(first.values())) if isinstance(first, dict) else first[0]
    return int(cell)


def run(
    execute: Callable[[str], object],
    business_date: str,
    catalog: str = CATALOG,
) -> list[str]:
    bd = parse_business_date(validate_param("txn_date", business_date, required=True))
    feed = feed_table(bd, catalog)
    if _scalar(execute(feed_exists_sql(bd, catalog))) == 0:
        raise FeedMissingError(
            f"ERROR: Feed dataset {feed} not found; check upstream file transfer for {business_date}"
        )
    sqls = ddl(catalog)
    for sql in sqls:
        execute(sql)
    if _scalar(execute(silver_count_sql(catalog))) == 0:
        seed = seed_history_sql(catalog)
        execute(seed)
        sqls.append(seed)
    loads = statements(bd, catalog)
    for sql in loads:
        execute(sql)
    sqls.extend(loads)
    return sqls


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--business-date", required=True)
    ap.add_argument("--report-month", default=None)
    ap.add_argument("--region", default="ALL")
    ap.add_argument("--abort-on-err", default="Y")
    ap.add_argument("--executor", choices=["spark", "warehouse"], default="spark",
                    help="warehouse: Statement Execution API (ad hoc CLI run, no cluster)")
    ap.add_argument("--warehouse-id", default=os.environ.get("RECON_WAREHOUSE_ID", "565cd2fd713738c4"))
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
    n = len(run(execute, a.business_date))
    print(f"daily_transaction_processing: {n} statements, business_date={a.business_date}")
    return 0


if __name__ == "__main__":
    _rc = main()
    if _rc:
        raise SystemExit(_rc)
