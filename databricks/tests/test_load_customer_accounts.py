"""U1 load_customer_accounts conversion (DEC-015 (a) literal semantics) and its recon spec."""

from datetime import date

import pytest

from jobs import load_customer_accounts as lca
from recon import rules
from recon.rules import RuleResult, multiset_key, t9_declared_unexercised
from recon.units import classify_column, tables_for
from sas_macros.parmv import ParamError

BD = date(2024, 1, 31)


def test_target_schema_is_29_columns_on_both_outputs():
    names = [c for c, _ in lca.COLUMNS]
    assert len(names) == 29
    assert names[-2:] == ["snapshot_date", "load_timestamp"]
    assert "exception_code" not in names and "exception_desc" not in names  # AMB-01 drop
    for stmt in lca.ddl():
        assert stmt.startswith("CREATE TABLE IF NOT EXISTS sas_legacy.sas_silver.")
        assert stmt.count("\n  ") == 29


def test_base_filters_follow_sas_where_clause():
    sql = lca.base_cte(BD, "ALL")
    assert "INNER JOIN sas_legacy.sas_bronze.cust_demographics d" in sql
    assert "NOT IN ('W', 'C')" in sql
    assert "a.open_date <= DATE'2024-01-31'" in sql
    assert "region_code" not in sql.split("WHERE", 1)[1]  # region=ALL adds no filter
    assert "AND d.region_code = 'NE'" in lca.base_cte(BD, "NE")


def test_derived_columns_preserve_intck_and_missing_semantics():
    sql = lca.base_cte(BD, "ALL")
    # intck('month') = calendar-boundary month difference, not elapsed months
    assert "(YEAR(DATE'2024-01-31') * 12 + MONTH(DATE'2024-01-31')) - (YEAR(open_date) * 12" in sql
    assert "DATEDIFF(DATE'2024-01-31', last_activity_date)" in sql
    assert "ELSE CAST(NULL AS DOUBLE)" in sql  # UTILIZATION_PCT = . outside CC/LOC/HELC
    assert "> 365 AND account_status = 'A' THEN 'Y'" in sql
    assert "current_balance >= 250000 THEN 'Y'" in sql


def test_exceptions_are_multi_output_before_timestamp_assignment():
    sql = lca.exceptions_sql(BD, "ALL")
    assert sql.startswith("INSERT OVERWRITE sas_legacy.sas_silver.acct_exceptions")
    assert sql.count("UNION ALL") == 2  # NEG_BAL, HIGH_UTIL, NO_RISK -> one row per rule
    assert sql.count("CAST(NULL AS DATE) AS snapshot_date") == 3  # AMB-05: OUTPUT before assignment
    assert "current_balance IS NULL OR current_balance < 0" in sql  # SAS `. < 0` is TRUE
    assert "WHERE utilization_pct > 95" in sql
    assert "WHERE risk_rating IS NULL" in sql


def test_snapshot_is_idempotent_per_business_date():
    sql = lca.snapshot_sql(BD, "ALL")
    assert "INSERT INTO sas_legacy.sas_silver.cust_accounts_daily\nREPLACE WHERE snapshot_date = DATE'2024-01-31'" in sql
    assert "DATE'2024-01-31' AS snapshot_date" in sql and "CURRENT_TIMESTAMP() AS load_timestamp" in sql


def test_run_aborts_on_empty_extract_like_nobs():
    executed = []

    def fake(sql):
        executed.append(sql)
        return [{"n": "0"}]

    assert lca.run(fake, "2024-01-31") == []
    assert len(executed) == 1 and "COUNT(*)" in executed[0]


def test_run_executes_ddl_then_two_loads_and_validates_params():
    executed = []

    def fake(sql):
        executed.append(sql)
        return [(487,)]

    out = lca.run(fake, "2024-01-31", "SE")
    assert len(out) == 4 and len(executed) == 5
    assert all("region_code = 'SE'" in s for s in out[2:])
    with pytest.raises(ValueError):
        lca.run(fake, "31JAN2024")
    with pytest.raises(ParamError):
        lca.run(fake, "2024-01-31", "XX")


def test_u1_acct_exceptions_spec_is_full_row_multiset():
    snap, exc = tables_for("U1")
    assert snap.keys == ("account_id", "snapshot_date") and not snap.multiset
    assert exc.multiset and len(exc.keys) == 29 and exc.t9_group is None
    assert exc.distinct_keys == ("account_id",)
    assert "DEC-015" in exc.t9_unexercised
    # a multiset key is the whole row: §3 column rules still govern, not key-exactness
    assert classify_column(exc, "interest_rate") == "T-5"
    assert classify_column(exc, "utilization_pct") == "T-5"
    assert classify_column(exc, "current_balance") == "T-4"
    assert classify_column(exc, "load_timestamp") == "T-3"  # AMB-05: literally null, not run-time
    assert classify_column(exc, "snapshot_date") == "T-3"
    assert classify_column(snap, "load_timestamp") == "T-7"
    assert classify_column(snap, "account_id") == "T-3"


def test_t9_declared_unexercised_verdict_label():
    exc = tables_for("U1")[1]
    r = t9_declared_unexercised(exc)
    assert isinstance(r, RuleResult) and r.rule == "T-9" and r.verdict == "DECLARED-UNEXERCISED"
    assert "DEC-015" in r.detail


def test_multiset_preserves_duplicates_and_quantises_tolerance_columns():
    exc = tables_for("U1")[1]
    cols = list(exc.keys)
    base = {c: None for c in cols}
    row = dict(base, account_id="A1", interest_rate="0.1252", utilization_pct="96.123456789")
    dup = dict(row)
    tgt = dict(row, current_balance="-10.001", utilization_pct="96.1234567")
    row["current_balance"] = dup["current_balance"] = "-10.00"
    assert multiset_key(exc, row) == multiset_key(exc, tgt)
    res = rules._multiset_rows(exc, [row, dup], [tgt, dict(tgt)], cols)
    t2 = next(r for r in res if r.rule == "T-2")
    assert t2.verdict == "PASS"
    res = rules._multiset_rows(exc, [row, dup], [tgt], cols)
    assert next(r for r in res if r.rule == "T-2").verdict == "FAIL"
