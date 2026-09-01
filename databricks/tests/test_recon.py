import json
from pathlib import Path

import pytest

from recon import rules
from recon.run_recon import main
from recon.units import UNITS, TableSpec, classify_column, tables_for

FIX = Path(__file__).parent / "fixtures"


def _run(tmp_path, target="target", **extra):
    argv = [
        "--unit", "U3", "--mode", "fixture", "--business-date", "2024-01-31",
        "--out", str(tmp_path), "--reference-dir", str(FIX / "reference"),
        "--target-dir", str(FIX / target),
    ]
    for k, v in extra.items():
        argv += [f"--{k.replace('_', '-')}", str(v)]
    rc = main(argv)
    return rc, json.loads((tmp_path / "recon.json").read_text())


def test_units_cover_u1_to_u5_with_keys():
    assert list(UNITS) == ["U1", "U2", "U3", "U4", "U5"]
    for u in UNITS:
        for spec in tables_for(u):
            assert spec.keys, spec.name
    assert tables_for("U5")[0].keys == ("batch_id", "step_num")


def test_reference_missing_is_clear(tmp_path, capsys):
    rc = main([
        "--unit", "U1", "--mode", "fixture", "--business-date", "2024-01-31",
        "--out", str(tmp_path), "--reference-dir", str(tmp_path / "nope"),
    ])
    assert rc == 2
    assert "reference missing" in capsys.readouterr().err


def test_fixture_pass_path(tmp_path):
    rc, rep = _run(tmp_path)
    assert rc == 0 and rep["overall"] == "PASS"
    assert rep["mode"] == "DEGRADED"
    assert rep["caveat"] == "reference-derived, not SAS-produced"
    assert len(rep["reference_manifest_sha256"]) == 64
    scores = next(t for t in rep["tables"] if t["table"] == "risk_scores")
    by_rule = {(r["rule"], r["column"]): r["verdict"] for r in scores["results"]}
    assert by_rule[("T-1", None)] == "PASS"
    assert by_rule[("ML-3", "ead")] == "PASS"  # 2500.50 vs 2500.504 within 0.005
    assert by_rule[("ML-4", "expected_loss")] == "PASS"  # 22.50 vs 22.504 within 0.01
    assert by_rule[("T-7", "score_timestamp")] == "PASS"  # excluded, non-null asserted
    assert by_rule[("ML-5", "pd")] == "PASS"
    assert by_rule[("ML-8", "woe_*")] == "NOT_APPLICABLE"
    summary = (tmp_path / "recon.summary.md").read_text().splitlines()
    assert len(summary) <= 30 and "DEGRADED" in summary[1]


def test_fixture_fail_path_reports_rules(tmp_path):
    rc, rep = _run(tmp_path, target="target_bad")
    assert rc == 1 and rep["overall"] == "FAIL"
    scores = next(t for t in rep["tables"] if t["table"] == "risk_scores")
    by_rule = {(r["rule"], r["column"]): r for r in scores["results"]}
    assert by_rule[("T-2", "account_id,score_date")]["verdict"] == "FAIL"  # A003 vs A004
    assert by_rule[("ML-1", "new_risk_rating")]["verdict"] == "FAIL"  # BBB -> BB
    assert by_rule[("ML-2", "pd")]["verdict"] == "FAIL"  # 0.02 -> 0.03
    assert by_rule[("ML-8", "woe_*")]["verdict"] == "FAIL"  # debug table missing on both sides
    assert by_rule[("ML-8", "woe_*")]["detail"].startswith("ML row failed")


def test_classify_column_defaults():
    spec = TableSpec("x", "sas_silver", ("account_id",))
    assert classify_column(spec, "current_balance") == "T-4"
    assert classify_column(spec, "load_timestamp") == "T-7"
    assert classify_column(spec, "account_id") == "T-3"


def test_value_comparators():
    assert rules._compare_value("T-4", "bal", "10.00", "10.004")
    assert not rules._compare_value("T-4", "bal", "10.00", "10.006")
    assert rules._compare_value("T-3", "d", "31JAN2024", "2024-01-31")
    assert rules._compare_value("T-3", "s", "AB  ", "AB")
    assert rules._compare_value("T-3", "n", "1.50", "1.5")
    assert rules._compare_value("T-3", "n", None, "")
    assert not rules._compare_value("T-3", "n", None, "0")


def test_spearman_ties_and_edges():
    assert rules.spearman([1, 2, 2, 3], [1, 2, 2, 3]) == pytest.approx(1.0)
    assert rules.spearman([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0)
    spec = tables_for("U3")[0]
    r = rules.ml7(spec, [{"account_id": "A", "score_date": "2024-01-31", "pd": "0.0300000000001"}])
    assert r.verdict == "INFO" and r.target == 1


def test_aggregate_sql_single_statement():
    sql = rules.aggregate_sql("sas_legacy.sas_silver.t", ["ead", "pd"], ("account_id",))
    assert sql.count("SELECT") == 1 and "COUNT(DISTINCT `account_id`)" in sql and "SUM(`ead`)" in sql
