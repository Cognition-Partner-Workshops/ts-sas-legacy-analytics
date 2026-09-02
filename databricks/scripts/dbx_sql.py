"""Run a Databricks SQL file through the Statement Execution API."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests


def _request(method: str, url: str, **kwargs: Any) -> dict[str, Any]:
    response = requests.request(method, url, timeout=60, **kwargs)
    response.raise_for_status()
    return response.json()


def execute(host: str, token: str, warehouse_id: str, statement: str) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    base_url = host.rstrip("/")
    body = {
        "warehouse_id": warehouse_id,
        "statement": statement,
        "wait_timeout": "50s",
        "disposition": "INLINE",
    }
    result = _request(
        "POST",
        f"{base_url}/api/2.0/sql/statements",
        headers=headers,
        json=body,
    )
    statement_id = result.get("statement_id")
    while result.get("status", {}).get("state") in {"PENDING", "RUNNING"}:
        time.sleep(1)
        result = _request(
            "GET",
            f"{base_url}/api/2.0/sql/statements/{statement_id}",
            headers=headers,
        )
    return result


def run_sql(path: Path, warehouse_id: str) -> int:
    host = os.environ.get("DATABRICKS_HOST")
    token = os.environ.get("DATABRICKS_TOKEN")
    if not host or not token:
        print("DATABRICKS_HOST and DATABRICKS_TOKEN are required", file=sys.stderr)
        return 2

    statements = [item.strip() for item in path.read_text().split(";\n") if item.strip()]
    for number, statement in enumerate(statements, start=1):
        result = execute(host, token, warehouse_id, statement)
        state = result.get("status", {}).get("state", "UNKNOWN")
        print(f"statement {number}: {state}")
        rows = result.get("result", {}).get("data_array", [])
        if rows:
            print(rows[:5])
        if state == "FAILED":
            error = result.get("status", {}).get("error", result.get("error", {}))
            print(error, file=sys.stderr)
            return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sql_file", type=Path)
    parser.add_argument("--warehouse-id", default="565cd2fd713738c4")
    args = parser.parse_args()
    return run_sql(args.sql_file, args.warehouse_id)


if __name__ == "__main__":
    raise SystemExit(main())
