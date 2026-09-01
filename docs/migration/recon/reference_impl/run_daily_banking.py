"""Literal re-expression of BatchJobs/run_daily_banking.sas
(%run_daily_banking(run_date=&CURR_DT, restart_from=)).

Runs the four steps in dependency order (lines 121-131) and returns every
persisted table plus the 4 WORK.BATCH_CONTROL rows appended to
ARCHIVE.BATCH_HISTORY (line 142). Notifications (%send_notification) and the
PROC PRINT (lines 135-139) have no table effect and are not reproduced.
"""
from __future__ import annotations

import datetime as dt
from typing import Dict, List

from . import (
    credit_risk_scoring,
    daily_transaction_processing,
    load_customer_accounts,
    monthly_regulatory_reporting,
)
from . import sas_semantics as S
from .seeds import Row

SENTINEL_TS = "2024-01-31T00:00:00"
SENTINEL_DURATION = 0.0
PROGRAM_ROOT = "/opt/sas/custom/programs/Banking"

STEPS = [  # lines 121-131
    (1, "Load Customer Accounts", "load_customer_accounts.sas"),
    (2, "Daily Transaction Processing", "daily_transaction_processing.sas"),
    (3, "Credit Risk Scoring", "credit_risk_scoring.sas"),
    (4, "Monthly Regulatory Reporting", "monthly_regulatory_reporting.sas"),
]


def batch_id(run_date: dt.date) -> str:
    """line 16: BANK_<yymmddn8>_<B8601DT of datetime()>; the wall-clock part is
    replaced by the fixed reference sentinel 000000 (see AMBIGUITIES AMB-10)."""
    return f"BANK_{S.yymmddn8(run_date)}_000000"


def run(libs: Dict[str, List[Row]], run_date: dt.date, report_month: str) -> Dict[str, List[Row]]:
    out: Dict[str, List[Row]] = {}
    bid = batch_id(run_date)

    # Step 1 (line 121): %let CURR_DT = &run_date -> run_date=&CURR_DT
    out.update(load_customer_accounts.run(libs, run_date))
    daily = out["STG_BANK.CUST_ACCOUNTS_DAILY"]
    # Step 2 (line 124): txn_date=&CURR_DT
    out.update(daily_transaction_processing.run(libs, daily, run_date))
    # Step 3 (line 127): score_date=&CURR_DT
    out.update(credit_risk_scoring.run(libs, daily, run_date))
    # Step 4 (line 130): report_month=&PREV_YM (autoexec_local: 202401)
    out.update(monthly_regulatory_reporting.run(libs, daily, report_month))

    # lines 80-91: one WORK.BATCH_CONTROL row per step, all PASS in the reference run
    out["ARCHIVE.BATCH_HISTORY"] = [
        {"BATCH_ID": bid, "STEP_NUM": float(n), "STEP_NAME": name,
         "PROGRAM_PATH": f"{PROGRAM_ROOT}/{prog}", "STATUS": "PASS",
         "START_TIME": SENTINEL_TS, "END_TIME": SENTINEL_TS,
         "DURATION": SENTINEL_DURATION, "ERROR_MSG": ""}
        for n, name, prog in STEPS]
    return out
