#!/usr/bin/env python3
"""Extract P1 banking output-table columns and transformation evidence.

The extractor intentionally reads only the requested legacy SAS programs,
autoexec configuration, and seeded CSV inputs.  It writes deterministic JSON
and Markdown evidence without changing any legacy source.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
TOOLS = REPO / ".migration" / "tools"
JSON_PATH = TOOLS / "p1_columns.json"
MARKDOWN_PATH = TOOLS / "p1_columns.md"

PROGRAMS = {
    "load_customer_accounts": REPO / "Programs/Banking/load_customer_accounts.sas",
    "daily_transaction_processing": REPO / "Programs/Banking/daily_transaction_processing.sas",
    "credit_risk_scoring": REPO / "Programs/Banking/credit_risk_scoring.sas",
    "monthly_regulatory_reporting": REPO / "Programs/Banking/monthly_regulatory_reporting.sas",
    "run_daily_banking": REPO / "BatchJobs/run_daily_banking.sas",
}
AUTOEXEC = REPO / "Config/autoexec.sas"
AUTOEXEC_LOCAL = REPO / "Config/autoexec_local.sas"


def rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


TEXT = {name: read(path) for name, path in PROGRAMS.items()}
LINES = {
    name: value.splitlines()
    for name, value in TEXT.items()
}


def line_of(program: str, needle: str, occurrence: int = 1) -> int:
    """Return the 1-based line containing needle, or UNKNOWN if absent."""
    seen = 0
    for number, line in enumerate(LINES[program], 1):
        if needle.lower() in line.lower():
            seen += 1
            if seen == occurrence:
                return number
    return -1


def cite(program: str, needle: str, occurrence: int = 1) -> str:
    number = line_of(program, needle, occurrence)
    return f"{rel(PROGRAMS[program])}:{number}" if number > 0 else "UNKNOWN"


def shorten(value: str, limit: int = 80) -> str:
    value = " ".join(value.strip().split())
    return value if len(value) <= limit else value[: limit - 3].rstrip() + "..."


def csv_evidence(source_table: str, column: str) -> dict[str, Any] | None:
    """Return header/sample evidence for a seeded source table column."""
    source_map = {
        "ORA_DW.CUST_ACCOUNTS": REPO / "Data/csv/oracle_dw/CUST_ACCOUNTS.csv",
        "ORA_DW.CUST_DEMOGRAPHICS": REPO / "Data/csv/oracle_dw/CUST_DEMOGRAPHICS.csv",
        "ORA_DW.BUREAU_SCORES": REPO / "Data/csv/oracle_dw/BUREAU_SCORES.csv",
        "ORA_DW.PAYMENT_HISTORY": REPO / "Data/csv/oracle_dw/PAYMENT_HISTORY.csv",
        "ORA_DW.COLLATERAL": REPO / "Data/csv/oracle_dw/COLLATERAL.csv",
        "ORA_DW.LOAN_DETAILS": REPO / "Data/csv/oracle_dw/LOAN_DETAILS.csv",
        "RAW_BANK.DAILY_RATES": REPO / "Data/csv/raw_bank/DAILY_RATES.csv",
        "RAW_BANK.TXN_FEED_20240131": REPO / "Data/csv/raw_bank/TXN_FEED_20240131.csv",
        "CURATED.DAILY_TRANSACTIONS": REPO / "Data/csv/curated/DAILY_TRANSACTIONS.csv",
    }
    path = source_map.get(source_table)
    if path is None or not path.exists():
        return None
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        row = next(reader, {})
    if column not in headers:
        return None
    return {
        "csv": rel(path),
        "column": column,
        "sample": row.get(column, ""),
    }


def column(
    name: str,
    expression: str,
    sas_type: str,
    format_applied: str | None,
    key: bool,
    citation: str,
    evidence: str,
    source_table: str | None = None,
    source_column: str | None = None,
    key_reason: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "name": name,
        "expression": shorten(expression),
        "sas_type": sas_type,
        "format": format_applied or None,
        "key": key,
        "cite": citation,
        "evidence": evidence,
    }
    if key_reason:
        item["key_reason"] = key_reason
    if source_table and source_column:
        item["source"] = f"{source_table}.{source_column}"
        csv_item = csv_evidence(source_table, source_column)
        if csv_item:
            item["csv_evidence"] = csv_item
    if note:
        item["note"] = note
    return item


def carried(
    name: str,
    source_table: str,
    source_column: str,
    program: str,
    needle: str,
    *,
    fmt: str | None = None,
    key: bool = False,
    key_reason: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    return column(
        name,
        f"{source_table}.{source_column}",
        f"carried from {source_table}.{source_column}",
        fmt,
        key,
        cite(program, needle),
        "INFERRED",
        source_table,
        source_column,
        key_reason,
        note,
    )


def fact(
    name: str,
    expression: str,
    sas_type: str,
    program: str,
    needle: str,
    *,
    fmt: str | None = None,
    key: bool = False,
    key_reason: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    return column(
        name,
        expression,
        sas_type,
        fmt,
        key,
        cite(program, needle),
        "FACT",
        key_reason=key_reason,
        note=note,
    )


def output_tables() -> list[dict[str, Any]]:
    p = "load_customer_accounts"
    account_cols = [
        ("ACCOUNT_ID", "ORA_DW.CUST_ACCOUNTS", "ACCOUNT_ID", None),
        ("CUSTOMER_ID", "ORA_DW.CUST_ACCOUNTS", "CUSTOMER_ID", None),
        ("ACCOUNT_TYPE", "ORA_DW.CUST_ACCOUNTS", "ACCOUNT_TYPE", "$ACCTTYPE."),
        ("ACCOUNT_STATUS", "ORA_DW.CUST_ACCOUNTS", "ACCOUNT_STATUS", "$ACCTSTAT."),
        ("OPEN_DATE", "ORA_DW.CUST_ACCOUNTS", "OPEN_DATE", "DATE9."),
        ("CLOSE_DATE", "ORA_DW.CUST_ACCOUNTS", "CLOSE_DATE", "DATE9."),
        ("CURRENT_BALANCE", "ORA_DW.CUST_ACCOUNTS", "CURRENT_BALANCE", "DOLLAR18.2"),
        ("AVAILABLE_BALANCE", "ORA_DW.CUST_ACCOUNTS", "AVAILABLE_BALANCE", "DOLLAR18.2"),
        ("CREDIT_LIMIT", "ORA_DW.CUST_ACCOUNTS", "CREDIT_LIMIT", "DOLLAR18.2"),
        ("INTEREST_RATE", "ORA_DW.CUST_ACCOUNTS", "INTEREST_RATE", None),
        ("BRANCH_ID", "ORA_DW.CUST_ACCOUNTS", "BRANCH_ID", None),
        ("OFFICER_ID", "ORA_DW.CUST_ACCOUNTS", "OFFICER_ID", None),
        ("LAST_ACTIVITY_DATE", "ORA_DW.CUST_ACCOUNTS", "LAST_ACTIVITY_DATE", "DATE9."),
        ("FIRST_NAME", "ORA_DW.CUST_DEMOGRAPHICS", "FIRST_NAME", None),
        ("LAST_NAME", "ORA_DW.CUST_DEMOGRAPHICS", "LAST_NAME", None),
        ("SSN_HASH", "ORA_DW.CUST_DEMOGRAPHICS", "SSN_HASH", None),
        ("DATE_OF_BIRTH", "ORA_DW.CUST_DEMOGRAPHICS", "DATE_OF_BIRTH", None),
        ("CUSTOMER_SEGMENT", "ORA_DW.CUST_DEMOGRAPHICS", "CUSTOMER_SEGMENT", "$CUSTSEG."),
        ("RISK_RATING", "ORA_DW.CUST_DEMOGRAPHICS", "RISK_RATING", "RISKRATE."),
        ("REGION_CODE", "ORA_DW.CUST_DEMOGRAPHICS", "REGION_CODE", "$REGION."),
        ("PRIMARY_EMAIL", "ORA_DW.CUST_DEMOGRAPHICS", "PRIMARY_EMAIL", None),
        ("PHONE_NUMBER", "ORA_DW.CUST_DEMOGRAPHICS", "PHONE_NUMBER", None),
    ]
    base = [
        carried(
            n,
            t,
            c,
            p,
            "set WORK.ACCT_RAW",
            fmt=f,
            key=n in {"ACCOUNT_ID", "CUSTOMER_ID", "ACCOUNT_STATUS", "OPEN_DATE", "REGION_CODE"},
            key_reason="ON / WHERE" if n in {"ACCOUNT_ID", "CUSTOMER_ID", "ACCOUNT_STATUS", "OPEN_DATE", "REGION_CODE"} else None,
        )
        for n, t, c, f in account_cols
    ]
    derived = [
        fact("ACCT_AGE_MONTHS", "intck('month', OPEN_DATE, \"&run_date\"d)", "num", p, "ACCT_AGE_MONTHS ="),
        fact("DAYS_INACTIVE", "\"&run_date\"d - LAST_ACTIVITY_DATE", "num", p, "DAYS_INACTIVE ="),
        fact("UTILIZATION_PCT", "(CURRENT_BALANCE / CREDIT_LIMIT) * 100", "num", p, "UTILIZATION_PCT ="),
        fact("DORMANCY_FLAG", "'Y' / 'N'", "char$1", p, "DORMANCY_FLAG = 'Y'"),
        fact("HIGH_BALANCE_FLAG", "'Y' / 'N'", "char$1", p, "HIGH_BALANCE_FLAG = 'Y'"),
        fact("SNAPSHOT_DATE", "\"&run_date\"d", "num (SAS date)", p, "SNAPSHOT_DATE ="),
        fact("LOAD_TIMESTAMP", "datetime()", "num (SAS datetime)", p, "LOAD_TIMESTAMP ="),
    ]
    stg_cols = base + derived
    exception_cols = [
        dict(item, note="Exception output shares the compiled DATA-step PDV; values assigned after early OUTPUT may be missing.")
        for item in stg_cols
    ]
    tables = [
        {
            "table": "STG_BANK.CUST_ACCOUNTS_DAILY",
            "created_or_appended_by": ["Programs/Banking/load_customer_accounts.sas:82"],
            "columns": stg_cols,
        },
        {
            "table": "STG_BANK.ACCT_EXCEPTIONS",
            "created_or_appended_by": ["Programs/Banking/load_customer_accounts.sas:168"],
            "columns": exception_cols,
            "note": "WORK.ACCT_EXCEPTIONS is output at lines 129/138/146, then inserted with SELECT *; the compiled PDV determines column order.",
        },
    ]

    p = "daily_transaction_processing"
    txn = [
        ("TRANSACTION_ID", "RAW_BANK.TXN_FEED_20240131", "TRANSACTION_ID"),
        ("ACCOUNT_ID", "RAW_BANK.TXN_FEED_20240131", "ACCOUNT_ID"),
        ("TRANSACTION_DATE", "RAW_BANK.TXN_FEED_20240131", "TRANSACTION_DATE"),
        ("TRANSACTION_TYPE", "RAW_BANK.TXN_FEED_20240131", "TRANSACTION_TYPE"),
        ("TRANSACTION_AMOUNT", "RAW_BANK.TXN_FEED_20240131", "TRANSACTION_AMOUNT"),
        ("CHANNEL", "RAW_BANK.TXN_FEED_20240131", "CHANNEL"),
        ("MERCHANT_CATEGORY", "RAW_BANK.TXN_FEED_20240131", "MERCHANT_CATEGORY"),
        ("DESCRIPTION", "RAW_BANK.TXN_FEED_20240131", "DESCRIPTION"),
        ("POST_DATE", "RAW_BANK.TXN_FEED_20240131", "POST_DATE"),
        ("CURRENCY_CODE", "RAW_BANK.TXN_FEED_20240131", "CURRENCY_CODE"),
    ]
    account_enrich = [
        ("ACCOUNT_TYPE", "STG_BANK.CUST_ACCOUNTS_DAILY", "ACCOUNT_TYPE"),
        ("CUSTOMER_ID", "STG_BANK.CUST_ACCOUNTS_DAILY", "CUSTOMER_ID"),
        ("CUSTOMER_SEGMENT", "STG_BANK.CUST_ACCOUNTS_DAILY", "CUSTOMER_SEGMENT"),
        ("REGION_CODE", "STG_BANK.CUST_ACCOUNTS_DAILY", "REGION_CODE"),
        ("BRANCH_ID", "STG_BANK.CUST_ACCOUNTS_DAILY", "BRANCH_ID"),
    ]
    txn_cols = [
        carried(n, t, c, p, "select", key=n in {"TRANSACTION_ID", "ACCOUNT_ID", "TRANSACTION_DATE"},
                key_reason="ON / ORDER BY / BY" if n in {"TRANSACTION_ID", "ACCOUNT_ID", "TRANSACTION_DATE"} else None)
        for n, t, c in txn
    ]
    txn_cols += [
        carried(n, t, c, p, "select", key=n == "ACCOUNT_ID", key_reason="ON / ORDER BY" if n == "ACCOUNT_ID" else None)
        for n, t, c in account_enrich
    ]
    txn_cols += [
        fact("PRE_TXN_BALANCE", "a.CURRENT_BALANCE as PRE_TXN_BALANCE", "num", p, "PRE_TXN_BALANCE", fmt="DOLLAR18.2"),
        fact("POST_TXN_BALANCE", "case ... end as POST_TXN_BALANCE", "num", p, "POST_TXN_BALANCE", fmt="DOLLAR18.2"),
        carried("RISK_RATING", "STG_BANK.CUST_ACCOUNTS_DAILY", "RISK_RATING", p, "a.RISK_RATING"),
        fact("RUNNING_BALANCE", "RUNNING_BALANCE = PRE_TXN_BALANCE + signed TRANSACTION_AMOUNT", "num", p, "retain RUNNING_BALANCE", fmt="DOLLAR18.2",
             key=False, note="Retained and updated in BY ACCOUNT_ID TRANSACTION_DATE TRANSACTION_ID order."),
    ]
    tables += [
        {
            "table": "CURATED.DAILY_TRANSACTIONS",
            "created_or_appended_by": ["Programs/Banking/daily_transaction_processing.sas:207"],
            "columns": txn_cols,
        },
        {
            "table": "CURATED.RUNNING_BALANCES",
            "created_or_appended_by": ["Programs/Banking/daily_transaction_processing.sas:222"],
            "columns": [
                carried("ACCOUNT_ID", "RAW_BANK.TXN_FEED_20240131", "ACCOUNT_ID", p, "keep ACCOUNT_ID", key=True, key_reason="BY"),
                carried("TRANSACTION_DATE", "RAW_BANK.TXN_FEED_20240131", "TRANSACTION_DATE", p, "keep ACCOUNT_ID", key=True, key_reason="BY"),
                carried("TRANSACTION_ID", "RAW_BANK.TXN_FEED_20240131", "TRANSACTION_ID", p, "keep ACCOUNT_ID", key=True, key_reason="BY"),
                fact("RUNNING_BALANCE", "RUNNING_BALANCE", "num", p, "keep ACCOUNT_ID", fmt="DOLLAR18.2",
                     note="Value is carried from WORK.TXN_WITH_BALANCE after retained BY-group calculation."),
            ],
        },
    ]
    anomaly = [
        *txn_cols,
        fact("AVG_TXN_AMT", "mean(abs(TRANSACTION_AMOUNT)) as AVG_TXN_AMT", "num (aggregate)", p, "AVG_TXN_AMT"),
        fact("STD_TXN_AMT", "std(abs(TRANSACTION_AMOUNT)) as STD_TXN_AMT", "num (aggregate)", p, "STD_TXN_AMT"),
        fact("Z_SCORE", "(abs(e.TRANSACTION_AMOUNT) - s.AVG_TXN_AMT) / s.STD_TXN_AMT", "num", p, "as Z_SCORE"),
        fact("ANOMALY_TYPE", "case ... end as ANOMALY_TYPE", "char$20", p, "ANOMALY_TYPE length=20"),
    ]
    tables.append({
        "table": "CURATED.TXN_ANOMALIES",
        "created_or_appended_by": ["Programs/Banking/daily_transaction_processing.sas:214"],
        "columns": anomaly,
    })
    tables.append({
        "table": "WORK.TXN_REJECTED",
        "created_or_appended_by": ["Programs/Banking/daily_transaction_processing.sas:45"],
        "columns": [
            *[
                carried(n, t, c, p, "set RAW_BANK")
                for n, t, c in txn
            ],
            fact("REJECT_REASON", "length REJECT_REASON $200", "char$200", p, "length REJECT_REASON"),
        ],
        "note": "Reject dataset is created by the two-target DATA step and removed in cleanup; it is not appended to a permanent table.",
    })

    p = "credit_risk_scoring"
    score_base = [
        ("ACCOUNT_ID", "STG_BANK.CUST_ACCOUNTS_DAILY", "ACCOUNT_ID"),
        ("CUSTOMER_ID", "STG_BANK.CUST_ACCOUNTS_DAILY", "CUSTOMER_ID"),
        ("ACCOUNT_TYPE", "STG_BANK.CUST_ACCOUNTS_DAILY", "ACCOUNT_TYPE"),
        ("CURRENT_BALANCE", "STG_BANK.CUST_ACCOUNTS_DAILY", "CURRENT_BALANCE"),
        ("CREDIT_LIMIT", "STG_BANK.CUST_ACCOUNTS_DAILY", "CREDIT_LIMIT"),
        ("ACCT_AGE_MONTHS", "STG_BANK.CUST_ACCOUNTS_DAILY", "ACCT_AGE_MONTHS"),
        ("DAYS_INACTIVE", "STG_BANK.CUST_ACCOUNTS_DAILY", "DAYS_INACTIVE"),
        ("UTILIZATION_PCT", "STG_BANK.CUST_ACCOUNTS_DAILY", "UTILIZATION_PCT"),
        ("CUSTOMER_SEGMENT", "STG_BANK.CUST_ACCOUNTS_DAILY", "CUSTOMER_SEGMENT"),
        ("REGION_CODE", "STG_BANK.CUST_ACCOUNTS_DAILY", "REGION_CODE"),
        ("FICO_SCORE", "ORA_DW.BUREAU_SCORES", "FICO_SCORE"),
        ("VANTAGE_SCORE", "ORA_DW.BUREAU_SCORES", "VANTAGE_SCORE"),
        ("BUREAU_INQS_6MO", "ORA_DW.BUREAU_SCORES", "BUREAU_INQS_6MO"),
        ("BUREAU_TRADES_OPEN", "ORA_DW.BUREAU_SCORES", "BUREAU_TRADES_OPEN"),
        ("BUREAU_DEROGS", "ORA_DW.BUREAU_SCORES", "BUREAU_DEROGS"),
        ("BUREAU_UTIL_PCT", "ORA_DW.BUREAU_SCORES", "BUREAU_UTIL_PCT"),
        ("BUREAU_OLDEST_TRADE_MO", "ORA_DW.BUREAU_SCORES", "BUREAU_OLDEST_TRADE_MO"),
        ("PMT_ONTIME_12MO", "ORA_DW.PAYMENT_HISTORY", "PMT_ONTIME_12MO"),
        ("PMT_LATE_30_12MO", "ORA_DW.PAYMENT_HISTORY", "PMT_LATE_30_12MO"),
        ("PMT_LATE_60_12MO", "ORA_DW.PAYMENT_HISTORY", "PMT_LATE_60_12MO"),
        ("PMT_LATE_90_12MO", "ORA_DW.PAYMENT_HISTORY", "PMT_LATE_90_12MO"),
        ("MAX_DAYS_PAST_DUE_EVER", "ORA_DW.PAYMENT_HISTORY", "MAX_DAYS_PAST_DUE_EVER"),
        ("MONTHS_SINCE_LAST_DPD", "ORA_DW.PAYMENT_HISTORY", "MONTHS_SINCE_LAST_DPD"),
        ("AVG_PMT_RATIO_12MO", "ORA_DW.PAYMENT_HISTORY", "AVG_PMT_RATIO_12MO"),
        ("COLLATERAL_VALUE", "ORA_DW.COLLATERAL", "COLLATERAL_VALUE"),
        ("LAST_APPRAISAL_DATE", "ORA_DW.COLLATERAL", "LAST_APPRAISAL_DATE"),
    ]
    score_cols = [
        carried(n, t, c, p, "select", key=n in {"ACCOUNT_ID", "CUSTOMER_ID"},
                key_reason="ON" if n in {"ACCOUNT_ID", "CUSTOMER_ID"} else None)
        for n, t, c in score_base
    ]
    score_cols.append(fact("LTV", "case when c.COLLATERAL_VALUE > 0 then ... end as LTV", "num", p, "end as LTV", fmt="8.4"))
    score_cols += [
        fact("PD", "1 / (1 + exp(-LOG_ODDS))", "num", p, "PD =", fmt="PERCENT8.4"),
        fact("LGD", "max(0, min(1, (LTV - 0.5) * 0.8))", "num", p, "LGD =", fmt="PERCENT8.4"),
        fact("EAD", "CURRENT_BALANCE + 0.50 * (CREDIT_LIMIT - CURRENT_BALANCE)", "num", p, "EAD =", fmt="DOLLAR18.2"),
        fact("EXPECTED_LOSS", "PD * LGD * EAD", "num", p, "EXPECTED_LOSS =", fmt="DOLLAR18.2"),
        fact("NEW_RISK_RATING", "7-way PD threshold assignment", "num", p, "NEW_RISK_RATING ="),
        fact("SCORE_DATE", "\"&score_date\"d", "num (SAS date)", p, "SCORE_DATE =", fmt="DATE9."),
        fact("MODEL_ID", "\"&model_id\"", "char$UNKNOWN", p, "MODEL_ID =", note="Macro parameter length is not declared in this program."),
        fact("SCORE_TIMESTAMP", "datetime()", "num (SAS datetime)", p, "SCORE_TIMESTAMP =", fmt="DATETIME20."),
    ]
    tables += [
        {
            "table": "CURATED.RISK_SCORES",
            "created_or_appended_by": ["Programs/Banking/credit_risk_scoring.sas:231"],
            "columns": score_cols,
        },
        {
            "table": "CURATED.RISK_MIGRATION",
            "created_or_appended_by": ["Programs/Banking/credit_risk_scoring.sas:238"],
            "columns": [
                fact("SCORE_DATE", "\"&score_date\"d as SCORE_DATE", "num (SAS date)", p, "SCORE_DATE format=date9.", fmt="DATE9."),
                carried("ACCOUNT_ID", "STG_BANK.CUST_ACCOUNTS_DAILY", "ACCOUNT_ID", p, "on s.ACCOUNT_ID = a.ACCOUNT_ID", key=True, key_reason="ON"),
                carried("PREV_RATING", "STG_BANK.CUST_ACCOUNTS_DAILY", "RISK_RATING", p, "a.RISK_RATING as PREV_RATING"),
                carried("CURR_RATING", "CURATED.RISK_SCORES", "NEW_RISK_RATING", p, "s.NEW_RISK_RATING as CURR_RATING"),
                fact("MIGRATION_DIRECTION", "case ... end as MIGRATION_DIRECTION", "char$10", p, "MIGRATION_DIRECTION length=10"),
                carried("PD", "CURATED.RISK_SCORES", "PD", p, "s.PD"),
                carried("EXPECTED_LOSS", "CURATED.RISK_SCORES", "EXPECTED_LOSS", p, "s.EXPECTED_LOSS"),
            ],
        },
        {
            "table": "REPORTS.RISK_SUMMARY",
            "created_or_appended_by": ["Programs/Banking/credit_risk_scoring.sas:249"],
            "columns": [
                carried("ACCOUNT_TYPE", "CURATED.RISK_SCORES", "ACCOUNT_TYPE", p, "class ACCOUNT_TYPE"),
                carried("NEW_RISK_RATING", "CURATED.RISK_SCORES", "NEW_RISK_RATING", p, "class ACCOUNT_TYPE"),
                fact("N_ACCOUNTS", "n=N_ACCOUNTS", "num", p, "n=N_ACCOUNTS"),
                fact("AVG_PD", "mean(PD)=AVG_PD", "num (aggregate)", p, "mean(PD)=AVG_PD"),
                fact("AVG_LGD", "mean(LGD)=AVG_LGD", "num (aggregate)", p, "mean(LGD)=AVG_LGD"),
                fact("TOTAL_EAD", "sum(EAD)=TOTAL_EAD", "num (aggregate)", p, "sum(EAD)=TOTAL_EAD"),
                fact("TOTAL_EL", "sum(EXPECTED_LOSS)=TOTAL_EL", "num (aggregate)", p, "sum(EXPECTED_LOSS)=TOTAL_EL"),
            ],
        },
    ]

    p = "monthly_regulatory_reporting"
    tables += [
        {
            "table": "REPORTS.MONTHLY_RWA",
            "created_or_appended_by": ["Programs/Banking/monthly_regulatory_reporting.sas:41"],
            "columns": [
                fact("REPORT_MONTH", "\"&report_month\" as REPORT_MONTH", "char$6", p, "REPORT_MONTH length=6"),
                carried("ACCOUNT_TYPE", "STG_BANK.CUST_ACCOUNTS_DAILY", "ACCOUNT_TYPE", p, "ACCOUNT_TYPE,", key=True, key_reason="GROUP BY / ORDER BY"),
                carried("CUSTOMER_SEGMENT", "STG_BANK.CUST_ACCOUNTS_DAILY", "CUSTOMER_SEGMENT", p, "CUSTOMER_SEGMENT,", key=True, key_reason="GROUP BY / ORDER BY"),
                fact("RISK_WEIGHT", "case when ACCOUNT_TYPE ... end as RISK_WEIGHT", "num", p, "end as RISK_WEIGHT"),
                fact("N_ACCOUNTS", "count(*) as N_ACCOUNTS", "num", p, "count(*) as N_ACCOUNTS"),
                fact("TOTAL_EXPOSURE", "sum(CURRENT_BALANCE) as TOTAL_EXPOSURE", "num (aggregate)", p, "as TOTAL_EXPOSURE", fmt="DOLLAR20.2"),
                fact("RWA", "sum(CURRENT_BALANCE * calculated RISK_WEIGHT) as RWA", "num (aggregate)", p, "as RWA", fmt="DOLLAR20.2"),
            ],
        },
        {
            "table": "REPORTS.DELINQUENCY_AGING",
            "created_or_appended_by": ["Programs/Banking/monthly_regulatory_reporting.sas:73"],
            "columns": [
                fact("REPORT_MONTH", "\"&report_month\" as REPORT_MONTH", "char$6", p, "REPORT_MONTH length=6"),
                carried("ACCOUNT_TYPE", "STG_BANK.CUST_ACCOUNTS_DAILY", "ACCOUNT_TYPE", p, "ACCOUNT_TYPE,", key=True, key_reason="GROUP BY / ORDER BY"),
                carried("REGION_CODE", "STG_BANK.CUST_ACCOUNTS_DAILY", "REGION_CODE", p, "REGION_CODE,", key=True, key_reason="GROUP BY / ORDER BY"),
                fact("DELINQ_BUCKET", "case when DAYS_PAST_DUE ... end as DELINQ_BUCKET", "char$10", p, "DELINQ_BUCKET length=10"),
                fact("N_ACCOUNTS", "count(*) as N_ACCOUNTS", "num", p, "count(*)               as N_ACCOUNTS"),
                fact("TOTAL_BALANCE", "sum(CURRENT_BALANCE) as TOTAL_BALANCE", "num (aggregate)", p, "as TOTAL_BALANCE", fmt="DOLLAR20.2"),
                fact("TOTAL_PAST_DUE", "sum(PAST_DUE_AMOUNT) as TOTAL_PAST_DUE", "num (aggregate)", p, "as TOTAL_PAST_DUE", fmt="DOLLAR20.2"),
            ],
        },
        {
            "table": "REPORTS.LLP_COVERAGE",
            "created_or_appended_by": ["Programs/Banking/monthly_regulatory_reporting.sas:115"],
            "columns": [
                fact("REPORT_MONTH", "\"&report_month\" as REPORT_MONTH", "char$6", p, "REPORT_MONTH length=6"),
                carried("ACCOUNT_TYPE", "STG_BANK.CUST_ACCOUNTS_DAILY", "ACCOUNT_TYPE", p, "a.ACCOUNT_TYPE,", key=True, key_reason="GROUP BY"),
                fact("N_LOANS", "count(*) as N_LOANS", "num", p, "count(*) as N_LOANS"),
                fact("GROSS_LOANS", "sum(a.CURRENT_BALANCE) as GROSS_LOANS", "num (aggregate)", p, "as GROSS_LOANS", fmt="DOLLAR20.2"),
                fact("TOTAL_ALLOWANCE", "sum(l.ALLOWANCE_AMT) as TOTAL_ALLOWANCE", "num (aggregate)", p, "as TOTAL_ALLOWANCE", fmt="DOLLAR20.2"),
                fact("COVERAGE_PCT", "sum(l.ALLOWANCE_AMT) / sum(a.CURRENT_BALANCE) * 100", "num", p, "end as COVERAGE_PCT", fmt="8.2"),
                fact("NPL_BALANCE", "sum(case when l.DAYS_PAST_DUE >= 90 then ... end)", "num (aggregate)", p, "as NPL_BALANCE", fmt="DOLLAR20.2"),
                fact("NPL_COVERAGE_PCT", "sum(l.ALLOWANCE_AMT) / calculated NPL_BALANCE * 100", "num", p, "end as NPL_COVERAGE_PCT", fmt="8.2"),
            ],
        },
        {
            "table": "REPORTS.CAPITAL_ADEQUACY",
            "created_or_appended_by": ["Programs/Banking/monthly_regulatory_reporting.sas:170"],
            "columns": [
                fact("REPORT_MONTH", "\"&report_month\" as REPORT_MONTH", "char$6", p, "REPORT_MONTH length=6"),
                fact("TOTAL_RWA", "sum(RWA) as TOTAL_RWA", "num (aggregate)", p, "as TOTAL_RWA", fmt="DOLLAR20.2"),
                fact("CET1_CAPITAL", "50000000 as CET1_CAPITAL", "num", p, "50000000                     as CET1_CAPITAL", fmt="DOLLAR20.2"),
                fact("TIER1_CAPITAL", "65000000 as TIER1_CAPITAL", "num", p, "65000000                     as TIER1_CAPITAL", fmt="DOLLAR20.2"),
                fact("TOTAL_CAPITAL", "80000000 as TOTAL_CAPITAL", "num", p, "80000000                     as TOTAL_CAPITAL", fmt="DOLLAR20.2"),
                fact("CET1_RATIO", "50000000 / sum(RWA) * 100", "num", p, "end as CET1_RATIO", fmt="8.2"),
                fact("TIER1_RATIO", "65000000 / sum(RWA) * 100", "num", p, "end as TIER1_RATIO", fmt="8.2"),
                fact("TOTAL_CAPITAL_RATIO", "80000000 / sum(RWA) * 100", "num", p, "end as TOTAL_CAPITAL_RATIO", fmt="8.2"),
                fact("CET1_STATUS", "case ... then 'PASS' else 'FAIL' end", "char$4", p, "as CET1_STATUS length=4"),
                fact("TIER1_STATUS", "case ... then 'PASS' else 'FAIL' end", "char$4", p, "as TIER1_STATUS length=4"),
                fact("TOTAL_CAPITAL_STATUS", "case ... then 'PASS' else 'FAIL' end", "char$4", p, "as TOTAL_CAPITAL_STATUS length=4"),
            ],
        },
    ]

    p = "run_daily_banking"
    tables.append({
        "table": "ARCHIVE.BATCH_HISTORY",
        "created_or_appended_by": ["BatchJobs/run_daily_banking.sas:142"],
        "columns": [
            fact("BATCH_ID", '"&batch_id"', "char$60", p, "length BATCH_ID $60"),
            fact("STEP_NUM", "&step_num", "num", p, "length BATCH_ID $60"),
            fact("STEP_NAME", '"&step_name"', "char$50", p, "length BATCH_ID $60"),
            fact("PROGRAM_PATH", '"&program"', "char$200", p, "length BATCH_ID $60"),
            fact("STATUS", 'ifc(&step_rc = 0, "PASS", "FAIL")', "char$10", p, "STATUS $10"),
            fact("START_TIME", "&step_start", "num (SAS datetime)", p, "format START_TIME", fmt="DATETIME20."),
            fact("END_TIME", "%sysfunc(datetime())", "num (SAS datetime)", p, "format START_TIME", fmt="DATETIME20."),
            fact("DURATION", "%sysevalf(%sysfunc(datetime()) - &step_start)", "num (SAS time)", p, "DURATION 8", fmt="TIME8."),
            fact("ERROR_MSG", 'ifc(&step_rc = 0, "", "SYSCC=&step_rc")', "char$500", p, "ERROR_MSG $500"),
        ],
    })
    return tables


def autoexec_variables() -> set[str]:
    names: set[str] = set()
    for path in (AUTOEXEC, AUTOEXEC_LOCAL):
        for match in re.finditer(r"%let\s+([A-Za-z_][A-Za-z0-9_]*)\s*=", read(path), re.I):
            names.add(match.group(1).upper())
    return names


def program_metadata() -> list[dict[str, Any]]:
    globals_ = autoexec_variables()
    result = []
    for name, text in TEXT.items():
        refs = sorted(
            {
                match.group(1).upper()
                for match in re.finditer(r"&([A-Za-z_][A-Za-z0-9_]*)", text)
                if match.group(1).upper() in globals_
            }
        )
        rounds = [
            {"arguments": shorten(match.group(1)), "line": text[: match.start()].count("\n") + 1}
            for match in re.finditer(r"\bround\s*\(([^)]*)\)", text, re.I | re.S)
        ]
        sequential = []
        for pattern, label in [
            (r"^\s*retain\s+([^;]+);", "retain"),
            (r"^\s*by\s+([^;]+);", "by"),
            (r"\bfirst\.([A-Za-z_][A-Za-z0-9_]*)", "first."),
            (r"\blag\s*\(([^)]*)\)", "lag"),
        ]:
            for match in re.finditer(pattern, text, re.I | re.M):
                sequential.append({
                    "kind": label,
                    "expression": shorten(match.group(0)),
                    "line": text[: match.start()].count("\n") + 1,
                })
        clock_calls = []
        for match in re.finditer(r"\b(datetime|today|time)\s*\(\s*\)", text, re.I):
            clock_calls.append({
                "call": match.group(0),
                "line": text[: match.start()].count("\n") + 1,
            })
        appends = []
        for match in re.finditer(
            r"proc\s+append\s+base\s*=\s*([^\s;]+)\s+data\s*=\s*([^\s;]+)",
            text,
            re.I | re.S,
        ):
            appends.append({
                "base": match.group(1),
                "data": match.group(2),
                "line": text[: match.start()].count("\n") + 1,
            })
        locks = [
            {
                "target": match.group(1).strip(),
                "arguments": shorten(match.group(0)),
                "line": text[: match.start()].count("\n") + 1,
            }
            for match in re.finditer(r"%lock\s*\(([^)]*)\)", text, re.I | re.S)
        ]
        business_where = []
        for match in re.finditer(r"\bwhere\b(.*?)(?:;|\n\s*group\s+by)", text, re.I | re.S):
            expr = shorten(match.group(1))
            if re.search(r"date|dt|month|score_date|snapshot_date|open_date", expr, re.I):
                business_where.append({
                    "expression": expr,
                    "line": text[: match.start()].count("\n") + 1,
                })
        result.append({
            "program": rel(PROGRAMS[name]),
            "name": name,
            "autoexec_macro_variables": refs,
            "round_calls": rounds,
            "row_sequential_logic": sorted(sequential, key=lambda item: item["line"]),
            "datetime_today_time_calls": clock_calls,
            "proc_append": appends,
            "lock_usage": locks,
            "business_date_where": business_where,
        })
    return result


def markdown(data: dict[str, Any]) -> str:
    def esc(value: Any) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = [
        "# P1 banking-core column extraction",
        "",
        f"Repository: `{data['repository']}`",
        "",
        "Mechanical extraction of output-table columns from the five requested SAS programs.",
        "Types are SAS types/evidence only; no Delta types are computed.",
        "",
        "## Output tables",
        "",
    ]
    for table in data["tables"]:
        lines += [
            f"### {table['table']}",
            "",
            f"Created/appended by: {', '.join(table['created_or_appended_by'])}",
            "",
            "| # | Column | Expression/source | SAS type | Format | Key | Evidence | Cite | CSV evidence |",
            "| ---: | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for index, item in enumerate(table["columns"], 1):
            csv_item = item.get("csv_evidence")
            csv_text = (
                f"{csv_item['csv']}::{csv_item['column']}={csv_item['sample']}"
                if csv_item else "—"
            )
            lines.append(
                "| "
                + " | ".join(
                    esc(x)
                    for x in [
                        index,
                        item["name"],
                        item["expression"],
                        item["sas_type"],
                        item.get("format") or "—",
                        "yes" if item["key"] else "no",
                        item["evidence"],
                        item["cite"],
                        csv_text,
                    ]
                )
                + " |"
            )
        if table.get("note"):
            lines += ["", f"Note: {table['note']}"]
        lines.append("")
    lines += ["## Per-program runtime evidence", ""]
    for program in data["programs"]:
        round_text = ", ".join(
            f"{item['arguments']} (line {item['line']})"
            for item in program["round_calls"]
        ) or "none"
        clock_text = ", ".join(
            f"{item['call']} (line {item['line']})"
            for item in program["datetime_today_time_calls"]
        ) or "none"
        append_text = ", ".join(
            f"base={item['base']} data={item['data']} (line {item['line']})"
            for item in program["proc_append"]
        ) or "none"
        lock_text = ", ".join(
            f"{item['arguments']} (line {item['line']})"
            for item in program["lock_usage"]
        ) or "none"
        where_text = ", ".join(
            f"{item['expression']} (line {item['line']})"
            for item in program["business_date_where"]
        ) or "none"
        lines += [
            f"### {program['program']}",
            "",
            f"- Autoexec macro variables: {', '.join(program['autoexec_macro_variables']) or '—'}",
            f"- Round calls: {round_text}",
            f"- Datetime/today/time calls: {clock_text}",
            f"- PROC APPEND: {append_text}",
            f"- `%lock`: {lock_text}",
            f"- Business-date WHERE: {where_text}",
        ]
        if program["row_sequential_logic"]:
            lines.append("- Row-sequential logic:")
            lines.extend(
                f"  - {x['kind']}: `{x['expression']}` (line {x['line']})"
                for x in program["row_sequential_logic"]
            )
        else:
            lines.append("- Row-sequential logic: none")
        lines.append("")
    lines += [
        "## UNKNOWN / limitations",
        "",
        "UNKNOWN is retained where the SAS source does not declare a fixed character length "
        "or where a macro parameter controls the resulting length. Source-table columns are "
        "marked INFERRED and include seeded CSV header/sample evidence when available.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    data = {
        "repository": str(REPO),
        "scope": [rel(path) for path in PROGRAMS.values()],
        "tables": output_tables(),
        "programs": program_metadata(),
        "unknowns": [
            "MODEL_ID has no declared length; emitted as char$UNKNOWN.",
            "Source-table character lengths are not declared in the selected programs; source CSV header/sample is supplied instead.",
            "Exception output columns are determined by the compiled DATA-step PDV and may be missing for variables assigned after early OUTPUT.",
        ],
    }
    JSON_PATH.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    MARKDOWN_PATH.write_text(markdown(data), encoding="utf-8")
    print(f"Wrote {JSON_PATH}")
    print(f"Wrote {MARKDOWN_PATH}")
    print(f"tables={len(data['tables'])}; programs={len(data['programs'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
