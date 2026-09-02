"""U5 — conversion of BatchJobs/run_daily_banking.sas (batch control table -> ARCHIVE.BATCH_HISTORY).

Steps 1-4 are the Workflow tasks with depends_on (D5-001).
The batch_summary task, run_if ALL_DONE, reads the current run via the Jobs API.
It appends one row per step task to sas_legacy.sas_silver.archive_batch_history
(PROC APPEND base=ARCHIVE.BATCH_HISTORY force); append-per-run is by design.
restart_from = Jobs repair run; %sendmail D4-003 DEFERRED (no email configured).
ABORT_ON_ERR=Y = dependency chain; ABORT_ON_ERR=N not exercised.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable, Mapping
from datetime import date, datetime, timezone


def _src_root() -> str:
    candidates = [globals().get("__file__"), sys.argv[0] if sys.argv else None, os.getcwd()]
    for candidate in candidates:
        if not candidate:
            continue
        path = os.path.abspath(candidate)
        if os.path.isfile(path):
            path = os.path.dirname(path)
        for _ in range(3):
            if os.path.isdir(os.path.join(path, "sas_macros")):
                return path
            path = os.path.dirname(path)
    return os.path.join(os.getcwd(), "..")


_SRC = _src_root()
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from sas_macros.parmv import validate_param

try:
    from databricks.sdk import WorkspaceClient
except ImportError:  # pragma: no cover - only absent from local test environments
    WorkspaceClient = None


CATALOG = os.environ.get("SAS_LEGACY_CATALOG", "sas_legacy")
TARGET = f"{CATALOG}.sas_silver.archive_batch_history"
STEPS: tuple[tuple[int, str, str, str], ...] = (
    (1, "load_customer_accounts", "Load Customer Accounts", "/opt/sas/custom/programs/Banking/load_customer_accounts.sas"),
    (2, "daily_transaction_processing", "Daily Transaction Processing", "/opt/sas/custom/programs/Banking/daily_transaction_processing.sas"),
    (3, "credit_risk_scoring", "Credit Risk Scoring", "/opt/sas/custom/programs/Banking/credit_risk_scoring.sas"),
    (4, "monthly_regulatory_reporting", "Monthly Regulatory Reporting", "/opt/sas/custom/programs/Banking/monthly_regulatory_reporting.sas"),
)
ERROR_MSG_MAX = 500


def ddl() -> str:
    return (
        f"CREATE TABLE IF NOT EXISTS {TARGET} "
        "(batch_id STRING, step_num INT, step_name STRING, program_path STRING, "
        "status STRING, start_time TIMESTAMP, end_time TIMESTAMP, duration DOUBLE, "
        "error_msg STRING) USING DELTA"
    )


def batch_id(run_date: date, job_start_ms: int) -> str:
    started = datetime.fromtimestamp(job_start_ms / 1000, tz=timezone.utc)
    return f"BANK_{run_date:%Y%m%d}_{started:%Y%m%dT%H%M%S}"


def _utc_naive(epoch_ms: int) -> datetime:
    return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).replace(tzinfo=None)


def control_rows(run: Mapping, run_date: date) -> list[dict]:
    run_batch_id = batch_id(run_date, run["start_time"])
    rows = []
    tasks = run.get("tasks", [])
    for step_num, task_key, step_name, program_path in STEPS:
        matches = [task for task in tasks if task.get("task_key") == task_key]
        if not matches:
            continue
        task = max(matches, key=lambda item: item.get("attempt_number", 0))
        state = task.get("state") or {}
        result_state = state.get("result_state")
        end_ms = task.get("end_time")
        if result_state in ("UPSTREAM_FAILED", "UPSTREAM_CANCELED", "SKIPPED", "EXCLUDED") or not end_ms:
            continue
        start_ms = task["start_time"]
        start_time = _utc_naive(start_ms)
        end_time = _utc_naive(end_ms)
        status = "PASS" if result_state == "SUCCESS" else "FAIL"
        error_msg = ""
        if status == "FAIL":
            state_message = state.get("state_message") or ""
            error_msg = f"SYSCC={result_state} {state_message}".rstrip()[:ERROR_MSG_MAX]
        rows.append(
            {
                "batch_id": run_batch_id,
                "step_num": step_num,
                "step_name": step_name,
                "program_path": program_path,
                "status": status,
                "start_time": start_time,
                "end_time": end_time,
                "duration": (end_time - start_time).total_seconds(),
                "error_msg": error_msg,
            }
        )
    return rows


def _sql_string(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def insert_sql(rows: list[dict]) -> str:
    if not rows:
        raise ValueError("rows must not be empty")
    values = []
    for row in rows:
        start = row["start_time"].strftime("%Y-%m-%d %H:%M:%S.%f")
        end = row["end_time"].strftime("%Y-%m-%d %H:%M:%S.%f")
        values.append(
            "("
            + ", ".join(
                (
                    _sql_string(row["batch_id"]),
                    str(row["step_num"]),
                    _sql_string(row["step_name"]),
                    _sql_string(row["program_path"]),
                    _sql_string(row["status"]),
                    f"TIMESTAMP'{start}'",
                    f"TIMESTAMP'{end}'",
                    f"CAST({row['duration']!r} AS DOUBLE)",
                    _sql_string(row["error_msg"]),
                )
            )
            + ")"
        )
    return (
        f"INSERT INTO {TARGET} "
        "(batch_id, step_num, step_name, program_path, status, start_time, end_time, duration, error_msg) "
        "VALUES " + ", ".join(values)
    )


def fetch_run_sdk(run_id: int) -> dict:
    if WorkspaceClient is None:
        raise RuntimeError("databricks-sdk is required to fetch a workflow run")
    return WorkspaceClient().jobs.get_run(run_id).as_dict()


def run(
    execute: Callable[[str], object],
    fetch_run: Callable[[int], Mapping],
    run_id: int,
    business_date: date | str,
) -> dict:
    business_date_value = validate_param("business_date", str(business_date), required=True)
    run_date = date.fromisoformat(business_date_value)
    execute(ddl())
    current_run = fetch_run(run_id)
    rows = control_rows(current_run, run_date)
    if rows:
        execute(insert_sql(rows))
    for row in rows:
        print(f"NOTE: Step {row['step_num']} {'PASSED' if row['status'] == 'PASS' else 'FAILED'}")
    return {
        "batch_id": rows[0]["batch_id"] if rows else batch_id(run_date, current_run["start_time"]),
        "rows_written": len(rows),
        "pass": sum(row["status"] == "PASS" for row in rows),
        "fail": sum(row["status"] == "FAIL" for row in rows),
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--business-date", required=True)
    ap.add_argument("--run-id", required=True, type=int)
    ap.add_argument("--report-month")
    ap.add_argument("--region")
    ap.add_argument("--abort-on-err")
    args, _unknown = ap.parse_known_args(argv)
    return args


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.getOrCreate()
    result = run(spark.sql, fetch_run_sdk, args.run_id, args.business_date)
    print(
        f"run_daily_banking: batch_id={result['batch_id']} rows_written={result['rows_written']} "
        f"pass={result['pass']} fail={result['fail']}"
    )
    return 0


if __name__ == "__main__":
    _rc = main()
    if _rc:
        raise SystemExit(_rc)
