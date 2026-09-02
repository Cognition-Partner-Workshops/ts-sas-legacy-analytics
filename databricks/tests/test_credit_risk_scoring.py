"""U3 credit_risk_scoring conversion (scorecard CRM-2023-Q4-v2, literal SAS semantics)."""

import re
from datetime import date

import pytest

from jobs import credit_risk_scoring as crs
from recon.units import classify_column, tables_for
from sas_macros.parmv import ParamError

SD = date(2024, 1, 31)
REF_HEADER = (
    "account_id,customer_id,account_type,current_balance,credit_limit,acct_age_months,"
    "days_inactive,utilization_pct,customer_segment,region_code,fico_score,vantage_score,"
    "bureau_inqs_6mo,bureau_trades_open,bureau_derogs,bureau_util_pct,bureau_oldest_trade_mo,"
    "pmt_ontime_12mo,pmt_late_30_12mo,pmt_late_60_12mo,pmt_late_90_12mo,max_days_past_due_ever,"
    "months_since_last_dpd,avg_pmt_ratio_12mo,collateral_value,last_appraisal_date,ltv,pd,lgd,"
    "ead,expected_loss,new_risk_rating,score_date,model_id,score_timestamp"
)


def test_target_schemas_match_reference_headers():
    assert ",".join(crs.RISK_SCORES_COLUMN_NAMES) == REF_HEADER
    assert [c for c, _ in crs.RISK_MIGRATION_COLUMNS] == [
        "score_date", "account_id", "prev_rating", "curr_rating", "migration_direction",
        "pd", "expected_loss"]
    assert [c for c, _ in crs.RISK_SUMMARY_COLUMNS] == [
        "account_type", "new_risk_rating", "n_accounts", "avg_pd", "avg_lgd", "total_ead", "total_el"]
    d = crs.ddl()
    assert d[0].startswith("CREATE TABLE IF NOT EXISTS sas_legacy.sas_silver.risk_scores")
    assert d[1].startswith("CREATE TABLE IF NOT EXISTS sas_legacy.sas_silver.risk_migration")
    assert d[2].startswith("CREATE TABLE IF NOT EXISTS sas_legacy.sas_gold.risk_summary")
    assert d[0].count("\n  ") == 35


def test_score_input_joins_and_filters_follow_sas():
    sql = crs.scored_cte(SD)
    assert "FROM sas_legacy.sas_silver.cust_accounts_daily a" in sql
    assert "WHERE b.score_date <= DATE'2024-01-31'" in sql  # correlated max(SCORE_DATE) 76-78
    assert "MAX(b.score_date) OVER (PARTITION BY b.customer_id)" in sql
    assert "ROW_NUMBER" not in sql  # ties duplicate as in SAS, no arbitrary pick
    assert "LEFT JOIN bureau_latest b" in sql
    assert "LEFT JOIN sas_legacy.sas_bronze.payment_history p" in sql
    assert "LEFT JOIN sas_legacy.sas_bronze.collateral c" in sql
    assert "a.snapshot_date = DATE'2024-01-31'" in sql
    assert "a.account_type IN ('MTG', 'AUTO', 'PERS', 'CC', 'LOC', 'HELC')" in sql
    assert "WHEN c.collateral_value > 0" in sql and "ELSE CAST(NULL AS DOUBLE)" in sql


def test_scorecard_constants_are_fixed_double_literals():
    sql = crs.scored_cte(SD)
    assert "-3.2145D AS intercept" in sql
    for woe in ("-1.204D", "-0.812D", "-0.356D", "0.198D", "0.654D", "1.102D",   # FICO
                "-0.956D", "-0.521D", "-0.102D", "0.334D", "0.789D", "1.245D",   # UTIL
                "-0.678D", "0.445D", "1.567D",                                    # DPD
                "-0.534D", "-0.289D", "0.045D", "0.456D",                         # AGE
                "-0.712D", "-0.234D", "0.356D", "0.889D"):                        # LTV
        assert woe in sql, woe
    assert ("intercept + 0.412D * woe_fico + 0.198D * woe_util + 0.289D * woe_dpd"
            " + 0.067D * woe_age + 0.134D * woe_ltv AS log_odds") in sql
    assert "1D / (1D + EXP(-log_odds)) AS pd" in sql
    assert "ROUND(" not in sql.upper()
    # no non-suffixed decimal literal may leak into DECIMAL arithmetic
    assert not re.search(r"(?<![\w.])-?\d+\.\d+(?![\dD])", sql.replace("DATE'2024-01-31'", ""))


def test_woe_bins_keep_missing_branches_and_edge_inclusivity():
    assert "WHEN fico_score IS NULL THEN 0.198D" in crs.WOE_FICO  # population average
    assert "WHEN utilization_pct IS NULL THEN 0D" in crs.WOE_UTIL
    assert "WHEN pmt_late_90_12mo IS NULL THEN 0D" in crs.WOE_DPD
    assert "WHEN acct_age_months IS NULL THEN 0D" in crs.WOE_AGE
    assert crs.WOE_LTV.index("NOT IN ('MTG', 'AUTO', 'HELC')") < crs.WOE_LTV.index("ltv IS NULL")
    assert "fico_score >= 760" in crs.WOE_FICO and "utilization_pct <= 90" in crs.WOE_UTIL
    assert "ltv <= 0.60D" in crs.WOE_LTV and "acct_age_months >= 24" in crs.WOE_AGE


def test_lgd_ead_el_rating_follow_sas_branches():
    assert ("CASE WHEN ltv IS NOT NULL THEN GREATEST(0D, LEAST(1D, (ltv - 0.5D) * 0.8D))\n"
            "               ELSE 0.40D END") in crs.LGD  # greatest/least never see NULL
    assert "WHEN account_type = 'CC' THEN 0.75D" in crs.LGD and "ELSE 0.50D" in crs.LGD
    assert "WHEN account_type IN ('CC', 'LOC', 'HELC')" in crs.EAD
    assert "0.50D * (CAST(credit_limit AS DOUBLE) - CAST(current_balance AS DOUBLE))" in crs.EAD
    assert crs.EXPECTED_LOSS == "pd * lgd * ead"
    bands = re.findall(r"WHEN pd < ([\d.]+)D THEN (\d)", crs.NEW_RISK_RATING)
    assert bands == [("0.005", "1"), ("0.01", "2"), ("0.03", "3"), ("0.07", "4"),
                     ("0.15", "5"), ("0.30", "6")]
    assert crs.NEW_RISK_RATING.rstrip().endswith("ELSE 7\n      END")


def test_risk_scores_replaces_slice_and_stamps_model_and_runtime():
    sql = crs.risk_scores_sql(SD)
    assert sql.startswith("INSERT INTO sas_legacy.sas_silver.risk_scores\n"
                          "REPLACE WHERE score_date = DATE'2024-01-31'")
    assert "'CRM-2023-Q4-v2' AS model_id" in sql
    assert "CURRENT_TIMESTAMP() AS score_timestamp" in sql
    assert "intercept" not in sql.split("FROM scored")[0].rsplit("SELECT", 1)[1]  # DROP 196


def test_risk_migration_uses_u1_risk_rating_and_amb_11_filter():
    sql = crs.risk_migration_sql(SD)
    assert sql.startswith("INSERT INTO sas_legacy.sas_silver.risk_migration\nREPLACE WHERE")
    assert "a.risk_rating AS prev_rating" in sql  # D9-002
    assert "INNER JOIN sas_legacy.sas_silver.cust_accounts_daily a" in sql
    assert "(a.risk_rating <> s.new_risk_rating OR a.risk_rating IS NULL)" in sql
    assert "WHEN a.risk_rating IS NULL THEN 'NEW'" in sql
    assert "WHEN s.new_risk_rating < a.risk_rating THEN 'UPGRADE'" in sql
    assert "WHEN s.new_risk_rating > a.risk_rating THEN 'DOWNGRADE'" in sql


def test_risk_summary_is_proc_means_full_overwrite():
    sql = crs.risk_summary_sql(SD)
    assert sql.startswith("INSERT OVERWRITE sas_legacy.sas_gold.risk_summary")
    assert "COUNT(pd) AS n_accounts" in sql  # AMB-08: N of first VAR, not _FREQ_
    assert "AVG(pd) AS avg_pd" in sql and "AVG(lgd) AS avg_lgd" in sql
    assert "SUM(ead) AS total_ead" in sql and "SUM(expected_loss) AS total_el" in sql
    assert "GROUP BY account_type, new_risk_rating" in sql


def test_run_executes_statements_in_order_and_debug_only_on_request():
    seen = []
    sqls = crs.run(seen.append, "2024-01-31")
    assert seen == sqls and len(sqls) == 6
    assert sqls == crs.statements(SD, "CRM-2023-Q4-V2")  # model_id is the only run() normalisation
    assert [s.split()[0] for s in sqls] == ["CREATE"] * 3 + ["INSERT"] * 3
    assert not any("risk_scores_woe_debug" in s for s in sqls)
    dbg = crs.run(lambda s: None, "2024-01-31", woe_debug=True)
    assert len(dbg) == 8 and "risk_scores_woe_debug" in dbg[-1]
    assert "log_odds" in dbg[-1] and "REPLACE WHERE score_date" in dbg[-1]


def test_model_id_is_upper_cased_like_parmv_and_params_validated():
    # DEC-017 (a): %parmv(model_id, _req=1) inherits _CASE=U, so legacy writes 'CRM-2023-Q4-V2'
    sqls = crs.run(lambda s: None, "2024-01-31")
    assert "'CRM-2023-Q4-V2' AS model_id" in sqls[3]
    assert "CRM-2023-Q4-v2" not in sqls[3]
    sqls = crs.run(lambda s: None, "2024-01-31", model_id="crm-2099-q1-v9")
    assert "'CRM-2099-Q1-V9' AS model_id" in sqls[3]
    with pytest.raises(ValueError):
        crs.run(lambda s: None, "31JAN2024")
    with pytest.raises(ParamError):
        crs.run(lambda s: None, "")
    with pytest.raises(ParamError):
        crs.run(lambda s: None, "2024-01-31", model_id="")


def test_catalog_override_and_main_arg_parsing():
    sql = crs.risk_scores_sql(SD, catalog="c_dev")
    assert "INSERT INTO c_dev.sas_silver.risk_scores" in sql
    assert "FROM c_dev.sas_silver.cust_accounts_daily a" in sql
    ns = crs._parse_args(["--business-date", "2024-01-31", "--region", "ALL",
                          "--report-month", "202401", "--abort-on-err", "Y"])
    assert ns.business_date == "2024-01-31" and ns.model_id == "CRM-2023-Q4-v2"
    assert ns.executor == "spark" and ns.woe_debug is False


def test_u3_recon_column_classes_are_pre_stated():
    specs = {s.name: s for s in tables_for("U3")}
    scores = specs["risk_scores"]
    assert scores.keys == ("account_id", "score_date")
    for col in ("fico_score", "vantage_score", "bureau_inqs_6mo", "bureau_trades_open",
                "bureau_derogs", "bureau_oldest_trade_mo", "pmt_ontime_12mo",
                "pmt_late_90_12mo", "max_days_past_due_ever", "months_since_last_dpd",
                "collateral_value", "last_appraisal_date", "model_id"):
        assert classify_column(scores, col) == "T-3", col
    for col in ("bureau_util_pct", "avg_pmt_ratio_12mo", "utilization_pct", "ltv"):
        assert classify_column(scores, col) == "T-5", col
    assert classify_column(scores, "new_risk_rating") == "ML-1"
    assert classify_column(scores, "pd") == "ML-2"
    assert classify_column(scores, "lgd") == "ML-3" and classify_column(scores, "ead") == "ML-3"
    assert classify_column(scores, "expected_loss") == "ML-4"
    assert classify_column(scores, "score_timestamp") == "T-7"
    mig = specs["risk_migration"]
    assert classify_column(mig, "pd") == "ML-2"
    assert classify_column(mig, "expected_loss") == "ML-4"
    assert classify_column(mig, "migration_direction") == "ML-6"
    assert specs["risk_summary"].keys == ("account_type", "new_risk_rating")
    assert classify_column(specs["risk_summary"], "n_accounts") == "T-3"
