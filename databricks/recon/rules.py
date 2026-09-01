"""Tolerance rules T-1..T-12 and ML-1..ML-8 (.migration/03_recon_tolerances.md v1).

Row values arrive as strings (CSV / Statement Execution JSON_ARRAY) or None for NULL.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from .units import EDGE_EPS, RATING_EDGES, TableSpec, classify_column

Row = dict[str, str | None]
Key = tuple[str, ...]

ABS_TOL = {"T-4": Decimal("0.005"), "T-5": 1e-6, "T-6": 1e-6, "ML-2": 1e-9, "ML-4": 0.01}
ML3_TOL = {"lgd": 1e-9, "ead": 0.005}
ML4_SUM_TOL = 0.05
MAX_EXAMPLES = 20

_SAS_DATE = re.compile(r"^(\d{2})([A-Z]{3})(\d{4})$")
_MONTHS = {m: i for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1
)}


@dataclass
class RuleResult:
    rule: str
    table: str
    column: str | None
    verdict: str  # PASS | FAIL | NOT_APPLICABLE | INFO | DECLARED-UNEXERCISED
    reference: object = None
    target: object = None
    detail: str = ""
    examples: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------- normalisation


def is_null(v: str | None) -> bool:
    return v is None or v == "" or v == "."


def norm_str(v: str | None) -> str | None:
    if is_null(v):
        return None
    return v.rstrip()  # T-3: rtrim only, case preserved


def norm_date(v: str | None) -> str | None:
    if is_null(v):
        return None
    s = v.strip()
    m = _SAS_DATE.match(s.upper())
    if m:
        return f"{m.group(3)}-{_MONTHS[m.group(2)]:02d}-{m.group(1)}"
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return s


def to_decimal(v: str | None) -> Decimal | None:
    if is_null(v):
        return None
    try:
        return Decimal(v.strip())
    except InvalidOperation:
        return None


def to_float(v: str | None) -> float | None:
    if is_null(v):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def norm_exact(v: str | None) -> str | None:
    """T-3 canonical form: numbers compared numerically, dates as ISO, strings rtrimmed."""
    if is_null(v):
        return None
    d = to_decimal(v)
    if d is not None:
        return format(d.normalize(), "f")
    return norm_date(norm_str(v))


def key_of(row: Row, keys: Key) -> Key:
    return tuple(norm_exact(row.get(k)) or "" for k in keys)


# ---------------------------------------------------------------- per-column compare


def _compare_value(rule: str, column: str, ref: str | None, tgt: str | None) -> bool:
    if rule == "T-7":
        return not is_null(tgt)  # excluded from comparison; non-null asserted
    if is_null(ref) or is_null(tgt):
        return is_null(ref) and is_null(tgt)
    if rule == "T-4":
        a, b = to_decimal(ref), to_decimal(tgt)
        return a is not None and b is not None and abs(a - b) <= ABS_TOL["T-4"]
    if rule in ("T-5", "T-6", "ML-2", "ML-4"):
        a, b = to_float(ref), to_float(tgt)
        return a is not None and b is not None and abs(a - b) <= ABS_TOL[rule]
    if rule == "ML-3":
        a, b = to_float(ref), to_float(tgt)
        return a is not None and b is not None and abs(a - b) <= ML3_TOL.get(column, 1e-9)
    # T-3, ML-1, ML-6 and anything else: exact
    return norm_exact(ref) == norm_exact(tgt)


def row_level(
    spec: TableSpec, ref_rows: list[Row], tgt_rows: list[Row], columns: list[str]
) -> list[RuleResult]:
    """T-1, T-2, and the per-column row rule for every shared column (keyed diff)."""
    out: list[RuleResult] = []
    out.append(
        RuleResult(
            "T-1", spec.name, None,
            "PASS" if len(ref_rows) == len(tgt_rows) else "FAIL",
            len(ref_rows), len(tgt_rows), "row count exact",
        )
    )
    if spec.multiset:
        out.extend(_multiset_rows(spec, ref_rows, tgt_rows, columns))
        return out
    ref_by = {key_of(r, spec.keys): r for r in ref_rows}
    tgt_by = {key_of(r, spec.keys): r for r in tgt_rows}
    dup_ref = len(ref_rows) - len(ref_by)
    dup_tgt = len(tgt_rows) - len(tgt_by)
    missing = sorted(set(ref_by) - set(tgt_by))
    extra = sorted(set(tgt_by) - set(ref_by))
    t2_ok = not missing and not extra and dup_ref == 0 and dup_tgt == 0
    out.append(
        RuleResult(
            "T-2", spec.name, ",".join(spec.keys),
            "PASS" if t2_ok else "FAIL",
            len(ref_by), len(tgt_by),
            f"missing_in_target={len(missing)} extra_in_target={len(extra)} "
            f"dup_keys_ref={dup_ref} dup_keys_target={dup_tgt}",
            [list(k) for k in (missing + extra)[:MAX_EXAMPLES]],
        )
    )
    shared = set(ref_by) & set(tgt_by)
    for col in columns:
        if col in spec.keys:
            continue
        rule = classify_column(spec, col)
        if rule in ("T-7",):
            bad = [k for k in shared if is_null(tgt_by[k].get(col))]
            out.append(
                RuleResult(
                    rule, spec.name, col, "PASS" if not bad else "FAIL",
                    "excluded", f"null_count={len(bad)}",
                    "run-time timestamp excluded from comparison; non-null asserted",
                    [list(k) for k in bad[:MAX_EXAMPLES]],
                )
            )
            continue
        mism = []
        for k in shared:
            rv, tv = ref_by[k].get(col), tgt_by[k].get(col)
            if not _compare_value(rule, col, rv, tv):
                mism.append([list(k), rv, tv])
        out.append(
            RuleResult(
                rule, spec.name, col, "PASS" if not mism else "FAIL",
                None, None,
                f"rows_compared={len(shared)} mismatches={len(mism)}",
                mism[:MAX_EXAMPLES],
            )
        )
    return out


def multiset_key(spec: TableSpec, row: Row) -> tuple:
    """Full-row key (DEC-015 (a)): exact per column, except T-4/T-5 numerics which are
    quantised to their tolerance and T-7 run-time columns which are excluded."""
    out = []
    for c in spec.keys:
        rule = classify_column(spec, c)
        v = row.get(c)
        if rule == "T-7":
            continue
        if rule in ("T-4", "T-5") and not is_null(v):
            f = to_float(v)
            out.append(f"{round(f, 2):.2f}" if rule == "T-4" else f"{round(f, 6):.6f}")
        else:
            out.append(norm_exact(v))
    return tuple(out)


def _multiset_rows(
    spec: TableSpec, ref_rows: list[Row], tgt_rows: list[Row], columns: list[str]
) -> list[RuleResult]:
    """T-2 as full-row multiset equality; per-column rules are subsumed by the key.
    T-7 columns keep their non-null assertion."""
    rc = Counter(multiset_key(spec, r) for r in ref_rows)
    tc = Counter(multiset_key(spec, r) for r in tgt_rows)
    missing = sorted((rc - tc).elements(), key=str)
    extra = sorted((tc - rc).elements(), key=str)
    out = [
        RuleResult(
            "T-2", spec.name, "*",
            "PASS" if not missing and not extra else "FAIL",
            {"rows": len(ref_rows), "distinct_rows": len(rc)},
            {"rows": len(tgt_rows), "distinct_rows": len(tc)},
            f"full-row multiset equality (DEC-015 (a)); missing_in_target={len(missing)} "
            f"extra_in_target={len(extra)}; T-7 columns excluded, T-4/T-5 at tolerance",
            [list(k) for k in (missing + extra)[:MAX_EXAMPLES]],
        )
    ]
    for col in columns:
        if classify_column(spec, col) == "T-7":
            n_null = sum(1 for r in tgt_rows if is_null(r.get(col)))
            out.append(
                RuleResult(
                    "T-7", spec.name, col, "PASS" if n_null == 0 else "FAIL",
                    "excluded", f"null_count={n_null}",
                    "run-time timestamp excluded from comparison; non-null asserted",
                )
            )
    return out


# ---------------------------------------------------------------- T-8 aggregates


def numeric_columns(spec: TableSpec, ref_rows: list[Row], columns: list[str]) -> list[str]:
    """Columns whose non-null reference values all parse as numbers (excluding T-7 columns)."""
    cols = []
    for c in columns:
        if classify_column(spec, c) == "T-7":
            continue
        vals = [r.get(c) for r in ref_rows if not is_null(r.get(c))]
        if vals and all(to_decimal(v) is not None for v in vals):
            cols.append(c)
    return cols


def local_aggregates(rows: list[Row], num_cols: list[str], keys: Key) -> dict[str, str | None]:
    agg: dict[str, str | None] = {}
    for c in num_cols:
        vals = [to_decimal(r.get(c)) for r in rows if not is_null(r.get(c))]
        vals = [v for v in vals if v is not None]
        agg[f"sum_{c}"] = format(sum(vals), "f") if vals else None
    for k in keys:
        agg[f"nd_{k}"] = str(len({norm_exact(r.get(k)) for r in rows if not is_null(r.get(k))}))
    return agg


def aggregate_sql(fqn: str, num_cols: list[str], keys: Key) -> str:
    parts = [f"CAST(SUM(`{c}`) AS STRING) AS `sum_{c}`" for c in num_cols]
    parts += [f"CAST(COUNT(DISTINCT `{k}`) AS STRING) AS `nd_{k}`" for k in keys]
    parts.append("CAST(COUNT(*) AS STRING) AS `n_rows`")
    return f"SELECT {', '.join(parts)} FROM {fqn}"


def compare_aggregates(
    spec: TableSpec, ref_agg: dict[str, str | None], tgt_agg: dict[str, str | None]
) -> list[RuleResult]:
    out = []
    for name, rv in ref_agg.items():
        tv = tgt_agg.get(name)
        if name.startswith("sum_"):
            col = name[4:]
            rule = classify_column(spec, col)
            ok = _compare_value(rule if rule in ABS_TOL or rule == "ML-3" else "T-3", col, rv, tv)
            if rule == "ML-4":  # SUM over table abs <= 0.05
                a, b = to_float(rv), to_float(tv)
                ok = a is not None and b is not None and abs(a - b) <= ML4_SUM_TOL
            detail = f"SUM({col}) under {rule} tolerance"
        else:
            col = name[3:]
            ok = norm_exact(rv) == norm_exact(tv)
            detail = f"COUNT(DISTINCT {col}) exact"
        out.append(RuleResult("T-8", spec.name, col, "PASS" if ok else "FAIL", rv, tv, detail))
    return out


# ---------------------------------------------------------------- T-9 grouped counts


def grouped_counts(rows: list[Row], col: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rows:
        g = norm_str(r.get(col)) or "<NULL>"
        counts[g] = counts.get(g, 0) + 1
    return counts


def t9_declared_unexercised(spec: TableSpec) -> RuleResult:
    assert spec.t9_unexercised
    return RuleResult("T-9", spec.name, None, "DECLARED-UNEXERCISED", None, None, spec.t9_unexercised)


def t9(spec: TableSpec, ref_rows: list[Row], tgt_rows: list[Row]) -> RuleResult:
    assert spec.t9_group
    rc, tc = grouped_counts(ref_rows, spec.t9_group), grouped_counts(tgt_rows, spec.t9_group)
    diffs = [[g, rc.get(g), tc.get(g)] for g in sorted(set(rc) | set(tc)) if rc.get(g) != tc.get(g)]
    return RuleResult(
        "T-9", spec.name, spec.t9_group, "PASS" if not diffs else "FAIL", rc, tc,
        f"count per {spec.t9_group} exact", diffs[:MAX_EXAMPLES],
    )


# ---------------------------------------------------------------- ML-5 / ML-7 / ML-8


def _avg_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        r = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = r
        i = j + 1
    return ranks


def spearman(x: list[float], y: list[float]) -> float | None:
    if len(x) < 2:
        return None
    rx, ry = _avg_ranks(x), _avg_ranks(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    vy = math.sqrt(sum((b - my) ** 2 for b in ry))
    if vx == 0 or vy == 0:
        return 1.0 if rx == ry else None
    return cov / (vx * vy)


def ml5(spec: TableSpec, ref_rows: list[Row], tgt_rows: list[Row]) -> RuleResult:
    ref_by = {key_of(r, spec.keys): to_float(r.get("pd")) for r in ref_rows}
    tgt_by = {key_of(r, spec.keys): to_float(r.get("pd")) for r in tgt_rows}
    shared = [k for k in ref_by if k in tgt_by and ref_by[k] is not None and tgt_by[k] is not None]
    rho = spearman([ref_by[k] for k in shared], [tgt_by[k] for k in shared])
    ok = rho is not None and abs(rho - 1.0) < 1e-12
    return RuleResult(
        "ML-5", spec.name, "pd", "PASS" if ok else "FAIL", 1.0, rho,
        f"Spearman rho over {len(shared)} scored accounts (ties allowed)",
    )


def ml7(spec: TableSpec, tgt_rows: list[Row]) -> RuleResult:
    edge_cases = []
    for r in tgt_rows:
        p = to_float(r.get("pd"))
        if p is None:
            continue
        for e in RATING_EDGES:
            if abs(p - e) <= EDGE_EPS:
                edge_cases.append([list(key_of(r, spec.keys)), p, e])
    return RuleResult(
        "ML-7", spec.name, "pd", "INFO", None, len(edge_cases),
        "accounts whose PD lies within 1e-9 of a rating edge (listed, none expected on seed)",
        edge_cases[:MAX_EXAMPLES],
    )


def ml8(
    spec: TableSpec, any_ml_fail: bool, ref_debug: list[Row] | None, tgt_debug: list[Row] | None
) -> RuleResult:
    if not any_ml_fail:
        return RuleResult(
            "ML-8", spec.name, "woe_*", "NOT_APPLICABLE", None, None,
            "feature parity check runs only when an ML-1..ML-6 row fails",
        )
    if ref_debug is None or tgt_debug is None:
        return RuleResult(
            "ML-8", spec.name, "woe_*", "FAIL", None, None,
            f"ML row failed and {spec.woe_debug} is missing on "
            f"{'reference' if ref_debug is None else 'target'} side",
        )
    cols = [c for c in (ref_debug[0].keys() if ref_debug else []) if c.startswith("woe_")]
    ref_by = {key_of(r, spec.keys): r for r in ref_debug}
    tgt_by = {key_of(r, spec.keys): r for r in tgt_debug}
    mism = []
    for k in set(ref_by) & set(tgt_by):
        for c in cols:
            a, b = to_float(ref_by[k].get(c)), to_float(tgt_by[k].get(c))
            if a is None or b is None or abs(a - b) > 1e-9:
                mism.append([list(k), c, ref_by[k].get(c), tgt_by[k].get(c)])
    return RuleResult(
        "ML-8", spec.name, "woe_*", "PASS" if not mism else "FAIL", None, None,
        f"woe columns={len(cols)} mismatches={len(mism)}", mism[:MAX_EXAMPLES],
    )


# ---------------------------------------------------------------- T-10..T-12


def t10(spec: TableSpec) -> RuleResult:
    how = "full-row multiset" if spec.multiset else f"sets keyed on ({', '.join(spec.keys)})"
    return RuleResult(
        "T-10", spec.name, None, "PASS", None, None,
        f"compared as {how}; no ordering asserted",
    )


def t11(spec: TableSpec) -> RuleResult:
    return RuleResult(
        "T-11", spec.name, None, "INFO", None, None,
        "rounding rule (ROUND HALF_UP, AVG untruncated) is a converted-code rule; "
        "its effect is judged by the T-4/T-5 row rules above",
    )


def t12(spec: TableSpec, xlsx_path: str | None) -> RuleResult:
    if not spec.xlsx:
        return RuleResult("T-12", spec.name, None, "NOT_APPLICABLE", None, None, "no workbook")
    if not xlsx_path:
        return RuleResult(
            "T-12", spec.name, None, "NOT_APPLICABLE", None, None,
            "workbook not reconciled (T-12); pass --xlsx-path to assert existence + 4 sheets",
        )
    try:
        import openpyxl

        wb = openpyxl.load_workbook(xlsx_path, read_only=True)
        expected = list(spec.xlsx_sheets) if spec.xlsx_sheets else 4
        actual = wb.sheetnames
        return RuleResult(
            "T-12", spec.name, None, "PASS" if actual == expected else "FAIL", expected, actual,
            f"workbook exists; sheets={actual}",
        )
    except Exception as exc:  # noqa: BLE001 - any load failure is a FAIL with the reason
        return RuleResult("T-12", spec.name, None, "FAIL", 4, None, f"workbook unreadable: {exc}")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None).isoformat() + "Z"
