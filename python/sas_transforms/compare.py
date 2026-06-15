"""Python equivalent of Macro/compare.sas.

SAS ``%compare`` wraps ``PROC COMPARE``: it compares two datasets (or two
libraries of datasets), reporting on variable and observation differences.

This module provides:

* **Dataset comparison** — row-level and column-level diff between two
  DataFrames, with optional BY-key identification and configurable
  numeric tolerance.
* **Library comparison** — given two ``dict[str, DataFrame]`` mappings
  (analogous to SAS librefs), report which members are matched/unmatched
  and compare matched members recursively.
"""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field
from typing import Optional, Sequence, Union

import numpy as np
import pandas as pd


@dataclass
class CompareResult:
    """Container for dataset-level comparison output."""

    base_only_cols: list[str] = field(default_factory=list)
    comp_only_cols: list[str] = field(default_factory=list)
    common_cols: list[str] = field(default_factory=list)
    base_only_rows: pd.DataFrame = field(default_factory=pd.DataFrame)
    comp_only_rows: pd.DataFrame = field(default_factory=pd.DataFrame)
    value_diffs: pd.DataFrame = field(default_factory=pd.DataFrame)
    equal: bool = True


@dataclass
class LibraryCompareResult:
    """Container for library-level comparison output."""

    base_only_members: list[str] = field(default_factory=list)
    comp_only_members: list[str] = field(default_factory=list)
    matched_members: list[str] = field(default_factory=list)
    member_results: dict[str, CompareResult] = field(default_factory=dict)


def compare(
    base: Union[pd.DataFrame, dict[str, pd.DataFrame]],
    comp: Union[pd.DataFrame, dict[str, pd.DataFrame]],
    *,
    by: Optional[Sequence[str]] = None,
    filter: Optional[str] = None,  # noqa: A002
    criterion: float = 1e-6,
    method: str = "exact",
    maxprint: int = 50,
) -> Union[CompareResult, LibraryCompareResult]:
    """Compare *base* and *comp*, mirroring SAS ``%compare``.

    Parameters
    ----------
    base, comp : DataFrame or dict of DataFrames
        When both are DataFrames a dataset comparison is performed.
        When both are dicts (member-name → DataFrame) a library
        comparison is performed.
    by : sequence of str, optional
        Key columns that uniquely identify a row.  Used for sorted
        merge comparison.  Ignored for library comparisons (but passed
        through to recursive dataset comparisons).
    filter : str, optional
        Regex pattern to select members in a library comparison.
    criterion : float
        Tolerance for numeric equality (default ``1e-6``).
    method : str
        ``"exact"`` (default), ``"absolute"``, ``"relative"``, or
        ``"percent"`` — mirrors SAS METHOD= option.
    maxprint : int
        Maximum number of value differences to retain in
        :attr:`CompareResult.value_diffs`.

    Returns
    -------
    CompareResult or LibraryCompareResult
    """
    if isinstance(base, dict) and isinstance(comp, dict):
        return _compare_libraries(base, comp, by=by, filter=filter,
                                  criterion=criterion, method=method,
                                  maxprint=maxprint)

    if isinstance(base, pd.DataFrame) and isinstance(comp, pd.DataFrame):
        return _compare_datasets(base, comp, by=by, criterion=criterion,
                                 method=method, maxprint=maxprint)

    raise TypeError("base and comp must both be DataFrames or both be dicts")


def _compare_libraries(
    base: dict[str, pd.DataFrame],
    comp: dict[str, pd.DataFrame],
    *,
    by: Optional[Sequence[str]],
    filter: Optional[str],
    criterion: float,
    method: str,
    maxprint: int,
) -> LibraryCompareResult:
    base_names = set(base)
    comp_names = set(comp)

    if filter is not None:
        rx = re.compile(filter, re.IGNORECASE)
        base_names = {n for n in base_names if rx.search(n)}

    matched = sorted(base_names & comp_names)
    result = LibraryCompareResult(
        base_only_members=sorted(base_names - comp_names),
        comp_only_members=sorted(comp_names - base_names),
        matched_members=matched,
    )

    for name in matched:
        result.member_results[name] = _compare_datasets(
            base[name], comp[name], by=by, criterion=criterion,
            method=method, maxprint=maxprint,
        )

    return result


def _compare_datasets(
    base: pd.DataFrame,
    comp: pd.DataFrame,
    *,
    by: Optional[Sequence[str]],
    criterion: float,
    method: str,
    maxprint: int,
) -> CompareResult:
    result = CompareResult()

    base_cols = set(base.columns)
    comp_cols = set(comp.columns)
    result.base_only_cols = sorted(base_cols - comp_cols)
    result.comp_only_cols = sorted(comp_cols - base_cols)
    result.common_cols = sorted(base_cols & comp_cols)

    by_list = list(by) if by else []

    if by_list:
        base_s = base.sort_values(by_list).reset_index(drop=True)
        comp_s = comp.sort_values(by_list).reset_index(drop=True)

        # Warn if BY keys are not unique — mirrors SAS PROC COMPARE warning
        if base_s.duplicated(subset=by_list).any() or comp_s.duplicated(subset=by_list).any():
            warnings.warn(
                "BY variables do not uniquely identify observations. "
                "Duplicate keys may produce unreliable comparison results. "
                "This mirrors the SAS WARNING for non-unique BY keys.",
                UserWarning,
                stacklevel=3,
            )

        # De-duplicate before merge to prevent row explosion
        base_keys = base_s[by_list].drop_duplicates()
        comp_keys = comp_s[by_list].drop_duplicates()

        merged = base_keys.merge(
            comp_keys, on=by_list, how="outer", indicator=True,
        )
        base_only_keys = merged.loc[merged["_merge"] == "left_only", by_list]
        comp_only_keys = merged.loc[merged["_merge"] == "right_only", by_list]

        result.base_only_rows = base_s.merge(base_only_keys, on=by_list)
        result.comp_only_rows = comp_s.merge(comp_only_keys, on=by_list)

        both_keys = merged.loc[merged["_merge"] == "both", by_list]
        base_common = base_s.merge(both_keys, on=by_list).drop_duplicates(subset=by_list, keep="first")
        comp_common = comp_s.merge(both_keys, on=by_list).drop_duplicates(subset=by_list, keep="first")
        base_common = base_common.reset_index(drop=True)
        comp_common = comp_common.reset_index(drop=True)
    else:
        min_len = min(len(base), len(comp))
        base_common = base.iloc[:min_len].reset_index(drop=True)
        comp_common = comp.iloc[:min_len].reset_index(drop=True)
        if len(base) > min_len:
            result.base_only_rows = base.iloc[min_len:].reset_index(drop=True)
        if len(comp) > min_len:
            result.comp_only_rows = comp.iloc[min_len:].reset_index(drop=True)

    compare_cols = [c for c in result.common_cols if c not in by_list]
    diffs: list[dict[str, object]] = []

    for col_name in compare_cols:
        if len(diffs) >= maxprint:
            break
        b_vals = base_common[col_name]
        c_vals = comp_common[col_name]

        for i in range(len(b_vals)):
            if len(diffs) >= maxprint:
                break
            bv, cv = b_vals.iat[i], c_vals.iat[i]
            if _values_differ(bv, cv, criterion, method):
                row_id = dict(zip(by_list, base_common[by_list].iloc[i])) if by_list else {"_ROW_": i}
                diffs.append({
                    **row_id,
                    "variable": col_name,
                    "base_value": bv,
                    "comp_value": cv,
                })

    result.value_diffs = pd.DataFrame(diffs) if diffs else pd.DataFrame()
    result.equal = (
        not result.base_only_cols
        and not result.comp_only_cols
        and result.base_only_rows.empty
        and result.comp_only_rows.empty
        and result.value_diffs.empty
    )
    return result


def _values_differ(bv: object, cv: object, criterion: float, method: str) -> bool:
    """Return *True* when *bv* and *cv* are considered different."""
    if bv is None and cv is None:
        return False
    if pd.isna(bv) and pd.isna(cv):
        return False
    if pd.isna(bv) or pd.isna(cv):
        return True
    # Non-numeric
    if not isinstance(bv, (int, float, np.integer, np.floating)):
        return bv != cv
    if not isinstance(cv, (int, float, np.integer, np.floating)):
        return bv != cv

    bv_f = float(bv)
    cv_f = float(cv)

    if method == "exact":
        return bv_f != cv_f
    elif method == "absolute":
        return abs(bv_f - cv_f) > criterion
    elif method == "relative":
        denom = max(abs(bv_f), abs(cv_f), 1e-15)
        return abs(bv_f - cv_f) / denom > criterion
    elif method == "percent":
        if bv_f == 0:
            return cv_f != 0
        return abs((bv_f - cv_f) / bv_f) * 100 > criterion
    return bv_f != cv_f
