"""W0-R self-checks: determinism, populations, keys, scoring ranges, running balance."""
import datetime as dt
import json
import os
import tempfile

import pandas as pd
import pytest
from reference_impl import run_all
from reference_impl.seeds import load_all, sha256

REF = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "reference"))
BUSINESS_DATE = dt.date(2024, 1, 31)
REPORT_MONTH = "202401"

# Seed manifest recorded in .migration/05_progress.md §"Baseline manifest"
SEED_SHA256 = {
    "curated/DAILY_TRANSACTIONS.csv": ("f31519447f5e2df2be283dc8dcf7c46e1fd3175ac235205abd97418739cbdbe5", 18293),
    "oracle_dw/BUREAU_SCORES.csv": ("989f8077cc84b3dfe3daf2a6fc5f5a995d49cd8e4a911831b4f3f6e9ffe5025c", 500),
    "oracle_dw/COLLATERAL.csv": ("fbdc1cf8b38d43e18c26a2e34b70616a19cf0637be1447f95a7d49f6b6b9bb6b", 114),
    "oracle_dw/CUST_ACCOUNTS.csv": ("30d762718cc7f15d7659f6734df28dbaf36532ebf5323a422ffeed49068c8b13", 487),
    "oracle_dw/CUST_DEMOGRAPHICS.csv": ("2050f727d3065926b7b3b047f6967150f16488d1acdfc20d384133b01019182b", 250),
    "oracle_dw/LOAN_DETAILS.csv": ("0eba231eb28d31ea2e4df7e0ee61e5b37f7e74fbcee5f6968627d0207730a1f7", 248),
    "oracle_dw/PAYMENT_HISTORY.csv": ("f745b79820420ca2ac870ae14992dde704d24e2e1e7942aebedd896f66c9f396", 248),
    "raw_bank/DAILY_RATES.csv": ("d61d8a5310a9c40530c07ef73bfed9b3e748a5a59fcc0a34581b7303b5490d6a", 455),
    "raw_bank/TXN_FEED_20240131.csv": ("0bebabbc3e4a8a4e799d51afccb2e0e1388bbce9b72ebc056b241f131c8e82b6", 622),
}


def read(name):
    return pd.read_csv(os.path.join(REF, f"{name}.csv"), dtype=str, keep_default_na=False)


@pytest.fixture(scope="module")
def manifest():
    with open(os.path.join(REF, "manifest.json")) as fh:
        return json.load(fh)


def test_seed_manifest_matches_progress_ledger(manifest):
    for rel, (sha, rows) in SEED_SHA256.items():
        p = os.path.join(run_all.DEFAULT_CSV_ROOT, rel)
        assert sha256(p) == sha, rel
        assert manifest["inputs"][f"Data/csv/{rel}"]["sha256"] == sha
        assert manifest["inputs"][f"Data/csv/{rel}"]["rows"] == rows
    assert manifest["inputs"]["Data/csv/raw_bank/DAILY_RATES.csv"]["used"] is False
    assert manifest["caveat"] == "reference-derived, not SAS-produced"


def test_regeneration_is_byte_identical(manifest):
    with tempfile.TemporaryDirectory() as tmp:
        m2 = run_all.generate(BUSINESS_DATE, REPORT_MONTH, run_all.DEFAULT_CSV_ROOT, tmp)
        for name, meta in manifest["outputs"].items():
            assert m2["outputs"][name]["sha256"] == meta["sha256"], name
            assert sha256(os.path.join(REF, name)) == meta["sha256"], name
        for name, meta in manifest["alternates"].items():
            assert m2["alternates"][name]["sha256"] == meta["sha256"], name


EXPECTED_ROWS = {
    "cust_accounts_daily": 466,       # 487 - 14 'C' - 7 'W'; all open_date <= 2024-01-31
    "daily_transactions": 18293 + 610,  # history + (622 feed - 12 rejects)
    "running_balances": 610,
    "txn_rejected": 12,
    "risk_scores": 236,               # MTG/AUTO/PERS/CC/LOC/HELC rows of the snapshot
    "capital_adequacy": 1,
    "archive_batch_history": 4,
}


@pytest.mark.parametrize("table,n", sorted(EXPECTED_ROWS.items()))
def test_row_counts_match_populations(table, n, manifest):
    assert len(read(table)) == n
    assert manifest["outputs"][f"{table}.csv"]["rows"] == n


def test_population_derivations():
    libs = load_all(run_all.DEFAULT_CSV_ROOT)
    acct = libs["ORA_DW.CUST_ACCOUNTS"]
    cust = {d["CUSTOMER_ID"] for d in libs["ORA_DW.CUST_DEMOGRAPHICS"]}
    expected = [a for a in acct if a["ACCOUNT_STATUS"] not in ("W", "C")
                and a["OPEN_DATE"] is not None and a["OPEN_DATE"] <= BUSINESS_DATE
                and a["CUSTOMER_ID"] in cust]
    assert len(read("cust_accounts_daily")) == len(expected) == 466
    scored = [a for a in expected if a["ACCOUNT_TYPE"] in ("MTG", "AUTO", "PERS", "CC", "LOC", "HELC")]
    assert len(read("risk_scores")) == len(scored) == 236
    assert len(libs["RAW_BANK.TXN_FEED_20240131"]) == 622
    assert len(read("running_balances")) + len(read("txn_rejected")) == 622


KEYS = {t: k for _, t, k in run_all.TABLES}


@pytest.mark.parametrize("table", sorted(k for k in KEYS if k not in ("acct_exceptions", "txn_rejected")))
def test_keys_unique_and_sorted(table):
    df = read(table)
    keys = KEYS[table]
    assert not df.duplicated(keys).any(), table
    assert (df[keys] != "").all().all(), f"{table}: blank key"
    rendered = df.to_dict("records")
    assert rendered == sorted(rendered, key=lambda r: run_all.sort_key(r, keys)), f"{table} not sorted"


def test_literal_exception_and_reject_tables():
    # AMB-01/02: DROP statement applies to both outputs -> no code/reason columns
    ex = read("acct_exceptions")
    assert "exception_code" not in ex.columns and len(ex) == 32
    assert (ex["snapshot_date"] == "").all() and (ex["load_timestamp"] == "").all()   # AMB-05
    rj = read("txn_rejected")
    assert "reject_reason" not in rj.columns and len(rj) == 12
    alt = pd.read_csv(os.path.join(REF, "alternates", "acct_exceptions__with_code.csv"), dtype=str)
    assert not alt.duplicated(["account_id", "exception_code"]).any()
    assert alt["exception_code"].value_counts().to_dict() == {"NO_RISK": 16, "HIGH_UTIL": 9, "NEG_BAL": 7}


def test_pd_in_open_unit_interval_and_bands():
    rs = read("risk_scores")
    p = rs["pd"].astype(float)
    assert ((p > 0) & (p < 1)).all()
    bands = rs["new_risk_rating"].astype(int)
    assert set(bands.unique()) <= set(range(1, 8))
    edges = [0.005, 0.01, 0.03, 0.07, 0.15, 0.30]
    for pdv, band in zip(p, bands):
        assert band == 1 + sum(pdv >= e for e in edges)
    lgd = rs["lgd"].astype(float)
    assert ((lgd >= 0) & (lgd <= 1)).all()
    assert (rs["score_timestamp"] == "2024-01-31T00:00:00").all()
    assert (rs["model_id"] == "CRM-2023-Q4-v2").all()


def test_running_balance_last_row_equals_prior_plus_signed_sum():
    rb = read("running_balances")
    daily = read("cust_accounts_daily").set_index("account_id")["current_balance"].astype(float)
    txns = read("daily_transactions")
    feed = txns[txns["transaction_id"].str.startswith("T")]          # appended feed rows (history is H*)
    assert len(feed) == 610
    plus = {"DEP", "INT", "REF", "REV", "TRF", "ADJ"}
    for acct, grp in feed.groupby("account_id"):
        amt = grp["transaction_amount"].astype(float)
        signed = sum(a if t in plus else -abs(a) for a, t in zip(amt, grp["transaction_type"]))
        last = rb[rb["account_id"] == acct].iloc[-1]["running_balance"]
        assert last != "", acct
        assert abs(float(last) - (daily[acct] + signed)) < 1e-6, acct
    assert set(rb["account_id"]).issubset(set(daily.index))


def test_anomaly_rules_and_std_missing_yields_no_zscore():
    an = read("txn_anomalies")
    assert set(an["anomaly_type"]) <= {"HIGH_AMOUNT", "OVERDRAFT", "LARGE_WITHDRAWAL", "ORPHAN_ACCOUNT"}
    z = an[an["anomaly_type"] == "HIGH_AMOUNT"]["z_score"].astype(float)
    assert (z > 3).all()
    od = an[an["anomaly_type"] == "OVERDRAFT"]
    assert (od["running_balance"].astype(float) < 0).all()
    assert (an[an["std_txn_amt"] == ""]["z_score"] == "").all()


def test_archive_batch_history_shape():
    bh = read("archive_batch_history")
    assert bh["batch_id"].unique().tolist() == ["BANK_20240131_000000"]
    assert bh["step_num"].tolist() == ["1", "2", "3", "4"]
    assert (bh["status"] == "PASS").all()
    assert (bh["start_time"] == "2024-01-31T00:00:00").all() and (bh["duration"] == "0").all()


def test_regulatory_tables_are_internally_consistent():
    rwa = read("monthly_rwa")
    cap = read("capital_adequacy").iloc[0]
    total = sum(float(x) for x in rwa["rwa"])
    assert abs(float(cap["total_rwa"]) - total) < 1e-6
    assert abs(float(cap["cet1_ratio"]) - 50000000 / total * 100) < 1e-6
    assert int(rwa["n_accounts"].astype(int).sum()) == 466            # left join, unique loan keys
    assert set(rwa[rwa["account_type"] == "MTG"]["risk_weight"]) == {"0.35", "0.5"}   # AMB-07 (seed: every MTG has LTV)
    da = read("delinquency_aging")
    assert int(da["n_accounts"].astype(int).sum()) == 236
    assert set(da["delinq_bucket"]) <= {"Current", "1-29", "30-59", "60-89", "90-119", "120-179", "180+", "Unknown"}
    llp = read("llp_coverage")
    assert llp["account_type"].tolist() == sorted(llp["account_type"])
