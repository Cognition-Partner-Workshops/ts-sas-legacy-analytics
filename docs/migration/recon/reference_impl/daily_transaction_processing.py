"""Literal re-expression of Programs/Banking/daily_transaction_processing.sas
(%daily_transaction_processing(txn_date=&CURR_DT)).

Outputs: CURATED.DAILY_TRANSACTIONS (history + appended feed rows),
CURATED.TXN_ANOMALIES, CURATED.RUNNING_BALANCES and the WORK-only
TXN_REJECTED rows. Line numbers refer to the SAS file.
"""
from __future__ import annotations

import datetime as dt
from typing import Dict, List, Tuple

from . import sas_semantics as S
from .seeds import Row

VALID_TYPES = ("DEP", "WDR", "TRF", "PMT", "FEE", "INT", "ADJ", "REV", "CHG", "REF")  # line 80
FEED_COLS = ["TRANSACTION_ID", "ACCOUNT_ID", "TRANSACTION_DATE", "TRANSACTION_TYPE",
             "TRANSACTION_AMOUNT", "CHANNEL", "MERCHANT_CATEGORY", "DESCRIPTION",
             "POST_DATE", "CURRENCY_CODE"]


def validate(feed: List[Row], txn_date: dt.date) -> Tuple[List[Row], List[Row], List[Row]]:
    """DATA step lines 45-97. Returns (TXN_VALIDATED, TXN_REJECTED, TXN_REJECTED-with-reason).

    `drop REJECT_REASON;` (line 96) applies to both output data sets, so the
    literal WORK.TXN_REJECTED has only the feed columns (AMBIGUITIES AMB-02).
    """
    valid: List[Row] = []
    rejected_full: List[Row] = []
    for src in feed:
        pdv: Row = dict(src)                                                # line 48
        pdv["REJECT_REASON"] = ""

        if S.missing(pdv["TRANSACTION_ID"]):                                # lines 53-57
            pdv["REJECT_REASON"] = "Missing TRANSACTION_ID"
            rejected_full.append(dict(pdv)); continue
        if S.missing(pdv["ACCOUNT_ID"]):                                    # lines 59-63
            pdv["REJECT_REASON"] = "Missing ACCOUNT_ID"
            rejected_full.append(dict(pdv)); continue
        if S.missing(pdv["TRANSACTION_AMOUNT"]):                            # lines 65-69
            pdv["REJECT_REASON"] = "Missing TRANSACTION_AMOUNT"
            rejected_full.append(dict(pdv)); continue
        if S.gt(S.sas_abs(pdv["TRANSACTION_AMOUNT"]), 10000000):            # lines 72-77
            pdv["REJECT_REASON"] = S.catx(" ", "Amount exceeds threshold:",
                                          S.put_dollar(pdv["TRANSACTION_AMOUNT"], 18, 2))
            rejected_full.append(dict(pdv)); continue
        if pdv["TRANSACTION_TYPE"] not in VALID_TYPES:                      # lines 80-85
            pdv["REJECT_REASON"] = S.catx(" ", "Invalid transaction type:", pdv["TRANSACTION_TYPE"])
            rejected_full.append(dict(pdv)); continue
        if S.gt(_days(pdv["TRANSACTION_DATE"]), _days(txn_date)):           # lines 88-93
            pdv["REJECT_REASON"] = S.catx(" ", "Future dated:", S.date9_put(pdv["TRANSACTION_DATE"]))
            rejected_full.append(dict(pdv)); continue

        valid.append({c: pdv[c] for c in FEED_COLS})                        # line 95 (REJECT_REASON dropped)

    rejected_literal = [{c: r[c] for c in FEED_COLS} for r in rejected_full]   # line 96
    return valid, rejected_literal, rejected_full


def _days(d):
    return None if d is None else float(d.toordinal())


def enrich(valid: List[Row], daily_accounts: List[Row]) -> List[Row]:
    """PROC SQL lines 105-130: left join onto STG_BANK.CUST_ACCOUNTS_DAILY."""
    acct = {a["ACCOUNT_ID"]: a for a in daily_accounts}                     # ACCOUNT_ID unique in snapshot
    out: List[Row] = []
    for t in valid:
        a = acct.get(t["ACCOUNT_ID"])                                       # lines 126-127
        g = a.__getitem__ if a is not None else (lambda c: None)
        gc = a.__getitem__ if a is not None else (lambda c: "")
        r: Row = dict(t)                                                    # line 108 t.*
        r["ACCOUNT_TYPE"] = gc("ACCOUNT_TYPE")                              # lines 109-113
        r["CUSTOMER_ID"] = gc("CUSTOMER_ID")
        r["CUSTOMER_SEGMENT"] = gc("CUSTOMER_SEGMENT")
        r["REGION_CODE"] = gc("REGION_CODE")
        r["BRANCH_ID"] = gc("BRANCH_ID")
        bal = g("CURRENT_BALANCE")
        r["PRE_TXN_BALANCE"] = bal                                          # line 114
        tt, amt = t["TRANSACTION_TYPE"], t["TRANSACTION_AMOUNT"]
        if tt in ("DEP", "INT", "REF", "REV"):                              # lines 115-123
            r["POST_TXN_BALANCE"] = S.add(bal, amt)
        elif tt in ("WDR", "PMT", "FEE", "CHG"):
            r["POST_TXN_BALANCE"] = S.sub(bal, S.sas_abs(amt))
        elif tt in ("TRF", "ADJ"):
            r["POST_TXN_BALANCE"] = S.add(bal, amt)
        else:
            r["POST_TXN_BALANCE"] = bal
        r["RISK_RATING"] = g("RISK_RATING")                                 # line 124
        out.append(r)
    out.sort(key=lambda r: (r["ACCOUNT_ID"], r["TRANSACTION_DATE"], r["TRANSACTION_ID"]))  # line 128
    return out


def running_balance(enriched: List[Row]) -> List[Row]:
    """DATA step lines 137-154: BY-group first./RETAIN running balance."""
    out: List[Row] = []
    running = None                                                          # line 141 retain
    prev_acct = object()
    for src in enriched:                                                    # lines 138-139
        pdv = dict(src)
        if src["ACCOUNT_ID"] != prev_acct:                                  # first.ACCOUNT_ID, lines 143-144
            running = pdv["PRE_TXN_BALANCE"]
        tt, amt = pdv["TRANSACTION_TYPE"], pdv["TRANSACTION_AMOUNT"]
        if tt in ("DEP", "INT", "REF", "REV"):                              # lines 146-151
            running = S.add(running, amt)
        elif tt in ("WDR", "PMT", "FEE", "CHG"):
            running = S.sub(running, S.sas_abs(amt))
        elif tt in ("TRF", "ADJ"):
            running = S.add(running, amt)
        pdv["RUNNING_BALANCE"] = running
        prev_acct = src["ACCOUNT_ID"]
        out.append(pdv)
    return out


def txn_stats(history: List[Row], txn_date: dt.date) -> Dict[str, Row]:
    """PROC SQL lines 159-170 over the *pre-append* CURATED.DAILY_TRANSACTIONS."""
    cutoff = S.intnx_day(txn_date, -90)                                     # line 167
    groups: Dict[str, List[S.Num]] = {}
    for h in history:                                                       # observation order
        if h["TRANSACTION_DATE"] is not None and h["TRANSACTION_DATE"] >= cutoff:
            groups.setdefault(h["ACCOUNT_ID"], []).append(S.sas_abs(h["TRANSACTION_AMOUNT"]))
    return {k: {"ACCOUNT_ID": k,
                "AVG_TXN_AMT": S.sas_mean(v),                              # line 163
                "STD_TXN_AMT": S.sas_std(v),                               # line 164 (sample std, n-1)
                "TXN_COUNT": float(len(v))}                                # line 165 count(*)
            for k, v in groups.items()}


def anomalies(with_balance: List[Row], stats: Dict[str, Row]) -> List[Row]:
    """PROC SQL lines 172-197. Comparisons follow SAS missing-sorts-low rules:
    `. < 0` is TRUE and `x > .` is TRUE, so orphan accounts (missing balances)
    classify as OVERDRAFT / LARGE_WITHDRAWAL before ORPHAN_ACCOUNT (AMB-06)."""
    out: List[Row] = []
    for e in with_balance:
        s = stats.get(e["ACCOUNT_ID"])                                      # lines 193-194 left join
        r = dict(e)                                                         # line 175 e.*
        r["AVG_TXN_AMT"] = s["AVG_TXN_AMT"] if s else None                  # line 176
        r["STD_TXN_AMT"] = s["STD_TXN_AMT"] if s else None                  # line 177
        if S.gt(r["STD_TXN_AMT"], 0):                                       # lines 178-182
            r["Z_SCORE"] = S.div(S.sub(S.sas_abs(e["TRANSACTION_AMOUNT"]), r["AVG_TXN_AMT"]),
                                 r["STD_TXN_AMT"])
        else:
            r["Z_SCORE"] = None
        if S.gt(r["Z_SCORE"], 3):                                           # lines 183-191
            r["ANOMALY_TYPE"] = "HIGH_AMOUNT"
        elif S.lt(e["RUNNING_BALANCE"], 0):
            r["ANOMALY_TYPE"] = "OVERDRAFT"
        elif e["TRANSACTION_TYPE"] == "WDR" and S.gt(S.sas_abs(e["TRANSACTION_AMOUNT"]),
                                                      S.mul(e["PRE_TXN_BALANCE"], 0.9)):
            r["ANOMALY_TYPE"] = "LARGE_WITHDRAWAL"
        elif S.missing(e["CUSTOMER_ID"]):
            r["ANOMALY_TYPE"] = "ORPHAN_ACCOUNT"
        else:
            r["ANOMALY_TYPE"] = ""
        if r["ANOMALY_TYPE"] != "":                                         # line 195 having
            out.append(r)
    return out


def run(libs: Dict[str, List[Row]], daily_accounts: List[Row], txn_date: dt.date) -> Dict[str, List[Row]]:
    feed = libs["RAW_BANK.TXN_FEED_" + S.yymmddn8(txn_date)]                # line 25 txn_ds
    history = libs["CURATED.DAILY_TRANSACTIONS"]
    valid, rejected, rejected_full = validate(feed, txn_date)
    enriched = enrich(valid, daily_accounts)
    with_bal = running_balance(enriched)
    stats = txn_stats(history, txn_date)                                    # Step 4 runs before Step 5 append
    anom = anomalies(with_bal, stats)

    # lines 207-209: PROC APPEND ... FORCE. Variables of DATA= that are not in
    # BASE= are dropped, so the curated table keeps only its 10 columns (AMB-03).
    appended = list(history) + [{c: r[c] for c in FEED_COLS} for r in with_bal]

    # lines 222-225
    balances = [{c: r[c] for c in ("ACCOUNT_ID", "TRANSACTION_DATE", "TRANSACTION_ID", "RUNNING_BALANCE")}
                for r in with_bal]
    return {"CURATED.DAILY_TRANSACTIONS": appended,
            "CURATED.TXN_ANOMALIES": anom,                                  # lines 214-216 (base absent -> full structure)
            "CURATED.RUNNING_BALANCES": balances,
            "WORK.TXN_REJECTED": rejected,
            "ALT.TXN_REJECTED_WITH_REASON": rejected_full,
            "ALT.DAILY_TRANSACTIONS_APPENDED_WIDE": with_bal}
