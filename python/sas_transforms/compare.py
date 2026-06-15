"""Python equivalent of Macro/compare.sas.

SAS macro signature:
    %compare(BASE=, COMP=, BY=, FILTER=, CHECKOBS=0,
             MAXPRINT=50,1000, CRITERION=.000001, METHOD=EXACT)

The SAS macro supports both dataset-level and library-level comparisons.
The Python translation focuses on the dataset comparison use-case, which is
the primary analytical function.  Library comparison is inherently a SAS
concept (libref); the ``compare`` helper accepts two dicts of DataFrames
to cover that use-case.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np
import pandas as pd


@dataclass
class CompareResult:
    """Structured result of a dataset comparison."""

    match: bool
    common_columns: list[str] = field(default_factory=list)
    base_only_columns: list[str] = field(default_factory=list)
    comp_only_columns: list[str] = field(default_factory=list)
    base_only_rows: pd.DataFrame = field(default_factory=pd.DataFrame)
    comp_only_rows: pd.DataFrame = field(default_factory=pd.DataFrame)
    value_diffs: pd.DataFrame = field(default_factory=pd.DataFrame)
    base_nobs: int = 0
    comp_nobs: int = 0

    def summary(self) -> str:
        """Human-readable summary mirroring PROC COMPARE output."""
        lines = [
            f"Base observations : {self.base_nobs}",
            f"Compare observations: {self.comp_nobs}",
            f"Common columns    : {len(self.common_columns)}",
            f"Base-only columns : {self.base_only_columns or '(none)'}",
            f"Comp-only columns : {self.comp_only_columns or '(none)'}",
            f"Base-only rows    : {len(self.base_only_rows)}",
            f"Comp-only rows    : {len(self.comp_only_rows)}",
            f"Value differences : {len(self.value_diffs)}",
            f"Datasets match    : {self.match}",
        ]
        return "\n".join(lines)


def compare_datasets(
    base: pd.DataFrame,
    comp: pd.DataFrame,
    *,
    by: Optional[Sequence[str]] = None,
    criterion: float = 1e-6,
    method: str = "exact",
) -> CompareResult:
    """Compare two DataFrames, mirroring SAS ``PROC COMPARE``.

    Parameters
    ----------
    base : DataFrame
        Base (reference) dataset.
    comp : DataFrame
        Comparison dataset.
    by : list[str], optional
        Key columns that uniquely identify rows.  When provided, the
        comparison is aligned on these keys (like SAS ``ID`` statement
        in PROC COMPARE).  Without *by*, rows are compared positionally.
    criterion : float
        Tolerance for numeric comparisons (default ``1e-6``).
    method : str
        ``"exact"`` (default) or ``"absolute"``.

    Returns
    -------
    CompareResult
    """
    result = CompareResult(
        match=True,
        base_nobs=len(base),
        comp_nobs=len(comp),
    )

    base_cols = set(base.columns)
    comp_cols = set(comp.columns)
    result.common_columns = sorted(base_cols & comp_cols)
    result.base_only_columns = sorted(base_cols - comp_cols)
    result.comp_only_columns = sorted(comp_cols - base_cols)

    if result.base_only_columns or result.comp_only_columns:
        result.match = False

    if by:
        by_list = list(by)
        base_sorted = base.sort_values(by_list).reset_index(drop=True)
        comp_sorted = comp.sort_values(by_list).reset_index(drop=True)

        merged = base_sorted.merge(
            comp_sorted,
            on=by_list,
            how="outer",
            indicator=True,
            suffixes=("_base", "_comp"),
        )

        base_only_mask = merged["_merge"] == "left_only"
        comp_only_mask = merged["_merge"] == "right_only"
        both_mask = merged["_merge"] == "both"

        if base_only_mask.any():
            result.base_only_rows = merged.loc[base_only_mask, by_list].reset_index(drop=True)
            result.match = False
        if comp_only_mask.any():
            result.comp_only_rows = merged.loc[comp_only_mask, by_list].reset_index(drop=True)
            result.match = False

        value_cols = [c for c in result.common_columns if c not in by_list]
        diff_records: list[dict] = []
        both_df = merged.loc[both_mask]
        for col in value_cols:
            bcol = f"{col}_base"
            ccol = f"{col}_comp"
            if bcol not in both_df.columns or ccol not in both_df.columns:
                continue
            bvals = both_df[bcol]
            cvals = both_df[ccol]
            if _is_numeric(bvals) and _is_numeric(cvals):
                ne = _numeric_ne(bvals, cvals, criterion, method)
            else:
                ne = bvals.astype(str) != cvals.astype(str)
            if ne.any():
                for idx in both_df.index[ne]:
                    rec: dict = {k: merged.at[idx, k] for k in by_list}
                    rec["_VAR_"] = col
                    rec["_BASE_"] = merged.at[idx, bcol]
                    rec["_COMP_"] = merged.at[idx, ccol]
                    diff_records.append(rec)

        if diff_records:
            result.value_diffs = pd.DataFrame(diff_records)
            result.match = False
    else:
        min_rows = min(len(base), len(comp))
        if len(base) != len(comp):
            result.match = False
            if len(base) > len(comp):
                result.base_only_rows = base.iloc[min_rows:].reset_index(drop=True)
            else:
                result.comp_only_rows = comp.iloc[min_rows:].reset_index(drop=True)

        diff_records = []
        for col in result.common_columns:
            bcol = base[col].iloc[:min_rows].reset_index(drop=True)
            ccol = comp[col].iloc[:min_rows].reset_index(drop=True)
            if _is_numeric(bcol) and _is_numeric(ccol):
                ne = _numeric_ne(bcol, ccol, criterion, method)
            else:
                ne = bcol.astype(str) != ccol.astype(str)
            if ne.any():
                for pos in bcol.index[ne]:
                    diff_records.append({
                        "_OBS_": pos + 1,
                        "_VAR_": col,
                        "_BASE_": bcol.iloc[pos],
                        "_COMP_": ccol.iloc[pos],
                    })

        if diff_records:
            result.value_diffs = pd.DataFrame(diff_records)
            result.match = False

    return result


def compare(
    base: dict[str, pd.DataFrame] | pd.DataFrame,
    comp: dict[str, pd.DataFrame] | pd.DataFrame,
    *,
    by: Optional[Sequence[str]] = None,
    filter_pattern: Optional[str] = None,
    criterion: float = 1e-6,
    method: str = "exact",
) -> dict[str, CompareResult] | CompareResult:
    """Compare datasets or libraries (dicts of DataFrames).

    When *base* and *comp* are plain DataFrames, delegates to
    :func:`compare_datasets`.  When they are dicts (keyed by dataset
    name), mirrors the SAS library comparison: reports which datasets
    exist in each library, then compares matching datasets.

    Parameters
    ----------
    base, comp : DataFrame or dict[str, DataFrame]
    by : list[str], optional
    filter_pattern : str, optional
        Regex pattern to limit which datasets in a library comparison
        are processed.
    criterion : float
    method : str

    Returns
    -------
    CompareResult (dataset mode) or dict[str, CompareResult] (library mode)
    """
    if isinstance(base, pd.DataFrame) and isinstance(comp, pd.DataFrame):
        return compare_datasets(base, comp, by=by, criterion=criterion,
                                method=method)

    if not isinstance(base, dict) or not isinstance(comp, dict):
        raise TypeError("base and comp must both be DataFrames or both be dicts")

    import re as _re

    base_names = set(base.keys())
    comp_names = set(comp.keys())

    if filter_pattern:
        pat = _re.compile(filter_pattern, _re.IGNORECASE)
        base_names = {n for n in base_names if pat.search(n)}

    common = base_names & comp_names
    results: dict[str, CompareResult] = {}
    for name in sorted(common):
        results[name] = compare_datasets(
            base[name], comp[name], by=by, criterion=criterion, method=method,
        )
    return results


# ── helpers ──────────────────────────────────────────────────────────

def _is_numeric(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series)


def _numeric_ne(
    a: pd.Series, b: pd.Series, criterion: float, method: str,
) -> pd.Series:
    a_num = pd.to_numeric(a, errors="coerce")
    b_num = pd.to_numeric(b, errors="coerce")
    if method.lower() == "exact":
        return (a_num != b_num) & ~(a_num.isna() & b_num.isna())
    diff = (a_num - b_num).abs()
    return (diff > criterion) & ~(a_num.isna() & b_num.isna())
