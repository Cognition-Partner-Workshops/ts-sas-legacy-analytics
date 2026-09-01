"""Literal re-expression of Programs/Banking/load_customer_accounts.sas
(%load_customer_accounts(run_date=&CURR_DT, region=ALL)).

Outputs: STG_BANK.CUST_ACCOUNTS_DAILY and the WORK.ACCT_EXCEPTIONS rows that
line 168-169 inserts into STG_BANK.ACCT_EXCEPTIONS. Line numbers cited per
block refer to the SAS file.
"""
from __future__ import annotations

import datetime as dt
from typing import Dict, List, Tuple

from . import sas_semantics as S
from .seeds import Row

SENTINEL_TS = "2024-01-31T00:00:00"

ACCT_RAW_COLS = [  # lines 36-58, select list order
    "ACCOUNT_ID", "CUSTOMER_ID", "ACCOUNT_TYPE", "ACCOUNT_STATUS", "OPEN_DATE",
    "CLOSE_DATE", "CURRENT_BALANCE", "AVAILABLE_BALANCE", "CREDIT_LIMIT",
    "INTEREST_RATE", "BRANCH_ID", "OFFICER_ID", "LAST_ACTIVITY_DATE",
    "FIRST_NAME", "LAST_NAME", "SSN_HASH", "DATE_OF_BIRTH", "CUSTOMER_SEGMENT",
    "RISK_RATING", "REGION_CODE", "PRIMARY_EMAIL", "PHONE_NUMBER",
]


def acct_raw(libs: Dict[str, List[Row]], run_date: dt.date) -> List[Row]:
    """PROC SQL lines 34-69: inner join accounts x demographics, filter, order."""
    demo = {d["CUSTOMER_ID"]: d for d in libs["ORA_DW.CUST_DEMOGRAPHICS"]}  # key unique (250)
    out: List[Row] = []
    for a in libs["ORA_DW.CUST_ACCOUNTS"]:
        d = demo.get(a["CUSTOMER_ID"])                                      # lines 60-61 inner join
        if d is None:
            continue
        if a["ACCOUNT_STATUS"] in ("W", "C"):                               # line 62
            continue
        if not S.le(_days(a["OPEN_DATE"]), _days(run_date)):                # line 63 (missing date -> false)
            continue
        r: Row = {c: a[c] for c in ACCT_RAW_COLS[:13]}
        r.update({c: d[c] for c in ACCT_RAW_COLS[13:]})
        out.append(r)
    out.sort(key=lambda r: (r["CUSTOMER_ID"], r["ACCOUNT_ID"]))             # line 67
    return out


def _days(d):
    return None if d is None else float(d.toordinal())


def data_step(acct_raw_rows: List[Row], run_date: dt.date) -> Tuple[List[Row], List[Row], List[Row]]:
    """DATA step lines 82-157 (two output data sets, one PDV).

    Returns (CUST_ACCOUNTS_DAILY, ACCT_EXCEPTIONS, ACCT_EXCEPTIONS-with-code). Per Base SAS the DROP
    statement on line 156 applies to *both* output data sets, so neither
    contains EXCEPTION_CODE/EXCEPTION_DESC (see AMBIGUITIES.md AMB-01). The
    exception rows are emitted before SNAPSHOT_DATE/LOAD_TIMESTAMP are
    assigned (lines 151-152), and those two variables are reset to missing at
    the top of every iteration (not retained, not from SET), so they are
    missing on every ACCT_EXCEPTIONS row.
    """
    daily: List[Row] = []
    exceptions: List[Row] = []
    for src in acct_raw_rows:
        pdv: Row = dict(src)                                                # line 85 set WORK.ACCT_RAW
        # Non-retained computed variables start each iteration as missing.
        pdv.update({"ACCT_AGE_MONTHS": None, "DAYS_INACTIVE": None,
                    "UTILIZATION_PCT": None, "DORMANCY_FLAG": "",
                    "HIGH_BALANCE_FLAG": "", "EXCEPTION_CODE": "",
                    "EXCEPTION_DESC": "", "SNAPSHOT_DATE": None,
                    "LOAD_TIMESTAMP": None})

        # lines 100-103
        pdv["ACCT_AGE_MONTHS"] = S.intck_month(pdv["OPEN_DATE"], run_date)
        pdv["DAYS_INACTIVE"] = S.date_diff_days(run_date, pdv["LAST_ACTIVITY_DATE"])

        # lines 106-109
        if pdv["ACCOUNT_TYPE"] in ("CC", "LOC", "HELC") and S.gt(pdv["CREDIT_LIMIT"], 0):
            pdv["UTILIZATION_PCT"] = S.mul(S.div(pdv["CURRENT_BALANCE"], pdv["CREDIT_LIMIT"]), 100)
        else:
            pdv["UTILIZATION_PCT"] = None

        # lines 112-115
        if S.gt(pdv["DAYS_INACTIVE"], 365) and pdv["ACCOUNT_STATUS"] == "A":
            pdv["DORMANCY_FLAG"] = "Y"
        else:
            pdv["DORMANCY_FLAG"] = "N"

        # lines 118-121
        if S.ge(pdv["CURRENT_BALANCE"], 250000):
            pdv["HIGH_BALANCE_FLAG"] = "Y"
        else:
            pdv["HIGH_BALANCE_FLAG"] = "N"

        # lines 124-130  NEG_BAL
        if pdv["ACCOUNT_TYPE"] in ("CHK", "SAV", "MMA", "CD") and S.lt(pdv["CURRENT_BALANCE"], 0):
            pdv["EXCEPTION_CODE"] = "NEG_BAL"
            pdv["EXCEPTION_DESC"] = S.catx(" ", "Negative balance",
                                           S.put_dollar(pdv["CURRENT_BALANCE"], 18, 2),
                                           "on deposit account", pdv["ACCOUNT_ID"])
            exceptions.append(dict(pdv))                                    # line 129 output

        # lines 133-139  HIGH_UTIL
        if S.gt(pdv["UTILIZATION_PCT"], 95):
            pdv["EXCEPTION_CODE"] = "HIGH_UTIL"
            pdv["EXCEPTION_DESC"] = S.catx(" ", "Utilization at",
                                           S.put_wd(pdv["UTILIZATION_PCT"], 5, 1), "%",
                                           "for account", pdv["ACCOUNT_ID"])
            exceptions.append(dict(pdv))                                    # line 138 output

        # lines 142-147  NO_RISK
        if S.eq(pdv["RISK_RATING"], None):
            pdv["EXCEPTION_CODE"] = "NO_RISK"
            pdv["EXCEPTION_DESC"] = S.catx(" ", "Missing risk rating for customer",
                                           pdv["CUSTOMER_ID"])
            exceptions.append(dict(pdv))                                    # line 146 output

        # lines 151-154
        pdv["SNAPSHOT_DATE"] = run_date
        pdv["LOAD_TIMESTAMP"] = SENTINEL_TS                                 # datetime() -> fixed sentinel
        daily.append(dict(pdv))

    # line 156: DROP applies to every output data set of the step. The
    # pre-DROP PDV rows are kept separately as the AMB-01 "intent" alternate.
    exceptions_literal = [{k: v for k, v in r.items() if k not in ("EXCEPTION_CODE", "EXCEPTION_DESC")}
                          for r in exceptions]
    for r in daily:
        del r["EXCEPTION_CODE"], r["EXCEPTION_DESC"]
    return daily, exceptions_literal, exceptions


def run(libs: Dict[str, List[Row]], run_date: dt.date) -> Dict[str, List[Row]]:
    raw = acct_raw(libs, run_date)
    daily, exceptions, exceptions_intent = data_step(raw, run_date)
    # lines 167-170: insert into STG_BANK.ACCT_EXCEPTIONS select * (only when nobs>0)
    # lines 188-198: WORK.ACCT_SUMMARY is WORK-only and deleted at line 209 -> not an output.
    return {"STG_BANK.CUST_ACCOUNTS_DAILY": daily,
            "STG_BANK.ACCT_EXCEPTIONS": exceptions,
            "ALT.ACCT_EXCEPTIONS_WITH_CODE": exceptions_intent}
