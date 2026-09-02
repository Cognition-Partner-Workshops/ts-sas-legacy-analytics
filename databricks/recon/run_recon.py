"""Recon harness CLI.

    python -m recon.run_recon --unit U3 --mode live --business-date 2024-01-31 --out out/

fixture mode reads target rows from local CSVs (`--target-dir`, default
databricks/tests/fixtures/target) so the harness can be self-tested without a warehouse.
live mode reads `sas_legacy.<schema>.<table>` through the SQL warehouse (one window per run:
one multi-metric aggregate statement per table, plus one keyed SELECT for tables under the
row-diff tier) and appends a row to `sas_legacy.sas_recon.run_log`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from collections.abc import Callable
from dataclasses import replace
from datetime import date
from pathlib import Path

if __package__ in (None, ""):  # executed as a plain script (spark_python_task)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "recon"

from recon import CAVEAT, RECON_MODE, TOLERANCES_VERSION
from recon.io import (
    ReferenceMissing,
    load_reference_manifest,
    load_reference_table,
    read_csv,
)
from recon.rules import (
    RuleResult,
    aggregate_sql,
    compare_aggregates,
    local_aggregates,
    ml5,
    ml7,
    ml8,
    now_iso,
    numeric_columns,
    resolve_xlsx,
    row_level,
    t9,
    t9_declared_unexercised,
    t10,
    t11,
    t12,
)
from recon.units import ROW_DIFF_TIER, TableSpec, tables_for

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DEFAULT_REF = REPO / "docs" / "migration" / "recon" / "reference"
DEFAULT_FIXTURE_TARGET = HERE.parent / "tests" / "fixtures" / "target"
DEFAULT_WAREHOUSE = "565cd2fd713738c4"
CATALOG = "sas_legacy"
XLSX_FETCH_OVERRIDE: Callable[[str], bytes] | None = None


def resolve_spec(spec: TableSpec, business_date: date | str) -> TableSpec:
    date_value = (
        business_date.isoformat() if isinstance(business_date, date) else str(business_date)
    )
    yyyymmdd = date_value.replace("-", "")
    rules = {
        column: rule.replace("{yyyymmdd}", yyyymmdd)
        for column, rule in spec.column_rules.items()
    }
    prefix = spec.latest_prefix.replace("{yyyymmdd}", yyyymmdd) if spec.latest_prefix else None
    return replace(spec, column_rules=rules, latest_prefix=prefix)


class TargetReader:
    """Reads target tables either from local CSVs (fixture) or the warehouse (live)."""

    def __init__(self, mode: str, target_dir: Path | None, warehouse=None):
        self.mode = mode
        self.target_dir = target_dir
        self.wh = warehouse

    def fqn(self, spec: TableSpec) -> str:
        return f"{CATALOG}.{spec.schema}.{spec.name}"

    def count(self, spec: TableSpec) -> int:
        if self.mode == "fixture":
            return len(self._local(spec.name, spec))
        where = self._latest_where(spec)
        sql = f"SELECT COUNT(*) AS n FROM {self.fqn(spec)}"
        return int(self.wh.query(f"{sql} WHERE {where}" if where else sql)[0]["n"])

    def rows(self, spec: TableSpec, name: str | None = None) -> list[dict] | None:
        name = name or spec.name
        if self.mode == "fixture":
            p = self.target_dir / f"{name}.csv"
            if not p.is_file():
                return None
            rows = read_csv(p)
            return self._filter_latest(spec, rows) if name == spec.name else rows
        fqn = f"{CATALOG}.{spec.schema}.{name}"
        where = self._latest_where(spec) if name == spec.name else None
        sql = f"SELECT * FROM {fqn}"
        return self.wh.query(f"{sql} WHERE {where}" if where else sql)

    def aggregates(self, spec: TableSpec, num_cols, ref_rows) -> dict:
        keys = spec.distinct_keys or spec.keys
        if self.mode == "fixture":
            return local_aggregates(self._local(spec.name, spec), num_cols, keys)
        return self.wh.query(aggregate_sql(self.fqn(spec), num_cols, keys, self._latest_where(spec)))[0]

    def _latest_where(self, spec: TableSpec) -> str | None:
        if not spec.latest_key or not spec.latest_prefix:
            return None
        key = spec.latest_key
        prefix = spec.latest_prefix
        fqn = self.fqn(spec)
        return f"{key} = (SELECT MAX({key}) FROM {fqn} WHERE {key} LIKE '{prefix}%')"

    def _filter_latest(self, spec: TableSpec, rows: list[dict]) -> list[dict]:
        if not spec.latest_key or not spec.latest_prefix:
            return rows
        key = spec.latest_key
        matches = [row.get(key) for row in rows if (row.get(key) or "").startswith(spec.latest_prefix)]
        if not matches:
            return []
        latest = max(matches)
        return [row for row in rows if row.get(key) == latest]

    def _local(self, name: str, spec: TableSpec | None = None) -> list[dict]:
        p = self.target_dir / f"{name}.csv"
        if not p.is_file():
            raise SystemExit(f"target fixture missing: {p}")
        rows = read_csv(p)
        return self._filter_latest(spec, rows) if spec else rows


def recon_table(
    spec: TableSpec,
    ref_dir: Path,
    tgt: TargetReader,
    xlsx_path: str | None,
    xlsx_info: dict | None = None,
):
    ref_rows = load_reference_table(ref_dir, spec.name)
    columns = list(ref_rows[0].keys()) if ref_rows else list(spec.keys)
    results: list[RuleResult] = []
    n_target = tgt.count(spec)
    tier = "row_level" if n_target < ROW_DIFF_TIER else "aggregate_only"

    if tier == "row_level":
        tgt_rows = tgt.rows(spec) or []
        results += row_level(spec, ref_rows, tgt_rows, columns)
    else:
        tgt_rows = None
        results.append(
            RuleResult("T-1", spec.name, None, "PASS" if n_target == len(ref_rows) else "FAIL",
                       len(ref_rows), n_target, "row count exact (aggregate tier)")
        )
        results.append(RuleResult("T-2", spec.name, ",".join(spec.keys), "NOT_APPLICABLE",
                                  None, None, f"table >= {ROW_DIFF_TIER} rows; keyed diff skipped"))

    num_cols = numeric_columns(spec, ref_rows, columns)
    ref_agg = local_aggregates(ref_rows, num_cols, spec.distinct_keys or spec.keys)
    tgt_agg = tgt.aggregates(spec, num_cols, ref_rows)
    results += compare_aggregates(spec, ref_agg, tgt_agg)

    if spec.t9_unexercised:
        results.append(t9_declared_unexercised(spec))
    elif spec.t9_group and tgt_rows is not None:
        results.append(t9(spec, ref_rows, tgt_rows))
    results.append(t10(spec))
    results.append(t11(spec))
    results.append(t12(spec, xlsx_info if xlsx_info and xlsx_info.get("error") else xlsx_path))

    if spec.ml and tgt_rows is not None:
        if "pd" in columns:
            results.append(ml5(spec, ref_rows, tgt_rows))
            results.append(ml7(spec, tgt_rows))
        ml_fail = any(r.rule.startswith("ML-") and r.verdict == "FAIL" for r in results)
        ref_dbg = load_reference_table(ref_dir, spec.woe_debug, required=False) if spec.woe_debug else None
        tgt_dbg = tgt.rows(spec, spec.woe_debug) if (spec.woe_debug and ml_fail) else None
        results.append(ml8(spec, ml_fail, ref_dbg, tgt_dbg))

    return {
        "table": spec.name,
        "schema": spec.schema,
        "keys": list(spec.keys),
        "tier": tier,
        "rows_reference": len(ref_rows),
        "rows_target": n_target,
        "results": [r.to_dict() for r in results],
    }


def summarize(report: dict) -> str:
    lines = [
        f"# recon {report['unit']} {report['business_date']} — {report['overall']}",
        (
            f"mode: {report['mode']} ({report['caveat']}); "
            f"tolerances {report['tolerances_version']}; run_id {report['run_id']}"
        ),
        f"reference manifest sha256: {report['reference_manifest_sha256']}",
    ]
    if report.get("xlsx"):
        info = report["xlsx"]
        lines.append(f"xlsx: {info['xlsx_source_path']} sha256={info.get('xlsx_sha256')}")
    lines.extend([
        "",
        "| table | tier | ref rows | tgt rows | PASS | FAIL | N/A | DECL-UNEX | failing rules |",
        "|---|---|---|---|---|---|---|---|---|",
    ])
    for t in report["tables"]:
        vs = [r["verdict"] for r in t["results"]]
        failing = sorted({f"{r['rule']}:{r['column']}" if r["column"] else r["rule"]
                          for r in t["results"] if r["verdict"] == "FAIL"})
        lines.append(
            f"| {t['table']} | {t['tier']} | {t['rows_reference']} | {t['rows_target']} | "
            f"{vs.count('PASS')} | {vs.count('FAIL')} | {vs.count('NOT_APPLICABLE') + vs.count('INFO')} | "
            f"{vs.count('DECLARED-UNEXERCISED')} | {', '.join(failing)[:80] or '-'} |"
        )
    lines.append("")
    lines.append(f"warehouse statements: {report['warehouse']['statements']}, "
                 f"elapsed_s: {report['warehouse']['elapsed_s']:.1f}")
    return "\n".join(lines[:30]) + "\n"


def run_log_sql(report: dict) -> str:
    def q(s: str) -> str:
        return "'" + s.replace("'", "''") + "'"

    return (
        f"INSERT INTO {CATALOG}.sas_recon.run_log "
        "(run_id, run_ts, unit, business_date, mode, tolerances_version, "
        "reference_manifest_sha256, overall, n_pass, n_fail, n_na, statements, elapsed_s, summary) "
        f"VALUES ({q(report['run_id'])}, TIMESTAMP{q(report['run_ts'])}, {q(report['unit'])}, "
        f"DATE{q(report['business_date'])}, {q(report['mode'])}, {q(report['tolerances_version'])}, "
        f"{q(report['reference_manifest_sha256'])}, {q(report['overall'])}, "
        f"{report['counts']['PASS']}, {report['counts']['FAIL']}, {report['counts']['NOT_APPLICABLE']}, "
        f"{report['warehouse']['statements']}, {report['warehouse']['elapsed_s']:.3f}, "
        f"{q(report['summary'])})"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--unit", required=True, choices=["U1", "U2", "U3", "U4", "U5"])
    ap.add_argument("--mode", required=True, choices=["fixture", "live"])
    ap.add_argument("--business-date", required=True)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--reference-dir", type=Path, default=DEFAULT_REF)
    ap.add_argument("--target-dir", type=Path, default=DEFAULT_FIXTURE_TARGET,
                    help="fixture mode: directory of <table>.csv target rows")
    ap.add_argument("--warehouse-id", default=os.environ.get("RECON_WAREHOUSE_ID", DEFAULT_WAREHOUSE))
    ap.add_argument("--xlsx-path", default=None, help="T-12 workbook path (U4 only)")
    ap.add_argument("--no-run-log", action="store_true", help="live: skip run_log append")
    a = ap.parse_args(argv)

    try:
        manifest, manifest_sha = load_reference_manifest(a.reference_dir)
    except ReferenceMissing as exc:
        print(exc, file=sys.stderr)
        return 2

    wh = None
    if a.mode == "live":
        from recon.warehouse import Warehouse

        wh = Warehouse(a.warehouse_id)
    tgt = TargetReader(a.mode, a.target_dir, wh)
    fetch = XLSX_FETCH_OVERRIDE or (wh.download_file if wh else None)
    local_xlsx, xlsx_info = resolve_xlsx(a.xlsx_path, fetch)

    tables = []
    try:
        for spec in tables_for(a.unit):
            resolved = resolve_spec(spec, a.business_date)
            tables.append(recon_table(resolved, a.reference_dir, tgt, local_xlsx, xlsx_info))
    except ReferenceMissing as exc:
        print(exc, file=sys.stderr)
        return 2

    verdicts = [r["verdict"] for t in tables for r in t["results"]]
    counts = {k: verdicts.count(k)
              for k in ("PASS", "FAIL", "NOT_APPLICABLE", "INFO", "DECLARED-UNEXERCISED")}
    report = {
        "run_id": str(uuid.uuid4()),
        "run_ts": now_iso(),
        "unit": a.unit,
        "business_date": a.business_date,
        "mode": RECON_MODE,
        "execution_mode": a.mode,
        "caveat": CAVEAT,
        "tolerances_version": TOLERANCES_VERSION,
        "reference_manifest_sha256": manifest_sha,
        "reference_manifest": manifest,
        "xlsx": xlsx_info,
        "overall": "PASS" if counts["FAIL"] == 0 else "FAIL",
        "counts": counts,
        "warehouse": {
            "statements": wh.statements if wh else 0,
            "elapsed_s": wh.elapsed_s if wh else 0.0,
        },
        "tables": tables,
    }
    report["summary"] = summarize(report)

    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "recon.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    (a.out / "recon.summary.md").write_text(report["summary"], encoding="utf-8")
    print(report["summary"])

    if wh and not a.no_run_log:
        wh.execute(run_log_sql(report))
    return 0 if report["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
