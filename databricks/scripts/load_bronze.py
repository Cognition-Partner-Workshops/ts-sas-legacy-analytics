"""Upload seed CSVs and materialize the typed bronze tables."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from dbx_sql import execute

EXPECTED = {
    "cust_accounts": ("oracle_dw/CUST_ACCOUNTS.csv", 487),
    "cust_demographics": ("oracle_dw/CUST_DEMOGRAPHICS.csv", 250),
    "bureau_scores": ("oracle_dw/BUREAU_SCORES.csv", 500),
    "payment_history": ("oracle_dw/PAYMENT_HISTORY.csv", 248),
    "collateral": ("oracle_dw/COLLATERAL.csv", 114),
    "loan_details": ("oracle_dw/LOAN_DETAILS.csv", 248),
    "daily_rates": ("raw_bank/DAILY_RATES.csv", 455),
    "txn_feed_20240131": ("raw_bank/TXN_FEED_20240131.csv", 622),
    "daily_transactions_hist": ("curated/DAILY_TRANSACTIONS.csv", 18293),
}


def _query(host: str, token: str, warehouse_id: str, sql: str) -> list[list[Any]]:
    result = execute(host, token, warehouse_id, sql)
    state = result.get("status", {}).get("state")
    if state != "SUCCEEDED":
        raise RuntimeError(f"SQL failed ({state}): {result.get('status', {}).get('error')}")
    return result.get("result", {}).get("data_array", [])


def _upload(repo: Path, relative: str) -> None:
    source = repo / "Data" / "csv" / relative
    target = f"dbfs:/Volumes/sas_legacy/sas_bronze/landing/seed/{Path(relative).name}"
    env = os.environ.copy()
    env["DATABRICKS_HOST"] = env["DATABRICKS_DEMO_HOST"]
    env["DATABRICKS_TOKEN"] = env["DATABRICKS_DEMO_TOKEN"]
    subprocess.run(
        ["databricks", "fs", "cp", "--overwrite", str(source), target],
        check=True,
        env=env,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(repo: Path, warehouse_id: str) -> int:
    host = os.environ.get("DATABRICKS_HOST")
    token = os.environ.get("DATABRICKS_TOKEN")
    if not host or not token:
        print("DATABRICKS_HOST and DATABRICKS_TOKEN are required", file=sys.stderr)
        return 2
    env = os.environ.copy()
    env["DATABRICKS_HOST"] = host
    env["DATABRICKS_TOKEN"] = token
    subprocess.run(
        ["databricks", "fs", "mkdirs", "dbfs:/Volumes/sas_legacy/sas_bronze/landing/seed"],
        check=True,
        env=env,
    )
    for relative, _ in EXPECTED.values():
        _upload(repo, relative)

    sql_path = Path(__file__).parents[1] / "sql" / "10_bronze.sql"
    statements = [item.strip() for item in sql_path.read_text().split(";\n") if item.strip()]
    for statement in statements:
        _query(host, token, warehouse_id, statement)

    counts: dict[str, int] = {}
    for table, (_, expected) in EXPECTED.items():
        rows = _query(host, token, warehouse_id, f"SELECT COUNT(*) FROM sas_legacy.sas_bronze.{table}")
        count = int(rows[0][0])
        counts[table] = count
        print(f"{table}: {count} (expected {expected})")
        if count != expected:
            raise RuntimeError(f"{table}: loaded {count}, expected {expected}")

    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
    ).strip()
    values = []
    for table, (relative, _) in EXPECTED.items():
        path = repo / "Data" / "csv" / relative
        filename = Path(relative).name
        values.append(
            "("
            f"'{filename}', {counts[table]}, '{_sha256(path)}', "
            f"DATE '2024-01-31', '{source_commit}', current_timestamp()"
            ")"
        )
    manifest_sql = (
        "INSERT INTO sas_legacy.sas_bronze._manifest "
        "(file, rows, sha256, business_date, source_commit, loaded_at) VALUES "
        + ", ".join(values)
    )
    _query(host, token, warehouse_id, manifest_sql)
    manifest_rows = _query(
        host,
        token,
        warehouse_id,
        "SELECT file, rows FROM sas_legacy.sas_bronze._manifest ORDER BY file",
    )
    for filename, manifest_count in manifest_rows:
        print(f"manifest {filename}: {manifest_count}")
        matching_table = next(
            table for table, (relative, _) in EXPECTED.items() if Path(relative).name == filename
        )
        if int(manifest_count) != counts[matching_table]:
            raise RuntimeError(f"manifest mismatch for {filename}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).parents[2])
    parser.add_argument("--warehouse-id", default="565cd2fd713738c4")
    args = parser.parse_args()
    return run(args.repo, args.warehouse_id)


if __name__ == "__main__":
    raise SystemExit(main())
