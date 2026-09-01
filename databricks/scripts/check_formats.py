"""Check deployed format-table cardinalities against the SAS format source."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from dbx_sql import execute

EXPECTED_TABLES = {
    "accttype": 12,
    "acctstat": 9,
    "riskrate": 8,
    "txncat": 11,
    "delqbkt": 7,
    "balrange": 8,
    "region": 8,
    "custseg": 7,
    "lnpurp": 9,
}


def parse_counts(source: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for match in re.finditer(
        r"(?m)^\s*value\s+(\$?[A-Za-z]\w*)\s+(.*?);", source, re.DOTALL | re.IGNORECASE
    ):
        name, body = match.groups()
        entries = [
            line for line in body.splitlines()
            if "=" in line and not line.lstrip().upper().startswith("OTHER")
        ]
        has_other = bool(re.search(r"(?m)^\s*OTHER\s*=", body))
        counts[name.lstrip("$").lower()] = len(entries) + int(has_other)
    return counts


def run(repo: Path, warehouse_id: str) -> int:
    host = os.environ.get("DATABRICKS_HOST")
    token = os.environ.get("DATABRICKS_TOKEN")
    if not host or not token:
        print("DATABRICKS_HOST and DATABRICKS_TOKEN are required", file=sys.stderr)
        return 2
    parsed = parse_counts((repo / "Formats" / "banking_formats.sas").read_text())
    lines = ["format counts (source expected / deployed actual)"]
    failed = False
    for name, expected in EXPECTED_TABLES.items():
        source_count = parsed.get(name)
        rows = execute(
            host,
            token,
            warehouse_id,
            f"SELECT COUNT(*) FROM sas_legacy.sas_ref.fmt_{name}",
        )
        state = rows.get("status", {}).get("state")
        if state != "SUCCEEDED":
            raise RuntimeError(f"format query failed for {name}: {rows}")
        actual = int(rows.get("result", {}).get("data_array", [[-1]])[0][0])
        ok = source_count == expected == actual
        lines.append(f"fmt_{name}: {source_count} / {expected} / {actual} -> {'PASS' if ok else 'FAIL'}")
        failed |= not ok
    evidence = repo / "databricks" / "evidence" / "w0a_formats.txt"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).parents[2])
    parser.add_argument("--warehouse-id", default="565cd2fd713738c4")
    args = parser.parse_args()
    return run(args.repo, args.warehouse_id)


if __name__ == "__main__":
    raise SystemExit(main())
