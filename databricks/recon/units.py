"""Unit -> table map and column -> rule classification.

Source: docs/migration/ts-sas-legacy-analytics_P1_banking_core_analysis.md §6
(tables, keys, checks) and §3 (type mapping rules); .migration/03_recon_tolerances.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field

ROW_DIFF_TIER = 5_000_000  # full row-level diff at or below this size (03_recon_tolerances §economics)
SAMPLE_FRACTION = 0.01
SAMPLE_MIN_ROWS = 100_000

# Declared source volumes: .migration/05_progress.md §"Baseline manifest" (rows excl. header).
DECLARED_SOURCE_VOLUMES: dict[str, int] = {
    "cust_accounts": 487,
    "cust_demographics": 250,
    "bureau_scores": 500,
    "payment_history": 248,
    "collateral": 114,
    "loan_details": 248,
    "daily_rates": 455,
    "txn_feed_20240131": 622,
    "daily_transactions_hist": 18293,
}

RATING_EDGES = (0.005, 0.01, 0.03, 0.07, 0.15, 0.30)  # ML-7
EDGE_EPS = 1e-9


ACCT_EXCEPTIONS_COLUMNS: tuple[str, ...] = (
    "account_id", "customer_id", "account_type", "account_status", "open_date", "close_date",
    "current_balance", "available_balance", "credit_limit", "interest_rate", "branch_id",
    "officer_id", "last_activity_date", "first_name", "last_name", "ssn_hash", "date_of_birth",
    "customer_segment", "risk_rating", "region_code", "primary_email", "phone_number",
    "acct_age_months", "days_inactive", "utilization_pct", "dormancy_flag", "high_balance_flag",
    "snapshot_date", "load_timestamp",
)


@dataclass(frozen=True)
class TableSpec:
    name: str
    schema: str
    keys: tuple[str, ...]
    # explicit column -> rule overrides; everything else is classified by name pattern
    column_rules: dict[str, str] = field(default_factory=dict)
    # T-9 group-by column (reject_reason / exception_type); None when the rule does not apply
    t9_group: str | None = None
    # Full-row multiset comparison (DEC-015 (a)): every column is part of the key and
    # duplicate rows are matched by multiplicity. `distinct_keys` bounds the T-8
    # COUNT DISTINCT probes for such tables; `t9_unexercised` carries the citation
    # emitted as the T-9 DECLARED-UNEXERCISED verdict.
    multiset: bool = False
    distinct_keys: tuple[str, ...] | None = None
    t9_unexercised: str | None = None
    ml: bool = False
    # ML-8 debug table (target side `<name>` ; reference `<name>.csv`)
    woe_debug: str | None = None
    xlsx: bool = False  # T-12: existence + 4 sheets when --xlsx-path is given


UNITS: dict[str, tuple[TableSpec, ...]] = {
    "U1": (
        TableSpec(
            "cust_accounts_daily",
            "sas_silver",
            ("account_id", "snapshot_date"),
            {"utilization_pct": "T-5", "load_timestamp": "T-7"},
        ),
        TableSpec(
            "acct_exceptions",
            "sas_silver",
            ACCT_EXCEPTIONS_COLUMNS,
            # AMB-05: OUTPUT precedes the SNAPSHOT_DATE/LOAD_TIMESTAMP assignment, so both are
            # literally missing on every exception row -> exact (T-3), not run-time (T-7).
            {"utilization_pct": "T-5", "snapshot_date": "T-3", "load_timestamp": "T-3"},
            multiset=True,
            distinct_keys=("account_id",),
            t9_unexercised=(
                "DEC-015 (a): literal SAS output has no EXCEPTION_TYPE/EXCEPTION_CODE column "
                "(the DROP statement applies to every OUTPUT data set, AMB-01/AMB-12); "
                "T-9 per-type count has no grouping column and is declared unexercised. "
                "Full-row multiset match (T-2) is the substitute. Owner: requester; severity medium; "
                "gate: close before STOP E via REQ-05 or production-schema export."
            ),
        ),
    ),
    "U2": (
        TableSpec(
            "daily_transactions",
            "sas_silver",
            ("transaction_id",),
            {"running_balance": "T-4"},
        ),
        TableSpec(
            "running_balances",
            "sas_silver",
            ("account_id", "transaction_date", "transaction_id"),
        ),
        TableSpec(
            "txn_anomalies",
            "sas_silver",
            ("transaction_id",),
            {
                "z_score": "T-6",
                "avg_txn_amt": "T-6",
                "std_txn_amt": "T-6",
                "anomaly_type": "T-3",
            },
        ),
        TableSpec(
            "txn_rejected",
            "sas_silver",
            ("transaction_id",),
            t9_group="reject_reason",
        ),
    ),
    "U3": (
        TableSpec(
            "risk_scores",
            "sas_silver",
            ("account_id", "score_date"),
            {
                "new_risk_rating": "ML-1",
                "pd": "ML-2",
                "lgd": "ML-3",
                "ead": "ML-3",
                "expected_loss": "ML-4",
                "score_timestamp": "T-7",
                # carried bureau/payment/collateral columns (pre-stated): integers and
                # DECIMAL/DATE are T-3 exact; the two source DOUBLEs are T-5 so T-8 sums
                # are not judged on double-accumulation ulps (U1 interest_rate lesson)
                "fico_score": "T-3",
                "vantage_score": "T-3",
                "bureau_inqs_6mo": "T-3",
                "bureau_trades_open": "T-3",
                "bureau_derogs": "T-3",
                "bureau_oldest_trade_mo": "T-3",
                "pmt_ontime_12mo": "T-3",
                "pmt_late_30_12mo": "T-3",
                "pmt_late_60_12mo": "T-3",
                "pmt_late_90_12mo": "T-3",
                "max_days_past_due_ever": "T-3",
                "months_since_last_dpd": "T-3",
                "collateral_value": "T-3",
                "last_appraisal_date": "T-3",
                "model_id": "T-3",
                "bureau_util_pct": "T-5",
                "avg_pmt_ratio_12mo": "T-5",
            },
            ml=True,
            woe_debug="risk_scores_woe_debug",
        ),
        TableSpec(
            "risk_migration",
            "sas_silver",
            ("account_id", "score_date"),
            {
                "migration_direction": "ML-6",
                "prev_rating": "ML-6",
                "curr_rating": "ML-6",
                "pd": "ML-2",  # carried from SCORED; default would be T-3 exact on a double
                "expected_loss": "ML-4",
            },
            ml=True,
        ),
        TableSpec(
            "risk_summary",
            "sas_gold",
            ("account_type", "new_risk_rating"),
            {
                "avg_pd": "T-5",
                "avg_lgd": "T-5",
                "total_ead": "T-4",
                "total_el": "T-4",
            },
        ),
    ),
    "U4": (
        TableSpec(
            "monthly_rwa",
            "sas_gold",
            ("report_month", "account_type", "customer_segment"),
            {"n_accounts": "T-3", "total_exposure": "T-4", "rwa": "T-4"},
            xlsx=True,
        ),
        TableSpec(
            "delinquency_aging",
            "sas_gold",
            ("report_month", "account_type", "region_code", "delinq_bucket"),
        ),
        TableSpec(
            "llp_coverage",
            "sas_gold",
            ("report_month", "account_type"),
            {"coverage_pct": "T-5", "npl_coverage_pct": "T-5"},
        ),
        TableSpec(
            "capital_adequacy",
            "sas_gold",
            ("report_month",),
        ),
    ),
    "U5": (
        TableSpec(
            "archive_batch_history",
            "sas_silver",
            ("batch_id", "step_num"),
            {
                "start_time": "T-7",
                "end_time": "T-7",
                "duration": "T-7",
                "status": "T-3",
                "step_name": "T-3",
            },
        ),
    ),
}

_T7_SUFFIXES = ("_timestamp", "_dttm", "_time")
_T6_NAMES = {"z_score", "avg_txn_amt", "std_txn_amt"}
_T5_TOKENS = ("_pct", "_ratio", "ltv", "nim", "interest_rate", "avg_pd", "avg_lgd")
_T4_TOKENS = (
    "_balance",
    "_amount",
    "_amt",
    "ead",
    "expected_loss",
    "rwa",
    "capital_",
    "total_",
    "gross_loans",
    "npl_balance",
    "cet1_capital",
    "credit_limit",
    "_exposure",
    "_el",
)


def classify_column(spec: TableSpec, column: str) -> str:
    """Return the tolerance rule id governing `column` (analysis §3 mapping rules)."""
    col = column.lower()
    if col in spec.column_rules:
        return spec.column_rules[col]
    if col in spec.keys and not spec.multiset:  # a multiset key is the whole row; §3 rules apply
        return "T-3"
    if col.endswith(_T7_SUFFIXES) or col == "duration":
        return "T-7"
    if col in _T6_NAMES:
        return "T-6"
    if any(tok in col for tok in _T5_TOKENS):
        return "T-5"
    if any(col == tok or col.endswith(tok) or col.startswith(tok) for tok in _T4_TOKENS):
        return "T-4"
    return "T-3"


def tables_for(unit: str) -> tuple[TableSpec, ...]:
    if unit not in UNITS:
        raise SystemExit(f"unknown unit {unit!r}; expected one of {', '.join(UNITS)}")
    return UNITS[unit]
