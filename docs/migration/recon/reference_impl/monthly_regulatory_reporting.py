"""Literal re-expression of Programs/Banking/monthly_regulatory_reporting.sas
(%monthly_regulatory_reporting(report_month=&PREV_YM), PREV_YM=202401).

Outputs: REPORTS.MONTHLY_RWA, DELINQUENCY_AGING, LLP_COVERAGE, CAPITAL_ADEQUACY.
The %export_xlsx workbook (lines 146-162) is out of the recon gate (T-12) and
is not produced. Line numbers refer to the SAS file.
"""
from __future__ import annotations

import datetime as dt
from typing import Dict, List, Optional

from . import sas_semantics as S
from .seeds import Row

LOAN_TYPES = ("MTG", "AUTO", "PERS", "CC", "LOC", "HELC")                   # lines 95, 138


def month_bounds(report_month: str):
    """lines 27-28: month_start = inputn(yyyymm01), month_end = intnx('month', start, 0, 'E')."""
    start = dt.date(int(report_month[:4]), int(report_month[4:6]), 1)
    return start, S.intnx_month_end(start)


def _joined(daily_accounts: List[Row], loans: List[Row], month_end: dt.date, inner: bool, types_only: bool):
    """Shared FROM/JOIN/WHERE of the four queries: accounts @ month_end (left|inner) join LOAN_DETAILS."""
    loan = {l["ACCOUNT_ID"]: l for l in loans}                              # ACCOUNT_ID unique (248)
    for a in daily_accounts:
        if a["SNAPSHOT_DATE"] != month_end:
            continue
        if types_only and a["ACCOUNT_TYPE"] not in LOAN_TYPES:
            continue
        l: Optional[Row] = loan.get(a["ACCOUNT_ID"])
        if inner and l is None:
            continue
        yield a, l


def monthly_rwa(daily_accounts: List[Row], loans: List[Row], report_month: str, month_end: dt.date) -> List[Row]:
    """PROC SQL lines 40-67. LTV is l.LTV (only LOAN_DETAILS carries LTV); an
    MTG row with missing LTV satisfies neither line 49 nor 50 and falls
    through to `else 1.00` (AMB-07)."""
    groups: Dict[tuple, List[tuple]] = {}
    for a, l in _joined(daily_accounts, loans, month_end, inner=False, types_only=False):  # lines 60-63
        t = a["ACCOUNT_TYPE"]
        ltv = l["LTV"] if l else None
        if t in ("CHK", "SAV", "MMA"): rw = 0.00                            # lines 46-56
        elif t == "CD": rw = 0.00
        elif t == "MTG" and S.le(ltv, 0.80): rw = 0.35
        elif t == "MTG" and S.gt(ltv, 0.80): rw = 0.50
        elif t == "HELC": rw = 0.50
        elif t in ("AUTO", "PERS"): rw = 0.75
        elif t == "CC": rw = 0.75
        elif t == "LOC": rw = 1.00
        else: rw = 1.00
        groups.setdefault((report_month, t, a["CUSTOMER_SEGMENT"], rw), []).append(
            (a["CURRENT_BALANCE"], S.mul(a["CURRENT_BALANCE"], rw)))         # line 59 row-wise product
    out: List[Row] = []
    for k in sorted(groups, key=lambda k: (k[1], k[2], k[3])):              # line 65 (+rw for determinism)
        g = groups[k]
        out.append({"REPORT_MONTH": k[0], "ACCOUNT_TYPE": k[1], "CUSTOMER_SEGMENT": k[2],
                    "RISK_WEIGHT": k[3],
                    "N_ACCOUNTS": float(len(g)),                            # line 57
                    "TOTAL_EXPOSURE": S.sas_sum(b for b, _ in g),           # line 58
                    "RWA": S.sas_sum(p for _, p in g)})                     # line 59
    return out


BUCKET_ORDER = {"Current": 0, "1-29": 1, "30-59": 2, "60-89": 3, "90-119": 4, "120-179": 5, "180+": 6}


def delinquency_aging(daily_accounts: List[Row], loans: List[Row], report_month: str, month_end: dt.date) -> List[Row]:
    """PROC SQL lines 72-109. Missing DAYS_PAST_DUE (no loan row) -> 'Unknown'."""
    groups: Dict[tuple, List[tuple]] = {}
    for a, l in _joined(daily_accounts, loans, month_end, inner=False, types_only=True):  # lines 91-95
        dpd = l["DAYS_PAST_DUE"] if l else None
        if S.eq(dpd, 0) and dpd is not None: b = "Current"                  # lines 78-87
        elif S.between(dpd, 1, 29): b = "1-29"
        elif S.between(dpd, 30, 59): b = "30-59"
        elif S.between(dpd, 60, 89): b = "60-89"
        elif S.between(dpd, 90, 119): b = "90-119"
        elif S.between(dpd, 120, 179): b = "120-179"
        elif S.ge(dpd, 180) and dpd is not None: b = "180+"
        else: b = "Unknown"
        groups.setdefault((report_month, a["ACCOUNT_TYPE"], a["REGION_CODE"], b), []).append(
            (a["CURRENT_BALANCE"], l["PAST_DUE_AMOUNT"] if l else None))
    out: List[Row] = []
    for k in sorted(groups, key=lambda k: (k[1], k[2], BUCKET_ORDER.get(k[3], 7))):  # lines 97-107
        g = groups[k]
        out.append({"REPORT_MONTH": k[0], "ACCOUNT_TYPE": k[1], "REGION_CODE": k[2], "DELINQ_BUCKET": k[3],
                    "N_ACCOUNTS": float(len(g)),                            # line 88
                    "TOTAL_BALANCE": S.sas_sum(b for b, _ in g),            # line 89
                    "TOTAL_PAST_DUE": S.sas_sum(p for _, p in g)})          # line 90
    return out


def llp_coverage(daily_accounts: List[Row], loans: List[Row], report_month: str, month_end: dt.date) -> List[Row]:
    """PROC SQL lines 114-141 (inner join)."""
    groups: Dict[tuple, List[tuple]] = {}
    for a, l in _joined(daily_accounts, loans, month_end, inner=True, types_only=True):  # lines 134-138
        groups.setdefault((report_month, a["ACCOUNT_TYPE"]), []).append((a, l))
    out: List[Row] = []
    for k in sorted(groups):                                                # no ORDER BY; group order
        g = groups[k]
        gross = S.sas_sum(a["CURRENT_BALANCE"] for a, _ in g)               # line 120
        allow = S.sas_sum(l["ALLOWANCE_AMT"] for _, l in g)                 # line 121
        if S.gt(gross, 0):                                                  # lines 122-126
            cov = S.mul(S.div(allow, gross), 100)
        else:
            cov = 0.0
        npl = S.sas_sum((a["CURRENT_BALANCE"] if S.ge(l["DAYS_PAST_DUE"], 90) and l["DAYS_PAST_DUE"] is not None
                         else 0.0) for a, l in g)                           # lines 127-128
        if S.gt(npl, 0):                                                    # lines 129-133
            npl_cov = S.mul(S.div(allow, npl), 100)
        else:
            npl_cov = 0.0
        out.append({"REPORT_MONTH": k[0], "ACCOUNT_TYPE": k[1], "N_LOANS": float(len(g)),
                    "GROSS_LOANS": gross, "TOTAL_ALLOWANCE": allow, "COVERAGE_PCT": cov,
                    "NPL_BALANCE": npl, "NPL_COVERAGE_PCT": npl_cov})
    return out


def capital_adequacy(rwa_rows: List[Row], report_month: str) -> List[Row]:
    """PROC SQL lines 169-190: single summary row over REPORTS.MONTHLY_RWA."""
    total = S.sas_sum(r["RWA"] for r in rwa_rows)                           # line 173
    ratio = lambda cap: S.mul(S.div(cap, total), 100) if S.gt(total, 0) else None  # lines 178-180
    status = lambda cap, mn: ("PASS" if S.eq(total, 0) else                 # lines 182-187
                              ("PASS" if S.ge(S.mul(S.div(cap, total), 100), mn) else "FAIL"))
    return [{"REPORT_MONTH": report_month, "TOTAL_RWA": total,
             "CET1_CAPITAL": 50000000.0, "TIER1_CAPITAL": 65000000.0, "TOTAL_CAPITAL": 80000000.0,
             "CET1_RATIO": ratio(50000000.0), "TIER1_RATIO": ratio(65000000.0),
             "TOTAL_CAPITAL_RATIO": ratio(80000000.0),
             "CET1_STATUS": status(50000000.0, 4.5), "TIER1_STATUS": status(65000000.0, 6.0),
             "TOTAL_CAPITAL_STATUS": status(80000000.0, 8.0)}]


def run(libs: Dict[str, List[Row]], daily_accounts: List[Row], report_month: str) -> Dict[str, List[Row]]:
    _, month_end = month_bounds(report_month)
    loans = libs["ORA_DW.LOAN_DETAILS"]
    rwa = monthly_rwa(daily_accounts, loans, report_month, month_end)
    return {"REPORTS.MONTHLY_RWA": rwa,
            "REPORTS.DELINQUENCY_AGING": delinquency_aging(daily_accounts, loans, report_month, month_end),
            "REPORTS.LLP_COVERAGE": llp_coverage(daily_accounts, loans, report_month, month_end),
            "REPORTS.CAPITAL_ADEQUACY": capital_adequacy(rwa, report_month)}
