"""U3 — conversion of Programs/Banking/credit_risk_scoring.sas (%credit_risk_scoring).

ML-SCORING profile: Spark SQL over sas_legacy.sas_silver.cust_accounts_daily (U1) and
sas_legacy.sas_bronze.{bureau_scores,payment_history,collateral} writing
sas_legacy.sas_silver.{risk_scores,risk_migration} and sas_legacy.sas_gold.risk_summary.

Scoring only: scorecard ``CRM-2023-Q4-v2`` (intercept + five WoE binnings, PD, LGD, EAD, EL,
seven rating bands) is transcribed literally and never re-fit.

Literal Base SAS semantics are the parity target (DEC-015 (a)):
- Latest bureau record: ``b.SCORE_DATE = (select max(SCORE_DATE) ... where SCORE_DATE <=
  score_date)`` keeps every bureau row on the customer's max qualifying date. Spark SQL does
  not allow a correlated subquery in a JOIN ON clause, so the same set is built as a window
  (``MAX(score_date) OVER (PARTITION BY customer_id)`` after the ``<= score_date`` filter).
  Ties on that date would duplicate the account exactly as SAS does (no row_number pick).
- All scorecard constants are DOUBLE literals (``0.412D``) so arithmetic stays IEEE double as
  in SAS; ``exp()`` last-ulp differences are inside ML-2 (abs <= 1e-9). PD is never rounded.
- ``LGD = max(0, min(1, (LTV-0.5)*0.8))`` is evaluated only inside ``not missing(LTV)`` in
  SAS, so ``greatest/least`` never see a NULL; the missing branch is the literal ``0.40``.
- ``RISK_RATING ne NEW_RISK_RATING or RISK_RATING is null`` (AMB-11) — SAS ``. ne x`` is TRUE
  and is covered by the explicit ``IS NULL`` disjunct.
- PROC MEANS ``n=N_ACCOUNTS`` is the non-missing count of the first VAR, ``PD`` (AMB-08);
  CLASS rows with a missing class value are excluded (none occur, filter stated anyway).
- ``%parmv(model_id)`` would upper-case the value (``_CASE=U``); the reference and the
  hand-off fix ``model_id`` as ``CRM-2023-Q4-v2``, which is what is written (see PR note).

Idempotency: ``risk_scores`` / ``risk_migration`` replace the ``score_date = business_date``
slice (Delta ``REPLACE WHERE``); ``risk_summary`` is a PROC MEANS output and is overwritten
wholesale from this run's scored slice.

``risk_scores_woe_debug`` (ML-8 intermediates) is materialised only on ``--woe-debug``.
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
GOLD = "sas_gold"

MODEL_ID = "CRM-2023-Q4-v2"
SCORED_TYPES = ("MTG", "AUTO", "PERS", "CC", "LOC", "HELC")
SECURED_TYPES = ("MTG", "AUTO", "HELC")
REVOLVING_TYPES = ("CC", "LOC", "HELC")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# WORK.SCORE_INPUT carried columns, in SAS order (source alias, column)
_INPUT_COLUMNS: tuple[tuple[str, str, str], ...] = (
    ("a", "account_id", "STRING"),
    ("a", "customer_id", "STRING"),
    ("a", "account_type", "STRING"),
    ("a", "current_balance", "DECIMAL(18,2)"),
    ("a", "credit_limit", "DECIMAL(18,2)"),
    ("a", "acct_age_months", "INT"),
    ("a", "days_inactive", "INT"),
    ("a", "utilization_pct", "DOUBLE"),
    ("a", "customer_segment", "STRING"),
    ("a", "region_code", "STRING"),
    ("b", "fico_score", "INT"),
    ("b", "vantage_score", "INT"),
    ("b", "bureau_inqs_6mo", "INT"),
    ("b", "bureau_trades_open", "INT"),
    ("b", "bureau_derogs", "INT"),
    ("b", "bureau_util_pct", "DOUBLE"),
    ("b", "bureau_oldest_trade_mo", "INT"),
    ("p", "pmt_ontime_12mo", "INT"),
    ("p", "pmt_late_30_12mo", "INT"),
    ("p", "pmt_late_60_12mo", "INT"),
    ("p", "pmt_late_90_12mo", "INT"),
    ("p", "max_days_past_due_ever", "INT"),
    ("p", "months_since_last_dpd", "INT"),
    ("p", "avg_pmt_ratio_12mo", "DOUBLE"),
    ("c", "collateral_value", "DECIMAL(18,2)"),
    ("c", "last_appraisal_date", "DATE"),
)
_SCORE_COLUMNS: tuple[tuple[str, str], ...] = (
    ("ltv", "DOUBLE"),
    ("pd", "DOUBLE"),
    ("lgd", "DOUBLE"),
    ("ead", "DOUBLE"),
    ("expected_loss", "DOUBLE"),
    ("new_risk_rating", "INT"),
    ("score_date", "DATE"),
    ("model_id", "STRING"),
    ("score_timestamp", "TIMESTAMP"),
)
RISK_SCORES_COLUMNS: tuple[tuple[str, str], ...] = tuple(
    (c, t) for _, c, t in _INPUT_COLUMNS
) + _SCORE_COLUMNS
RISK_SCORES_COLUMN_NAMES = tuple(c for c, _ in RISK_SCORES_COLUMNS)

RISK_MIGRATION_COLUMNS: tuple[tuple[str, str], ...] = (
    ("score_date", "DATE"),
    ("account_id", "STRING"),
    ("prev_rating", "INT"),
    ("curr_rating", "INT"),
    ("migration_direction", "STRING"),
    ("pd", "DOUBLE"),
    ("expected_loss", "DOUBLE"),
)
RISK_SUMMARY_COLUMNS: tuple[tuple[str, str], ...] = (
    ("account_type", "STRING"),
    ("new_risk_rating", "INT"),
    ("n_accounts", "BIGINT"),
    ("avg_pd", "DOUBLE"),
    ("avg_lgd", "DOUBLE"),
    ("total_ead", "DOUBLE"),
    ("total_el", "DOUBLE"),
)
WOE_DEBUG_COLUMNS: tuple[tuple[str, str], ...] = (
    ("account_id", "STRING"),
    ("score_date", "DATE"),
    ("intercept", "DOUBLE"),
    ("woe_fico", "DOUBLE"),
    ("woe_util", "DOUBLE"),
    ("woe_dpd", "DOUBLE"),
    ("woe_age", "DOUBLE"),
    ("woe_ltv", "DOUBLE"),
    ("log_odds", "DOUBLE"),
    ("pd", "DOUBLE"),
)

# ---- scorecard CRM-2023-Q4-v2 (Programs/Banking/credit_risk_scoring.sas 96-190), fixed ----
INTERCEPT = "-3.2145D"
WOE_FICO = """CASE
        WHEN fico_score IS NULL THEN 0.198D
        WHEN fico_score >= 760 THEN -1.204D
        WHEN fico_score >= 720 THEN -0.812D
        WHEN fico_score >= 680 THEN -0.356D
        WHEN fico_score >= 640 THEN 0.198D
        WHEN fico_score >= 600 THEN 0.654D
        ELSE 1.102D
      END"""
WOE_UTIL = """CASE
        WHEN utilization_pct IS NULL THEN 0D
        WHEN utilization_pct <= 10 THEN -0.956D
        WHEN utilization_pct <= 30 THEN -0.521D
        WHEN utilization_pct <= 50 THEN -0.102D
        WHEN utilization_pct <= 70 THEN 0.334D
        WHEN utilization_pct <= 90 THEN 0.789D
        ELSE 1.245D
      END"""
WOE_DPD = """CASE
        WHEN pmt_late_90_12mo IS NULL THEN 0D
        WHEN pmt_late_90_12mo = 0 THEN -0.678D
        WHEN pmt_late_90_12mo = 1 THEN 0.445D
        ELSE 1.567D
      END"""
WOE_AGE = """CASE
        WHEN acct_age_months IS NULL THEN 0D
        WHEN acct_age_months >= 120 THEN -0.534D
        WHEN acct_age_months >= 60 THEN -0.289D
        WHEN acct_age_months >= 24 THEN 0.045D
        ELSE 0.456D
      END"""
_WOE_LTV_TEMPLATE = """CASE
        WHEN account_type NOT IN ({secured}) THEN 0D
        WHEN ltv IS NULL THEN 0D
        WHEN ltv <= 0.60D THEN -0.712D
        WHEN ltv <= 0.80D THEN -0.234D
        WHEN ltv <= 1.00D THEN 0.356D
        ELSE 0.889D
      END"""
LOG_ODDS = ("intercept + 0.412D * woe_fico + 0.198D * woe_util + 0.289D * woe_dpd"
            " + 0.067D * woe_age + 0.134D * woe_ltv")
PD = "1D / (1D + EXP(-log_odds))"
_LGD_TEMPLATE = """CASE
        WHEN account_type IN ({secured}) THEN
          CASE WHEN ltv IS NOT NULL THEN GREATEST(0D, LEAST(1D, (ltv - 0.5D) * 0.8D))
               ELSE 0.40D END
        WHEN account_type = 'CC' THEN 0.75D
        ELSE 0.50D
      END"""
_EAD_TEMPLATE = """CASE
        WHEN account_type IN ({revolving})
          THEN CAST(current_balance AS DOUBLE)
               + 0.50D * (CAST(credit_limit AS DOUBLE) - CAST(current_balance AS DOUBLE))
        ELSE CAST(current_balance AS DOUBLE)
      END"""
EXPECTED_LOSS = "pd * lgd * ead"
NEW_RISK_RATING = """CASE
        WHEN pd < 0.005D THEN 1
        WHEN pd < 0.01D THEN 2
        WHEN pd < 0.03D THEN 3
        WHEN pd < 0.07D THEN 4
        WHEN pd < 0.15D THEN 5
        WHEN pd < 0.30D THEN 6
        ELSE 7
      END"""


def _sql_list(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


WOE_LTV = _WOE_LTV_TEMPLATE.format(secured=_sql_list(SECURED_TYPES))
LGD = _LGD_TEMPLATE.format(secured=_sql_list(SECURED_TYPES))
EAD = _EAD_TEMPLATE.format(revolving=_sql_list(REVOLVING_TYPES))


def parse_business_date(value: str) -> date:
    if not _DATE_RE.match(value):
        raise ValueError(f"business_date must be YYYY-MM-DD, got {value!r}")
    return date.fromisoformat(value)


def _table(catalog: str, schema: str, name: str, cols: tuple[tuple[str, str], ...]) -> str:
    body = ",\n  ".join(f"{c} {t}" for c, t in cols)
    return f"CREATE TABLE IF NOT EXISTS {catalog}.{schema}.{name} (\n  {body}\n) USING DELTA"


def ddl(catalog: str = CATALOG) -> list[str]:
    return [
        _table(catalog, SILVER, "risk_scores", RISK_SCORES_COLUMNS),
        _table(catalog, SILVER, "risk_migration", RISK_MIGRATION_COLUMNS),
        _table(catalog, GOLD, "risk_summary", RISK_SUMMARY_COLUMNS),
    ]


def woe_debug_ddl(catalog: str = CATALOG) -> str:
    return _table(catalog, SILVER, "risk_scores_woe_debug", WOE_DEBUG_COLUMNS)


def scored_cte(score_date: date, catalog: str = CATALOG) -> str:
    """WORK.SCORE_INPUT (Step 1) and WORK.SCORED (Step 2) including the WOE intermediates
    that the SAS DROP statement removes on output."""
    d = f"DATE'{score_date.isoformat()}'"
    src_cols = ",\n      ".join(f"{alias}.{c}" for alias, c, _ in _INPUT_COLUMNS)
    return f"""
WITH bureau_latest AS (
  SELECT * FROM (
    SELECT b.*, MAX(b.score_date) OVER (PARTITION BY b.customer_id) AS max_score_date
    FROM {catalog}.{BRONZE}.bureau_scores b
    WHERE b.score_date <= {d}
  ) WHERE score_date = max_score_date
),
score_input AS (
  SELECT
      {src_cols},
      CASE
        WHEN c.collateral_value > 0
          THEN CAST(a.current_balance AS DOUBLE) / CAST(c.collateral_value AS DOUBLE)
        ELSE CAST(NULL AS DOUBLE)
      END AS ltv
  FROM {catalog}.{SILVER}.cust_accounts_daily a
  LEFT JOIN bureau_latest b
    ON a.customer_id = b.customer_id
  LEFT JOIN {catalog}.{BRONZE}.payment_history p
    ON a.account_id = p.account_id
  LEFT JOIN {catalog}.{BRONZE}.collateral c
    ON a.account_id = c.account_id
  WHERE a.snapshot_date = {d}
    AND a.account_type IN ({_sql_list(SCORED_TYPES)})
),
woe AS (
  SELECT
      i.*,
      {INTERCEPT} AS intercept,
      {WOE_FICO} AS woe_fico,
      {WOE_UTIL} AS woe_util,
      {WOE_DPD} AS woe_dpd,
      {WOE_AGE} AS woe_age,
      {WOE_LTV} AS woe_ltv
  FROM score_input i
),
odds AS (
  SELECT w.*, {LOG_ODDS} AS log_odds FROM woe w
),
prob AS (
  SELECT o.*, {PD} AS pd FROM odds o
),
loss AS (
  SELECT
      r.*,
      {LGD} AS lgd,
      {EAD} AS ead
  FROM prob r
),
scored AS (
  SELECT
      l.*,
      {EXPECTED_LOSS} AS expected_loss,
      {NEW_RISK_RATING} AS new_risk_rating,
      {d} AS score_date
  FROM loss l
)"""


def risk_scores_sql(score_date: date, model_id: str = MODEL_ID, catalog: str = CATALOG) -> str:
    """PROC APPEND ... CURATED.RISK_SCORES, replacing the score_date slice."""
    cols = ",\n      ".join(RISK_SCORES_COLUMN_NAMES[:-3])
    return f"""INSERT INTO {catalog}.{SILVER}.risk_scores
REPLACE WHERE score_date = DATE'{score_date.isoformat()}'
{scored_cte(score_date, catalog)}
SELECT
      {cols},
      score_date,
      '{model_id}' AS model_id,
      CURRENT_TIMESTAMP() AS score_timestamp
FROM scored"""


def woe_debug_sql(score_date: date, catalog: str = CATALOG) -> str:
    """ML-8 intermediates (the columns SAS drops at line 196)."""
    cols = ",\n      ".join(c for c, _ in WOE_DEBUG_COLUMNS)
    return f"""INSERT INTO {catalog}.{SILVER}.risk_scores_woe_debug
REPLACE WHERE score_date = DATE'{score_date.isoformat()}'
{scored_cte(score_date, catalog)}
SELECT
      {cols}
FROM scored"""


def risk_migration_sql(score_date: date, catalog: str = CATALOG) -> str:
    """WORK.RISK_MIGRATION (Step 3) from this run's scored slice, appended with replace."""
    d = f"DATE'{score_date.isoformat()}'"
    return f"""INSERT INTO {catalog}.{SILVER}.risk_migration
REPLACE WHERE score_date = {d}
SELECT
      {d} AS score_date,
      a.account_id,
      a.risk_rating AS prev_rating,
      s.new_risk_rating AS curr_rating,
      CASE
        WHEN a.risk_rating IS NULL THEN 'NEW'
        WHEN s.new_risk_rating < a.risk_rating THEN 'UPGRADE'
        WHEN s.new_risk_rating > a.risk_rating THEN 'DOWNGRADE'
        ELSE 'STABLE'
      END AS migration_direction,
      s.pd,
      s.expected_loss
FROM {catalog}.{SILVER}.risk_scores s
INNER JOIN {catalog}.{SILVER}.cust_accounts_daily a
  ON s.account_id = a.account_id
WHERE s.score_date = {d}
  AND a.snapshot_date = {d}
  AND (a.risk_rating <> s.new_risk_rating OR a.risk_rating IS NULL)"""


def risk_summary_sql(score_date: date, catalog: str = CATALOG) -> str:
    """PROC MEANS nway CLASS ACCOUNT_TYPE NEW_RISK_RATING over WORK.SCORED (full overwrite)."""
    d = f"DATE'{score_date.isoformat()}'"
    return f"""INSERT OVERWRITE {catalog}.{GOLD}.risk_summary
SELECT
      account_type,
      new_risk_rating,
      COUNT(pd) AS n_accounts,
      AVG(pd) AS avg_pd,
      AVG(lgd) AS avg_lgd,
      SUM(ead) AS total_ead,
      SUM(expected_loss) AS total_el
FROM {catalog}.{SILVER}.risk_scores
WHERE score_date = {d}
  AND account_type IS NOT NULL
  AND new_risk_rating IS NOT NULL
GROUP BY account_type, new_risk_rating"""


def statements(score_date: date, model_id: str = MODEL_ID, catalog: str = CATALOG,
               woe_debug: bool = False) -> list[str]:
    sqls = ddl(catalog) + [
        risk_scores_sql(score_date, model_id, catalog),
        risk_migration_sql(score_date, catalog),
        risk_summary_sql(score_date, catalog),
    ]
    if woe_debug:
        sqls += [woe_debug_ddl(catalog), woe_debug_sql(score_date, catalog)]
    return sqls


def run(execute: Callable[[str], object], business_date: str, model_id: str = MODEL_ID,
        catalog: str = CATALOG, woe_debug: bool = False) -> list[str]:
    sd = parse_business_date(validate_param("score_date", business_date, required=True))
    # %parmv defaults to _CASE=U; the model identifier is case-preserved to match the
    # reference/hand-off value CRM-2023-Q4-v2 (recorded as a decision in the PR/ledger).
    mid = validate_param("model_id", model_id, required=True, case="N")
    sqls = statements(sd, mid, catalog, woe_debug)
    for s in sqls:
        execute(s)
    return sqls


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--business-date", required=True, help="score_date (YYYY-MM-DD)")
    ap.add_argument("--model-id", default=MODEL_ID)
    ap.add_argument("--woe-debug", action="store_true",
                    help="also materialise sas_silver.risk_scores_woe_debug (ML-8)")
    ap.add_argument("--executor", choices=["spark", "warehouse"], default="spark",
                    help="warehouse: Statement Execution API (ad hoc CLI run, no cluster)")
    ap.add_argument("--warehouse-id", default=os.environ.get("RECON_WAREHOUSE_ID", "565cd2fd713738c4"))
    # bundle passes the shared parameter set; the ones below are not used by U3
    ap.add_argument("--report-month", default=None)
    ap.add_argument("--region", default=None)
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
    n = len(run(execute, a.business_date, a.model_id, woe_debug=a.woe_debug))
    print(f"credit_risk_scoring: {n} statements, score_date={a.business_date} model_id={a.model_id}")
    return 0


if __name__ == "__main__":
    _rc = main()
    if _rc:  # serverless spark_python_task reports any SystemExit (even 0) as a failure
        raise SystemExit(_rc)
