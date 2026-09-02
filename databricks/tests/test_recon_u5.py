import json
from datetime import date
from pathlib import Path

from recon import rules, run_recon
from recon.units import tables_for


FIXTURES = Path(__file__).parent / "fixtures"


def _results(report: dict) -> dict[tuple[str, str | None], dict]:
    return {
        (result["rule"], result["column"]): result
        for table in report["tables"]
        for result in table["results"]
    }


def test_u5_fixture_recon_passes_latest_batch_and_patterns(tmp_path: Path) -> None:
    assert run_recon.main(
        [
            "--unit", "U5", "--mode", "fixture", "--business-date", "2024-01-31",
            "--out", str(tmp_path), "--reference-dir", str(FIXTURES / "reference"),
            "--target-dir", str(FIXTURES / "target"),
        ]
    ) == 0
    report = json.loads((tmp_path / "recon.json").read_text(encoding="utf-8"))
    results = _results(report)
    assert results[("T-1", None)]["reference"] == 4
    assert results[("T-1", None)]["target"] == 4
    assert results[("T-2", "batch_id,step_num")]["verdict"] == "PASS"
    assert results[("T-3", "batch_id")]["verdict"] == "PASS"
    for column in ("program_path", "error_msg", "status", "step_name"):
        assert results[("T-3", column)]["verdict"] == "PASS"
    for column in ("start_time", "end_time", "duration"):
        assert results[("T-7", column)]["verdict"] == "PASS"
    assert results[("T-8", "step_num")]["verdict"] == "PASS"
    assert ("T-8", "batch_id") not in results
    assert results[("T-8", "step_num")]["target"] == "4"


def test_u5_target_bad_fails_pattern_and_status(tmp_path: Path) -> None:
    assert run_recon.main(
        [
            "--unit", "U5", "--mode", "fixture", "--business-date", "2024-01-31",
            "--out", str(tmp_path), "--reference-dir", str(FIXTURES / "reference"),
            "--target-dir", str(FIXTURES / "target_bad"),
        ]
    ) == 1
    report = json.loads((tmp_path / "recon.json").read_text(encoding="utf-8"))
    results = _results(report)
    assert results[("T-3", "batch_id")]["verdict"] == "FAIL"
    assert results[("T-3", "status")]["verdict"] == "FAIL"


def test_resolve_spec_substitutes_business_date() -> None:
    spec = tables_for("U5")[0]
    resolved = run_recon.resolve_spec(spec, date(2024, 1, 31))
    assert resolved.latest_prefix == "BANK_20240131_"
    assert resolved.column_rules["batch_id"] == r"T-3:pattern=^BANK_20240131_\d{8}T\d{6}$"


def test_aggregate_sql_where_is_one_statement() -> None:
    sql = rules.aggregate_sql("sas_legacy.sas_silver.t", ["duration"], ("step_num",), "x = 1")
    assert sql.startswith("SELECT ")
    assert " FROM sas_legacy.sas_silver.t WHERE x = 1" in sql
