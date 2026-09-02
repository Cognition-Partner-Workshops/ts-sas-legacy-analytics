from datetime import date, datetime, timezone

from jobs import run_daily_banking as rdb


def _task(key: str, result: str, start: int, end: int, attempt: int = 0, message: str = "") -> dict:
    return {
        "task_key": key,
        "start_time": start,
        "end_time": end,
        "attempt_number": attempt,
        "state": {"result_state": result, "state_message": message},
    }


def _run(tasks: list[dict]) -> dict:
    return {"start_time": 1788308100000, "tasks": tasks}


def test_batch_id_format() -> None:
    start = int(datetime(2026, 9, 2, 0, 15, tzinfo=timezone.utc).timestamp() * 1000)
    assert rdb.batch_id(date(2024, 1, 31), start) == "BANK_20240131_20260902T001500"


def test_control_rows_success_tasks_are_in_step_order() -> None:
    tasks = [
        _task(key, "SUCCESS", 1000 + i * 1000, 2000 + i * 1000)
        for i, (_num, key, _name, _path) in enumerate(rdb.STEPS)
    ]
    tasks.append(_task("batch_summary", "SUCCESS", 1000, 2000))
    rows = rdb.control_rows(_run(tasks), date(2024, 1, 31))
    assert [row["step_num"] for row in rows] == [1, 2, 3, 4]
    assert all(row["status"] == "PASS" and row["error_msg"] == "" for row in rows)
    assert rows[0]["duration"] == 1.0


def test_control_rows_failures_retries_upstream_and_truncation() -> None:
    long_message = "x" * 600
    tasks = [
        _task("load_customer_accounts", "SUCCESS", 1000, 2000),
        _task("daily_transaction_processing", "SUCCESS", 2000, 3000),
        _task("credit_risk_scoring", "FAILED", 3000, 5000, message=long_message),
        _task("monthly_regulatory_reporting", "UPSTREAM_FAILED", 5000, 6000),
    ]
    rows = rdb.control_rows(_run(tasks), date(2024, 1, 31))
    assert len(rows) == 3
    assert rows[2]["status"] == "FAIL"
    assert rows[2]["error_msg"].startswith("SYSCC=FAILED")
    assert len(rows[2]["error_msg"]) == 500

    retry_tasks = [
        _task("load_customer_accounts", "FAILED", 1000, 2000),
        _task("load_customer_accounts", "SUCCESS", 2000, 3000, attempt=1),
    ]
    assert rdb.control_rows(_run(retry_tasks), date(2024, 1, 31))[0]["status"] == "PASS"


def test_insert_sql_escapes_quotes_and_has_one_insert() -> None:
    rows = rdb.control_rows(
        _run([_task(key, "SUCCESS", 1000, 2000) for _num, key, _name, _path in rdb.STEPS]),
        date(2024, 1, 31),
    )
    rows[0]["step_name"] = "Load 'Customer' Accounts"
    sql = rdb.insert_sql(rows)
    assert sql.count("INSERT INTO") == 1
    assert sql.count("), (") == 3
    assert "Load ''Customer'' Accounts" in sql


def test_ddl_has_all_columns_in_order() -> None:
    sql = rdb.ddl()
    expected = (
        "batch_id STRING", "step_num INT", "step_name STRING", "program_path STRING",
        "status STRING", "start_time TIMESTAMP", "end_time TIMESTAMP", "duration DOUBLE",
        "error_msg STRING",
    )
    assert all(sql.index(column) < sql.index(expected[i + 1]) for i, column in enumerate(expected[:-1]))


def test_run_executes_ddl_and_insert_and_returns_counts() -> None:
    executed = []
    fetched = _run([_task(key, "SUCCESS", 1000, 2000) for _num, key, _name, _path in rdb.STEPS])
    result = rdb.run(executed.append, lambda _run_id: fetched, 42, "2024-01-31")
    assert executed[0] == rdb.ddl()
    assert executed[1].startswith("INSERT INTO")
    assert result["rows_written"] == 4
    assert result["pass"] == 4 and result["fail"] == 0


def test_run_with_all_upstream_skipped_writes_only_ddl() -> None:
    executed = []
    fetched = _run([
        _task(key, "UPSTREAM_CANCELED", 1000, 2000)
        for _num, key, _name, _path in rdb.STEPS
    ])
    result = rdb.run(executed.append, lambda _run_id: fetched, 42, "2024-01-31")
    assert executed == [rdb.ddl()]
    assert result["rows_written"] == 0
