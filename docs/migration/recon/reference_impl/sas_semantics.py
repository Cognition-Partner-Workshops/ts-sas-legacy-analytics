"""Base SAS value semantics used by the reference implementation.

Numeric missing is represented as ``None``; character missing is ``''``.
Every helper mirrors the Base SAS 9.4 rule it is named after so the program
modules can stay a statement-by-statement transcription of the SAS source.
"""
from __future__ import annotations

import datetime as dt
import math
from typing import Iterable, Optional

Num = Optional[float]

MONTHS = {m: i for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], start=1)}


# ----------------------------------------------------------------------------
# Missing values
# ----------------------------------------------------------------------------
def missing(x) -> bool:
    """SAS MISSING(): numeric None/NaN or blank character."""
    if x is None:
        return True
    if isinstance(x, str):
        return x.strip() == ""
    if isinstance(x, float) and math.isnan(x):
        return True
    return False


def num(s: str) -> Num:
    """Numeric informat read of a CSV field (blank -> missing)."""
    s = s.strip()
    return None if s == "" else float(s)


def date9(s: str) -> Optional[dt.date]:
    """DATE9. informat (ddMONyyyy); blank -> missing."""
    s = s.strip()
    if s == "":
        return None
    return dt.date(int(s[5:9]), MONTHS[s[2:5].upper()], int(s[0:2]))


# ----------------------------------------------------------------------------
# Arithmetic: any missing operand propagates missing
# ----------------------------------------------------------------------------
def add(a: Num, b: Num) -> Num:
    return None if a is None or b is None else a + b


def sub(a: Num, b: Num) -> Num:
    return None if a is None or b is None else a - b


def mul(a: Num, b: Num) -> Num:
    return None if a is None or b is None else a * b


def div(a: Num, b: Num) -> Num:
    """SAS division: missing if either operand missing or divisor 0 (SAS
    prints a note and yields missing on division by zero)."""
    if a is None or b is None or b == 0:
        return None
    return a / b


def sas_abs(a: Num) -> Num:
    return None if a is None else abs(a)


def sas_exp(a: Num) -> Num:
    return None if a is None else math.exp(a)


def sas_max(*args: Num) -> Num:
    """SAS MAX(): ignores missing arguments; missing only if all are missing."""
    vals = [a for a in args if a is not None]
    return max(vals) if vals else None


def sas_min(*args: Num) -> Num:
    """SAS MIN(): ignores missing arguments; missing only if all are missing."""
    vals = [a for a in args if a is not None]
    return min(vals) if vals else None


# ----------------------------------------------------------------------------
# Comparisons: in DATA step / PROC SQL WHERE-CASE, a missing numeric compares
# as the lowest value (. < any number). So `. > x` is false, `. < x` is true,
# `. = .` is true. Callers that need the "missing -> false" reading of a
# strictly-numeric test use gt/ge/lt/le with `strict=True` semantics below.
# ----------------------------------------------------------------------------
def gt(a: Num, b: Num) -> bool:
    if a is None:
        return False            # . > b is never true
    if b is None:
        return True             # a > . is true for any non-missing a
    return a > b


def ge(a: Num, b: Num) -> bool:
    if a is None:
        return b is None        # . >= . is true
    if b is None:
        return True
    return a >= b


def lt(a: Num, b: Num) -> bool:
    return gt(b, a)


def le(a: Num, b: Num) -> bool:
    return ge(b, a)


def eq(a: Num, b: Num) -> bool:
    return a == b               # None == None -> True (. = .)


def between(a: Num, lo: float, hi: float) -> bool:
    """SQL BETWEEN with missing sorting low: missing is below any lo>=. so
    `. between 1 and 29` is false."""
    return ge(a, lo) and le(a, hi)


# ----------------------------------------------------------------------------
# Date functions
# ----------------------------------------------------------------------------
def intck_month(start: Optional[dt.date], end: Optional[dt.date]) -> Num:
    """INTCK('month', start, end): number of month *boundaries* crossed."""
    if start is None or end is None:
        return None
    return float((end.year * 12 + end.month) - (start.year * 12 + start.month))


def intnx_day(d: dt.date, n: int) -> dt.date:
    return d + dt.timedelta(days=n)


def intnx_month_end(d: dt.date) -> dt.date:
    """INTNX('month', d, 0, 'E')."""
    nxt = dt.date(d.year + (d.month // 12), d.month % 12 + 1, 1)
    return nxt - dt.timedelta(days=1)


def date_diff_days(a: Optional[dt.date], b: Optional[dt.date]) -> Num:
    """SAS date subtraction (dates are day counts)."""
    if a is None or b is None:
        return None
    return float((a - b).days)


def yymmddn8(d: dt.date) -> str:
    return d.strftime("%Y%m%d")


def date9_put(d: Optional[dt.date]) -> str:
    """PUT(d, DATE9.)"""
    if d is None:
        return "."
    return d.strftime("%d%b%Y").upper()


# ----------------------------------------------------------------------------
# Numeric formats used inside CATX() calls
# ----------------------------------------------------------------------------
def put_dollar(x: Num, w: int = 18, d: int = 2) -> str:
    """PUT(x, DOLLARw.d): '$1,234.56', negative '-$1,234.56', missing '.'.
    Result is right-aligned to width w (CATX strips the padding anyway)."""
    if x is None:
        return ".".rjust(w)
    sign = "-" if x < 0 else ""
    body = f"{abs(x):,.{d}f}"
    s = f"{sign}${body}"
    if len(s) > w:              # SAS drops separators, then decimals, to fit
        s = f"{sign}${abs(x):.{d}f}"
        if len(s) > w:
            s = f"{sign}${abs(x):.0f}"
    return s.rjust(w)


def put_wd(x: Num, w: int = 5, d: int = 1) -> str:
    """PUT(x, w.d): right-aligned, decimals dropped if the value cannot fit."""
    if x is None:
        return ".".rjust(w)
    s = f"{x:.{d}f}"
    dd = d
    while len(s) > w and dd > 0:
        dd -= 1
        s = f"{x:.{dd}f}"
    return s.rjust(w)


def parmv(value: str, case: str = "U") -> str:
    """%parmv(_CASE=) value conversion (Macro/parmv.sas:147, 204-215): the
    default _CASE=U upper-cases the parameter value at macro entry; L lowers;
    N leaves it unchanged."""
    case = case.upper()
    if case == "U":
        return value.upper()
    if case == "L":
        return value.lower()
    return value


def catx(sep: str, *parts: str) -> str:
    """CATX(): strips leading/trailing blanks, drops blank items."""
    return sep.join(p.strip() for p in parts if p.strip() != "")


# ----------------------------------------------------------------------------
# Summary statistics (PROC SQL / PROC MEANS defaults): missing values are
# excluded; N counts non-missing; STD is the sample (n-1) standard deviation;
# sums accumulate sequentially in observation order.
# ----------------------------------------------------------------------------
def sas_sum(values: Iterable[Num]) -> Num:
    total: Num = None
    for v in values:
        if v is None:
            continue
        total = v if total is None else total + v
    return total


def sas_n(values: Iterable[Num]) -> int:
    return sum(1 for v in values if v is not None)


def sas_mean(values: Iterable[Num]) -> Num:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return sas_sum(vals) / len(vals)


def sas_std(values: Iterable[Num]) -> Num:
    vals = [v for v in values if v is not None]
    n = len(vals)
    if n < 2:
        return None
    m = sas_sum(vals) / n
    ss = sas_sum([(v - m) ** 2 for v in vals])
    return math.sqrt(ss / (n - 1))
