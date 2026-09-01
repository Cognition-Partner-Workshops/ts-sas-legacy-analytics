"""Literal re-expression of Programs/Banking/credit_risk_scoring.sas
(%credit_risk_scoring(score_date=&CURR_DT, model_id=CRM-2023-Q4-v2)).

Outputs: CURATED.RISK_SCORES, CURATED.RISK_MIGRATION, REPORTS.RISK_SUMMARY.
Line numbers refer to the SAS file.
"""
from __future__ import annotations

import datetime as dt
from typing import Dict, List, Optional

from . import sas_semantics as S
from .seeds import Row

SENTINEL_TS = "2024-01-31T00:00:00"
MODEL_ID = "CRM-2023-Q4-v2"                                                  # line 18 default
SCORED_TYPES = ("MTG", "AUTO", "PERS", "CC", "LOC", "HELC")                  # line 84
WOE_COLS = ["INTERCEPT", "WOE_FICO", "WOE_UTIL", "WOE_DPD", "WOE_AGE", "WOE_LTV", "LOG_ODDS"]  # line 196


def score_input(libs: Dict[str, List[Row]], daily_accounts: List[Row], score_date: dt.date) -> List[Row]:
    """PROC SQL lines 32-86."""
    bureau = libs["ORA_DW.BUREAU_SCORES"]
    # lines 76-78: correlated subquery -> latest SCORE_DATE <= score_date per customer
    latest: Dict[str, Optional[dt.date]] = {}
    for b in bureau:
        if b["SCORE_DATE"] is not None and b["SCORE_DATE"] <= score_date:
            cur = latest.get(b["CUSTOMER_ID"])
            if cur is None or b["SCORE_DATE"] > cur:
                latest[b["CUSTOMER_ID"]] = b["SCORE_DATE"]
    bureau_rows: Dict[str, List[Row]] = {}
    for b in bureau:
        if latest.get(b["CUSTOMER_ID"]) is not None and b["SCORE_DATE"] == latest[b["CUSTOMER_ID"]]:
            bureau_rows.setdefault(b["CUSTOMER_ID"], []).append(b)
    pay = {p["ACCOUNT_ID"]: p for p in libs["ORA_DW.PAYMENT_HISTORY"]}       # unique ACCOUNT_ID
    col = {c["ACCOUNT_ID"]: c for c in libs["ORA_DW.COLLATERAL"]}           # unique ACCOUNT_ID

    b_cols = ["FICO_SCORE", "VANTAGE_SCORE", "BUREAU_INQS_6MO", "BUREAU_TRADES_OPEN",
              "BUREAU_DEROGS", "BUREAU_UTIL_PCT", "BUREAU_OLDEST_TRADE_MO"]  # lines 47-53
    p_cols = ["PMT_ONTIME_12MO", "PMT_LATE_30_12MO", "PMT_LATE_60_12MO", "PMT_LATE_90_12MO",
              "MAX_DAYS_PAST_DUE_EVER", "MONTHS_SINCE_LAST_DPD", "AVG_PMT_RATIO_12MO"]  # lines 56-62
    out: List[Row] = []
    for a in daily_accounts:
        if not (a["SNAPSHOT_DATE"] == score_date and a["ACCOUNT_TYPE"] in SCORED_TYPES):  # lines 83-84
            continue
        # left join fan-out if a customer had >1 bureau rows on the max date (none in seed)
        for b in bureau_rows.get(a["CUSTOMER_ID"], [None]):
            r: Row = {c: a[c] for c in ("ACCOUNT_ID", "CUSTOMER_ID", "ACCOUNT_TYPE", "CURRENT_BALANCE",
                                        "CREDIT_LIMIT", "ACCT_AGE_MONTHS", "DAYS_INACTIVE",
                                        "UTILIZATION_PCT", "CUSTOMER_SEGMENT", "REGION_CODE")}  # lines 35-44
            r.update({c: (b[c] if b else None) for c in b_cols})
            p = pay.get(a["ACCOUNT_ID"])                                    # lines 79-80
            r.update({c: (p[c] if p else None) for c in p_cols})
            c = col.get(a["ACCOUNT_ID"])                                    # lines 81-82
            r["COLLATERAL_VALUE"] = c["COLLATERAL_VALUE"] if c else None
            r["LAST_APPRAISAL_DATE"] = c["LAST_APPRAISAL_DATE"] if c else None
            if S.gt(r["COLLATERAL_VALUE"], 0):                              # lines 67-71
                r["LTV"] = S.div(a["CURRENT_BALANCE"], r["COLLATERAL_VALUE"])
            else:
                r["LTV"] = None
            out.append(r)
    return out


def scorecard(inputs: List[Row], score_date: dt.date) -> List[Row]:
    """DATA step lines 92-197. WOE_* / LOG_ODDS are kept on the returned rows
    (ML-8 debug); callers drop WOE_COLS for the persisted table (line 196)."""
    out: List[Row] = []
    for src in inputs:
        r = dict(src)                                                       # line 93
        r["INTERCEPT"] = -3.2145                                            # line 96

        f = r["FICO_SCORE"]                                                 # lines 99-107
        if not S.missing(f):
            if f >= 760: r["WOE_FICO"] = -1.204
            elif f >= 720: r["WOE_FICO"] = -0.812
            elif f >= 680: r["WOE_FICO"] = -0.356
            elif f >= 640: r["WOE_FICO"] = 0.198
            elif f >= 600: r["WOE_FICO"] = 0.654
            else: r["WOE_FICO"] = 1.102
        else:
            r["WOE_FICO"] = 0.198

        u = r["UTILIZATION_PCT"]                                            # lines 110-118
        if not S.missing(u):
            if u <= 10: r["WOE_UTIL"] = -0.956
            elif u <= 30: r["WOE_UTIL"] = -0.521
            elif u <= 50: r["WOE_UTIL"] = -0.102
            elif u <= 70: r["WOE_UTIL"] = 0.334
            elif u <= 90: r["WOE_UTIL"] = 0.789
            else: r["WOE_UTIL"] = 1.245
        else:
            r["WOE_UTIL"] = 0.0

        d = r["PMT_LATE_90_12MO"]                                           # lines 121-126
        if not S.missing(d):
            if d == 0: r["WOE_DPD"] = -0.678
            elif d == 1: r["WOE_DPD"] = 0.445
            else: r["WOE_DPD"] = 1.567
        else:
            r["WOE_DPD"] = 0.0

        g = r["ACCT_AGE_MONTHS"]                                            # lines 129-135
        if not S.missing(g):
            if g >= 120: r["WOE_AGE"] = -0.534
            elif g >= 60: r["WOE_AGE"] = -0.289
            elif g >= 24: r["WOE_AGE"] = 0.045
            else: r["WOE_AGE"] = 0.456
        else:
            r["WOE_AGE"] = 0.0

        ltv = r["LTV"]                                                      # lines 138-147
        if r["ACCOUNT_TYPE"] in ("MTG", "AUTO", "HELC"):
            if not S.missing(ltv):
                if ltv <= 0.60: r["WOE_LTV"] = -0.712
                elif ltv <= 0.80: r["WOE_LTV"] = -0.234
                elif ltv <= 1.00: r["WOE_LTV"] = 0.356
                else: r["WOE_LTV"] = 0.889
            else:
                r["WOE_LTV"] = 0.0
        else:
            r["WOE_LTV"] = 0.0

        # lines 150-155 (left-to-right accumulation, as SAS evaluates it)
        r["LOG_ODDS"] = (r["INTERCEPT"]
                         + 0.412 * r["WOE_FICO"]
                         + 0.198 * r["WOE_UTIL"]
                         + 0.289 * r["WOE_DPD"]
                         + 0.067 * r["WOE_AGE"]
                         + 0.134 * r["WOE_LTV"])
        r["PD"] = 1 / (1 + S.sas_exp(-r["LOG_ODDS"]))                       # line 157

        if r["ACCOUNT_TYPE"] in ("MTG", "AUTO", "HELC"):                    # lines 161-168
            if not S.missing(ltv):
                r["LGD"] = S.sas_max(0, S.sas_min(1, (ltv - 0.5) * 0.8))
            else:
                r["LGD"] = 0.40
        elif r["ACCOUNT_TYPE"] == "CC":
            r["LGD"] = 0.75
        else:
            r["LGD"] = 0.50

        if r["ACCOUNT_TYPE"] in ("CC", "LOC", "HELC"):                      # lines 172-175
            r["EAD"] = S.add(r["CURRENT_BALANCE"], S.mul(0.50, S.sub(r["CREDIT_LIMIT"], r["CURRENT_BALANCE"])))
        else:
            r["EAD"] = r["CURRENT_BALANCE"]

        r["EXPECTED_LOSS"] = S.mul(S.mul(r["PD"], r["LGD"]), r["EAD"])      # line 179

        pd_ = r["PD"]                                                       # lines 183-189
        if S.lt(pd_, 0.005): r["NEW_RISK_RATING"] = 1.0
        elif S.lt(pd_, 0.01): r["NEW_RISK_RATING"] = 2.0
        elif S.lt(pd_, 0.03): r["NEW_RISK_RATING"] = 3.0
        elif S.lt(pd_, 0.07): r["NEW_RISK_RATING"] = 4.0
        elif S.lt(pd_, 0.15): r["NEW_RISK_RATING"] = 5.0
        elif S.lt(pd_, 0.30): r["NEW_RISK_RATING"] = 6.0
        else: r["NEW_RISK_RATING"] = 7.0

        r["SCORE_DATE"] = score_date                                        # line 191
        r["MODEL_ID"] = MODEL_ID                                            # line 192
        r["SCORE_TIMESTAMP"] = SENTINEL_TS                                  # line 193 datetime() -> sentinel
        out.append(r)
    return out


def risk_migration(scored: List[Row], daily_accounts: List[Row], score_date: dt.date) -> List[Row]:
    """PROC SQL lines 202-224."""
    acct = {a["ACCOUNT_ID"]: a for a in daily_accounts}
    out: List[Row] = []
    for s in scored:
        a = acct.get(s["ACCOUNT_ID"])                                       # lines 218-219 inner join
        if a is None or a["SNAPSHOT_DATE"] != score_date:                   # line 220
            continue
        prev, new = a["RISK_RATING"], s["NEW_RISK_RATING"]
        if not (prev != new or prev is None):                               # lines 221-222 (. ne x is true in SAS SQL)
            continue
        if prev is None: direction = "NEW"                                  # lines 209-214
        elif S.lt(new, prev): direction = "UPGRADE"
        elif S.gt(new, prev): direction = "DOWNGRADE"
        else: direction = "STABLE"
        out.append({"SCORE_DATE": score_date, "ACCOUNT_ID": a["ACCOUNT_ID"],
                    "PREV_RATING": prev, "CURR_RATING": new,
                    "MIGRATION_DIRECTION": direction, "PD": s["PD"],
                    "EXPECTED_LOSS": s["EXPECTED_LOSS"]})                   # lines 205-216
    return out


def risk_summary(scored: List[Row]) -> List[Row]:
    """PROC MEANS lines 246-256 (NWAY; class levels with missing values are
    excluded by default; N = non-missing count of the first VAR, PD)."""
    groups: Dict[tuple, List[Row]] = {}
    for s in scored:
        if S.missing(s["ACCOUNT_TYPE"]) or s["NEW_RISK_RATING"] is None:
            continue
        groups.setdefault((s["ACCOUNT_TYPE"], s["NEW_RISK_RATING"]), []).append(s)
    out: List[Row] = []
    for (atype, rating) in sorted(groups):                                  # class-variable order
        g = groups[(atype, rating)]
        out.append({"ACCOUNT_TYPE": atype, "NEW_RISK_RATING": rating,
                    "N_ACCOUNTS": float(S.sas_n(r["PD"] for r in g)),      # line 250
                    "AVG_PD": S.sas_mean(r["PD"] for r in g),               # line 251
                    "AVG_LGD": S.sas_mean(r["LGD"] for r in g),             # line 252
                    "TOTAL_EAD": S.sas_sum(r["EAD"] for r in g),            # line 253
                    "TOTAL_EL": S.sas_sum(r["EXPECTED_LOSS"] for r in g)})  # line 254
    return out


def run(libs: Dict[str, List[Row]], daily_accounts: List[Row], score_date: dt.date) -> Dict[str, List[Row]]:
    inp = score_input(libs, daily_accounts, score_date)
    scored_full = scorecard(inp, score_date)
    scored = [{k: v for k, v in r.items() if k not in WOE_COLS} for r in scored_full]  # line 196 drop
    return {"CURATED.RISK_SCORES": scored,                                  # lines 231-232 (base absent -> full structure)
            "CURATED.RISK_MIGRATION": risk_migration(scored, daily_accounts, score_date),
            "REPORTS.RISK_SUMMARY": risk_summary(scored),
            "ALT.RISK_SCORES_WOE_DEBUG": [{c: r[c] for c in ["ACCOUNT_ID", "SCORE_DATE"] + WOE_COLS + ["PD"]}
                                          for r in scored_full]}
