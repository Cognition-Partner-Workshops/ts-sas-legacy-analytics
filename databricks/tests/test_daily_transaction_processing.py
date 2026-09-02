"""U2 daily transaction processing conversion and recon spec."""

from datetime import date

import pytest

from jobs import daily_transaction_processing as dtp
from recon.units import TXN_FEED_COLUMNS, classify_column, tables_for

BD = date(2024, 1, 31)


def test_feed_table_name_follows_yymmddn8():
    assert dtp.feed_table(BD) == "sas_legacy.sas_bronze.txn_feed_20240131"
    assert "table_name = 'txn_feed_20240131'" in dtp.feed_exists_sql(BD)


def test_target_schemas_follow_base_schema():
    schemas = dtp.ddl()
    assert len(schemas) == 4
    assert all(s.startswith("CREATE TABLE IF NOT EXISTS sas_legacy.sas_silver.") for s in schemas)
    daily, running, anomalies, rejected = schemas
    assert daily.count("\n  ") == 10 and "running_balance" not in daily and "reject_reason" not in daily
    assert rejected.count("\n  ") == 10 and "running_balance" not in rejected and "reject_reason" not in rejected
    assert anomalies.count("\n  ") == 23 and anomalies.rstrip().endswith("anomaly_type STRING\n) USING DELTA")
    assert running.count("\n  ") == 4


def test_reject_predicate_uses_sas_missing_semantics():
    assert "transaction_type IS NULL OR transaction_type NOT IN (" in dtp.REJECT_PREDICATE
    assert "ABS(transaction_amount) > 10000000" in dtp.REJECT_PREDICATE
    assert "transaction_amount IS NULL" in dtp.REJECT_PREDICATE
    sql = dtp.rejected_sql(BD)
    assert "transaction_date > DATE'2024-01-31'" in sql
    assert sql.startswith("INSERT OVERWRITE sas_legacy.sas_silver.txn_rejected")
    assert "reject_reason" not in sql.lower()


def test_running_balance_is_window_sum_seeded_from_snapshot():
    sql = dtp.base_cte(BD)
    assert "SUM(e.signed_amount) OVER (PARTITION BY e.account_id ORDER BY e.transaction_date, e.transaction_id ROWS UNBOUNDED PRECEDING)" in sql.replace("\n", " ")
    assert "e.pre_txn_balance +" in sql
    assert "a.snapshot_date = DATE'2024-01-31'" in sql
    assert "LEFT JOIN sas_legacy.sas_silver.cust_accounts_daily a" in sql
    assert dtp.running_balances_sql(BD).startswith(
        "INSERT INTO sas_legacy.sas_silver.running_balances\n"
        "REPLACE WHERE transaction_date = DATE'2024-01-31'"
    )


def test_anomaly_stats_are_pre_append_sample_std():
    sql = dtp.anomalies_sql(BD)
    assert "STDDEV_SAMP(" in sql
    assert "DATE_SUB(DATE'2024-01-31', 90)" in sql
    assert "NOT EXISTS (SELECT 1 FROM validated" in sql
    assert "WHEN s.std_txn_amt > 0" in sql
    assert "ELSE CAST(NULL AS DOUBLE)" in sql
    assert "FROM sas_legacy.sas_silver.daily_transactions h" in sql


def test_anomaly_classification_order_and_missing_low():
    sql = dtp.anomalies_sql(BD)
    assert sql.index("HIGH_AMOUNT") < sql.index("OVERDRAFT") < sql.index("LARGE_WITHDRAWAL") < sql.index("ORPHAN_ACCOUNT")
    assert "e.running_balance IS NULL OR e.running_balance < 0" in sql
    assert "e.pre_txn_balance IS NULL OR ABS(e.transaction_amount) > e.pre_txn_balance * 0.9" in sql
    assert "WHERE anomaly_type <> ''" in sql


def test_append_is_merge_on_transaction_id_with_base_schema():
    sql = dtp.append_sql(BD)
    assert sql.startswith("MERGE INTO sas_legacy.sas_silver.daily_transactions b")
    assert "ON b.transaction_id = s.transaction_id" in sql
    assert "WHEN NOT MATCHED THEN INSERT" in sql
    assert "WHEN MATCHED" not in sql
    assert "running_balance" not in sql.split("WHEN NOT MATCHED", 1)[1]
    assert "pre_txn_balance" not in sql.split("WHEN NOT MATCHED", 1)[1]


def test_run_aborts_when_feed_missing():
    executed = []

    def fake(sql):
        executed.append(sql)
        return [{"n": "0"}]

    with pytest.raises(dtp.FeedMissingError):
        dtp.run(fake, "2024-01-31")
    assert len(executed) == 1


def test_run_seeds_history_only_when_silver_empty():
    executed = []

    def empty_silver(sql):
        executed.append(sql)
        if "information_schema" in sql:
            return [{"n": "1"}]
        return [{"n": "0"}]

    out = dtp.run(empty_silver, "2024-01-31")
    assert len(out) == 9
    assert any("daily_transactions_hist" in sql for sql in out)
    running = next(sql for sql in executed if sql.startswith("INSERT INTO sas_legacy.sas_silver.running_balances"))
    anomalies = next(sql for sql in executed if sql.startswith("INSERT INTO sas_legacy.sas_silver.txn_anomalies"))
    merged = next(sql for sql in executed if sql.startswith("MERGE INTO"))
    rejected = next(sql for sql in executed if sql.startswith("INSERT OVERWRITE sas_legacy.sas_silver.txn_rejected"))
    assert executed.index(running) < executed.index(anomalies) < executed.index(merged) < executed.index(rejected)

    executed = []

    def populated_silver(sql):
        executed.append(sql)
        if "information_schema" in sql:
            return [{"n": "1"}]
        return [{"n": "18903"}]

    out = dtp.run(populated_silver, "2024-01-31")
    assert len(out) == 8 and not any("daily_transactions_hist" in sql for sql in out)
    with pytest.raises(ValueError):
        dtp.run(populated_silver, "31JAN2024")


def test_u2_spec_matches_literal_schemas():
    dt, rb, an, rj = tables_for("U2")
    assert classify_column(dt, "transaction_amount") == "T-4"
    assert "running_balance" not in dt.column_rules
    assert (
        rj.multiset
        and rj.keys == TXN_FEED_COLUMNS
        and rj.t9_group is None
        and rj.distinct_keys == ("account_id",)
        and "AMB-02" in rj.t9_unexercised
    )
    assert classify_column(rj, "transaction_amount") == "T-4"
    assert classify_column(rj, "merchant_category") == "T-3"
    assert classify_column(an, "z_score") == "T-6"
    assert classify_column(an, "anomaly_type") == "T-3"
    assert classify_column(an, "pre_txn_balance") == "T-4"
    assert classify_column(rb, "running_balance") == "T-4"
