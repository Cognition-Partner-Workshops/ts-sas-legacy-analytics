"""Seed readers: one function per library.table, typed exactly as
``Data/load_seed_data.sas`` reads them (DATE9. informats, numeric vs $).

Rows are plain dicts (SAS PDV style): numeric missing = None, char = ''.
``RAW_BANK.DAILY_RATES`` is declared by the legacy autoexec but never read by
any banking program, so it has no reader here (checksum-only in the manifest).
"""
from __future__ import annotations

import csv
import hashlib
import os
from typing import Callable, Dict, List

from .sas_semantics import date9, num

Row = Dict[str, object]

SEED_FILES = {
    "CURATED.DAILY_TRANSACTIONS": "curated/DAILY_TRANSACTIONS.csv",
    "ORA_DW.BUREAU_SCORES": "oracle_dw/BUREAU_SCORES.csv",
    "ORA_DW.COLLATERAL": "oracle_dw/COLLATERAL.csv",
    "ORA_DW.CUST_ACCOUNTS": "oracle_dw/CUST_ACCOUNTS.csv",
    "ORA_DW.CUST_DEMOGRAPHICS": "oracle_dw/CUST_DEMOGRAPHICS.csv",
    "ORA_DW.LOAN_DETAILS": "oracle_dw/LOAN_DETAILS.csv",
    "ORA_DW.PAYMENT_HISTORY": "oracle_dw/PAYMENT_HISTORY.csv",
    "RAW_BANK.DAILY_RATES": "raw_bank/DAILY_RATES.csv",
    "RAW_BANK.TXN_FEED_20240131": "raw_bank/TXN_FEED_20240131.csv",
}

CHAR: Callable[[str], object] = lambda s: s.strip()


def _read(path: str, types: Dict[str, Callable[[str], object]]) -> List[Row]:
    with open(path, newline="", encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        assert rdr.fieldnames == list(types), (path, rdr.fieldnames)
        return [{c: types[c](r[c]) for c in types} for r in rdr]


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


TXN_TYPES = {  # load_seed_data.sas:111-121 (feed and curated history share it)
    "TRANSACTION_ID": CHAR, "ACCOUNT_ID": CHAR, "TRANSACTION_DATE": date9,
    "TRANSACTION_TYPE": CHAR, "TRANSACTION_AMOUNT": num, "CHANNEL": CHAR,
    "MERCHANT_CATEGORY": CHAR, "DESCRIPTION": CHAR, "POST_DATE": date9,
    "CURRENCY_CODE": CHAR,
}


def load_all(csv_root: str) -> Dict[str, List[Row]]:
    p = lambda k: os.path.join(csv_root, SEED_FILES[k])
    return {
        # load_seed_data.sas:25-36
        "ORA_DW.CUST_DEMOGRAPHICS": _read(p("ORA_DW.CUST_DEMOGRAPHICS"), {
            "CUSTOMER_ID": CHAR, "FIRST_NAME": CHAR, "LAST_NAME": CHAR,
            "SSN_HASH": CHAR, "DATE_OF_BIRTH": date9, "CUSTOMER_SEGMENT": CHAR,
            "RISK_RATING": num, "REGION_CODE": CHAR, "PRIMARY_EMAIL": CHAR,
            "PHONE_NUMBER": CHAR}),
        # load_seed_data.sas:41-54
        "ORA_DW.CUST_ACCOUNTS": _read(p("ORA_DW.CUST_ACCOUNTS"), {
            "ACCOUNT_ID": CHAR, "CUSTOMER_ID": CHAR, "ACCOUNT_TYPE": CHAR,
            "ACCOUNT_STATUS": CHAR, "OPEN_DATE": date9, "CLOSE_DATE": date9,
            "CURRENT_BALANCE": num, "AVAILABLE_BALANCE": num, "CREDIT_LIMIT": num,
            "INTEREST_RATE": num, "BRANCH_ID": CHAR, "OFFICER_ID": CHAR,
            "LAST_ACTIVITY_DATE": date9}),
        # load_seed_data.sas:58-67
        "ORA_DW.BUREAU_SCORES": _read(p("ORA_DW.BUREAU_SCORES"), {
            "CUSTOMER_ID": CHAR, "SCORE_DATE": date9, "FICO_SCORE": num,
            "VANTAGE_SCORE": num, "BUREAU_INQS_6MO": num, "BUREAU_TRADES_OPEN": num,
            "BUREAU_DEROGS": num, "BUREAU_UTIL_PCT": num, "BUREAU_OLDEST_TRADE_MO": num}),
        # load_seed_data.sas:71-79
        "ORA_DW.PAYMENT_HISTORY": _read(p("ORA_DW.PAYMENT_HISTORY"), {
            "ACCOUNT_ID": CHAR, "PMT_ONTIME_12MO": num, "PMT_LATE_30_12MO": num,
            "PMT_LATE_60_12MO": num, "PMT_LATE_90_12MO": num,
            "MAX_DAYS_PAST_DUE_EVER": num, "MONTHS_SINCE_LAST_DPD": num,
            "AVG_PMT_RATIO_12MO": num}),
        # load_seed_data.sas:83-91
        "ORA_DW.COLLATERAL": _read(p("ORA_DW.COLLATERAL"), {
            "ACCOUNT_ID": CHAR, "COLLATERAL_VALUE": num, "LAST_APPRAISAL_DATE": date9}),
        # load_seed_data.sas:95-105
        "ORA_DW.LOAN_DETAILS": _read(p("ORA_DW.LOAN_DETAILS"), {
            "ACCOUNT_ID": CHAR, "LOAN_PURPOSE": CHAR, "ORIG_AMOUNT": num,
            "ORIG_DATE": date9, "TERM_MONTHS": num, "LTV": num,
            "DAYS_PAST_DUE": num, "PAST_DUE_AMOUNT": num, "ALLOWANCE_AMT": num}),
        "RAW_BANK.TXN_FEED_20240131": _read(p("RAW_BANK.TXN_FEED_20240131"), TXN_TYPES),
        "CURATED.DAILY_TRANSACTIONS": _read(p("CURATED.DAILY_TRANSACTIONS"), TXN_TYPES),
    }
