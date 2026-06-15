"""Python equivalent of Macro/transpose.sas.

SAS ``%transpose`` wraps ``PROC TRANSPOSE``: it optionally sorts the input
by *by* variables, then pivots *var* columns into rows (or, when *id* is
given, into columns named after the formatted values of the id variable).

This module reproduces that behaviour with :func:`pandas.DataFrame.melt`
(long-form transpose) and :func:`pandas.DataFrame.pivot_table`
(wide-form transpose when *id* is supplied).
"""

from __future__ import annotations

from typing import Optional, Sequence

import pandas as pd


def transpose(
    data: pd.DataFrame,
    *,
    by: Optional[Sequence[str]] = None,
    var: Optional[Sequence[str]] = None,
    id: Optional[str] = None,  # noqa: A002 — mirrors SAS parameter name
    id_label: Optional[str] = None,
    copy: Optional[Sequence[str]] = None,
    let: bool = False,
    prefix: Optional[str] = None,
    name: Optional[str] = "_NAME_",
    label: Optional[str] = "_LABEL_",
    col: Optional[Sequence[str]] = None,
    where: Optional[str] = None,
    sort: bool = True,
    notsorted: bool = False,
) -> pd.DataFrame:
    """Transpose *data*, mirroring SAS ``%transpose``.

    Parameters
    ----------
    data : DataFrame
        Input dataset.
    by : sequence of str, optional
        Grouping columns (``BY`` statement).
    var : sequence of str, optional
        Columns to transpose.  If *None*, all numeric columns are used.
    id : str, optional
        Column whose values become output column names (wide-form).
    id_label : str, optional
        Column whose values label the output columns (requires *id*).
    copy : sequence of str, optional
        Columns copied through without transposing.
    let : bool
        When *True* and *id* is specified, keep only the last occurrence
        per BY-group (SAS ``LET`` option).
    prefix : str, optional
        Prefix for generated value columns (default ``"COL"``).
    name : str or None
        Name for the column that stores original variable names
        (``_NAME_``).  *None* drops the column.
    label : str or None
        Name for the column that stores original variable labels
        (``_LABEL_``).  *None* drops the column.
    col : sequence of str, optional
        Rename the generated ``COL1 .. COLn`` columns.
    where : str, optional
        Pandas query expression applied to *data* before transposing.
    sort : bool
        Sort *data* by *by* columns before transposing (default *True*).
    notsorted : bool
        If *True*, skip sorting even when *by* is specified.

    Returns
    -------
    DataFrame
        Transposed dataset.
    """
    if id is not None and col is not None:
        raise ValueError("Only one of 'col' or 'id' may be specified, not both.")
    if id_label is not None and id is None:
        raise ValueError("'id_label' requires 'id' to also be specified.")

    df = data.copy()

    if where is not None:
        df = df.query(where)

    by = list(by) if by is not None else []
    if var is None:
        var = list(df.select_dtypes(include="number").columns.difference(by))
    else:
        var = list(var)

    if notsorted:
        sort = False
    if sort and by:
        df = df.sort_values(by).reset_index(drop=True)

    copy_cols = list(copy) if copy is not None else []

    # ---- wide-form transpose (ID= was specified) -------------------------
    if id is not None:
        aggfunc = "last" if let else "first"
        pivot = df.pivot_table(
            index=by or None,
            columns=id,
            values=var,
            aggfunc=aggfunc,
            sort=False,
        )
        # Flatten multi-level column index
        if isinstance(pivot.columns, pd.MultiIndex):
            pivot.columns = [
                f"{v}_{c}" if len(var) > 1 else str(c)
                for v, c in pivot.columns
            ]
        else:
            pivot.columns = [str(c) for c in pivot.columns]

        result = pivot.reset_index()

        if copy_cols:
            if by:
                copy_df = df.groupby(by, sort=False)[copy_cols].first().reset_index()
                result = result.merge(copy_df, on=by, how="left")
            else:
                for c in copy_cols:
                    result[c] = df[c].iat[0] if len(df) > 0 else None

        return result

    # ---- long-form transpose (default, no ID=) ----------------------------
    pfx = prefix if prefix else "COL"

    if by:
        groups = df.groupby(by, sort=False)
        parts: list[pd.DataFrame] = []
        for keys, group in groups:
            if not isinstance(keys, tuple):
                keys = (keys,)
            transposed = _transpose_group(
                group, by, var, pfx, copy_cols, name, label,
            )
            for i, b in enumerate(by):
                transposed.insert(i, b, keys[i])
            parts.append(transposed)
        result = pd.concat(parts, ignore_index=True)
    else:
        result = _transpose_group(df, by, var, pfx, copy_cols, name, label)

    # Rename COL# columns if requested
    if col is not None:
        rename_map: dict[str, str] = {}
        for i, new_name in enumerate(col, start=1):
            old_name = f"{pfx}{i}"
            if old_name in result.columns:
                rename_map[old_name] = new_name
        result = result.rename(columns=rename_map)

    return result


def _transpose_group(
    group: pd.DataFrame,
    by: list[str],
    var: list[str],
    prefix: str,
    copy_cols: list[str],
    name_col: Optional[str],
    label_col: Optional[str],
) -> pd.DataFrame:
    """Transpose a single BY-group, producing COL1..COLn columns."""
    vals = group[var].values  # shape (nobs, nvar)
    n_obs = vals.shape[0]

    rows: list[dict[str, object]] = []
    for j, v in enumerate(var):
        row: dict[str, object] = {}
        if name_col is not None:
            row[name_col] = v
        if label_col is not None:
            row[label_col] = v
        for i in range(n_obs):
            row[f"{prefix}{i + 1}"] = vals[i, j]
        rows.append(row)

    result = pd.DataFrame(rows)

    if copy_cols:
        for c in copy_cols:
            result[c] = group[c].iloc[0]

    return result
