"""Generate the W0-R reference outputs.

    cd docs/migration/recon
    python -m reference_impl.run_all --business-date 2024-01-31 --report-month 202401

Writes docs/migration/recon/reference/<table>.csv (14 tables, lower_snake
columns, ISO dates, fixed run-time sentinels), alternates/ for the
AMBIGUITIES.md alternate readings, and manifest.json.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import os
import subprocess
from typing import Dict, List

from . import run_daily_banking
from .seeds import SEED_FILES, Row, load_all, sha256

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
DEFAULT_CSV_ROOT = os.path.join(REPO_ROOT, "Data", "csv")
DEFAULT_OUT = os.path.join(HERE, "..", "reference")

CAVEAT = "reference-derived, not SAS-produced"
GENERATOR = "python -m reference_impl.run_all --business-date 2024-01-31 --report-month 202401"
CHANGELOG = [
    {"date": "2026-09-02", "decision": "DEC-017 (a)",
     "changed": ["risk_scores.csv"],
     "manifest_sha256_before": "aea7c04a35b6171c343a1eedc45bb509402b746864a6e111ac6608d154625cc7",
     "reason": "MODEL_ID upper-cased at %parmv entry (_CASE=U default): CRM-2023-Q4-v2 -> CRM-2023-Q4-V2"},
]

# SAS table -> reference csv name, T-2 sort key (analysis §6). monthly_rwa adds
# risk_weight because the SAS GROUP BY includes it (AMB-07).
TABLES = [
    ("STG_BANK.CUST_ACCOUNTS_DAILY", "cust_accounts_daily", ["account_id", "snapshot_date"]),
    ("STG_BANK.ACCT_EXCEPTIONS", "acct_exceptions", ["account_id"]),
    ("CURATED.DAILY_TRANSACTIONS", "daily_transactions", ["transaction_id"]),
    ("CURATED.RUNNING_BALANCES", "running_balances", ["account_id", "transaction_date", "transaction_id"]),
    ("CURATED.TXN_ANOMALIES", "txn_anomalies", ["transaction_id"]),
    ("WORK.TXN_REJECTED", "txn_rejected", ["transaction_id"]),
    ("CURATED.RISK_SCORES", "risk_scores", ["account_id", "score_date"]),
    ("CURATED.RISK_MIGRATION", "risk_migration", ["account_id", "score_date"]),
    ("REPORTS.RISK_SUMMARY", "risk_summary", ["account_type", "new_risk_rating"]),
    ("REPORTS.MONTHLY_RWA", "monthly_rwa", ["report_month", "account_type", "customer_segment", "risk_weight"]),
    ("REPORTS.DELINQUENCY_AGING", "delinquency_aging", ["report_month", "account_type", "region_code", "delinq_bucket"]),
    ("REPORTS.LLP_COVERAGE", "llp_coverage", ["report_month", "account_type"]),
    ("REPORTS.CAPITAL_ADEQUACY", "capital_adequacy", ["report_month"]),
    ("ARCHIVE.BATCH_HISTORY", "archive_batch_history", ["batch_id", "step_num"]),
]
ALTERNATES = [
    ("ALT.ACCT_EXCEPTIONS_WITH_CODE", "acct_exceptions__with_code", ["account_id", "exception_code"]),
    ("ALT.TXN_REJECTED_WITH_REASON", "txn_rejected__with_reason", ["transaction_id"]),
    ("ALT.DAILY_TRANSACTIONS_APPENDED_WIDE", "daily_transactions__appended_rows_wide", ["transaction_id"]),
    ("ALT.RISK_SCORES_WOE_DEBUG", "risk_scores__woe_debug", ["account_id", "score_date"]),
]


def fmt(v) -> str:
    """CSV rendering: missing -> '', dates ISO, integral floats without '.0',
    other floats via repr (shortest round-trip)."""
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, dt.date):
        return v.isoformat()
    if isinstance(v, float):
        if math.isnan(v):
            return ""
        if v.is_integer() and abs(v) < 1e15:
            return str(int(v))
        return repr(v)
    return str(v)


def sort_key(row: Dict[str, str], keys: List[str]):
    # Missing sorts low (SAS); dates/strings compare as their ISO/text form,
    # numbers numerically.
    def one(k):
        v = row[k]
        if v == "":
            return (0, 0.0, "")
        try:
            return (1, float(v), "")
        except ValueError:
            return (2, 0.0, v)
    return tuple(one(k) for k in keys)


def write_table(rows: List[Row], path: str, keys: List[str]) -> int:
    cols = [c.lower() for c in rows[0].keys()] if rows else keys
    rendered = [{c.lower(): fmt(v) for c, v in r.items()} for r in rows]
    rendered.sort(key=lambda r: sort_key(r, keys))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rendered)
    return len(rendered)


SOURCE_DIRS = ["Programs", "BatchJobs", "Config", "Formats", "Macro", "Data"]


def source_commit() -> str:
    """Last commit touching the read-only SAS source + seed directories."""
    try:
        return subprocess.check_output(["git", "log", "-1", "--format=%H", "--", *SOURCE_DIRS],
                                       cwd=REPO_ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):  # git absent
        return "unknown"


def generate(business_date: dt.date, report_month: str, csv_root: str, out_dir: str) -> dict:
    libs = load_all(csv_root)
    tables = run_daily_banking.run(libs, business_date, report_month)

    os.makedirs(os.path.join(out_dir, "alternates"), exist_ok=True)
    outputs = {}
    for sas_name, csv_name, keys in TABLES:
        path = os.path.join(out_dir, f"{csv_name}.csv")
        n = write_table(tables[sas_name], path, keys)
        outputs[f"{csv_name}.csv"] = {"sas_table": sas_name, "rows": n, "sha256": sha256(path)}
    alternates = {}
    for sas_name, csv_name, keys in ALTERNATES:
        path = os.path.join(out_dir, "alternates", f"{csv_name}.csv")
        n = write_table(tables[sas_name], path, keys)
        alternates[f"alternates/{csv_name}.csv"] = {"rows": n, "sha256": sha256(path)}

    inputs = {}
    for lib_table, rel in sorted(SEED_FILES.items(), key=lambda kv: kv[1]):
        p = os.path.join(csv_root, rel)
        with open(p, newline="", encoding="utf-8") as fh:
            n = sum(1 for _ in fh) - 1
        inputs[f"Data/csv/{rel}"] = {"sas_table": lib_table, "rows": n, "sha256": sha256(p),
                                     "used": lib_table != "RAW_BANK.DAILY_RATES"}

    manifest = {
        "caveat": CAVEAT,
        "mode": "DEGRADED (snapshot Data/csv; no SAS runtime; results apply to the seed snapshot, not production)",
        "tolerance_version": "v1 (.migration/03_recon_tolerances.md)",
        "business_date": business_date.isoformat(),
        "report_month": report_month,
        "batch_id": run_daily_banking.batch_id(business_date),
        "runtime_sentinels": {"timestamp": run_daily_banking.SENTINEL_TS, "duration": 0},
        "source_commit": source_commit(),
        "source_commit_scope": "last commit touching " + ", ".join(SOURCE_DIRS) + "/",
        "generator": GENERATOR,
        "changelog": CHANGELOG,
        "outputs": outputs,
        "alternates": alternates,
        "inputs": inputs,
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=False)
        fh.write("\n")
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--business-date", required=True, help="ISO date, e.g. 2024-01-31")
    ap.add_argument("--report-month", required=True, help="yyyymm, e.g. 202401")
    ap.add_argument("--csv-root", default=DEFAULT_CSV_ROOT)
    ap.add_argument("--out", default=DEFAULT_OUT)
    a = ap.parse_args(argv)
    m = generate(dt.date.fromisoformat(a.business_date), a.report_month, a.csv_root, os.path.abspath(a.out))
    for name, meta in m["outputs"].items():
        print(f"{name:32s} rows={meta['rows']:6d} sha256={meta['sha256']}")
    print(f"manifest.json written; caveat: {m['caveat']}")


if __name__ == "__main__":
    main()
