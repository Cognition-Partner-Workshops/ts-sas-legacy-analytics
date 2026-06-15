"""Python equivalent of Macro/transpose.sas.

SAS macro signature (simplified):
    %transpose(DATA=, OUT=, BY=, VAR=, PREFIX=, SORT=Y, NOTSORTED=N,
               ID=, IDLABEL=, LET=, COPY=, WHERE=, FORMAT=, LBL=,
               COL=, NAME=_NAME_, LABEL=_LABEL_)

Python signature preserves the same logical parameters as keyword arguments.
"""

from __future__ import annotations

from typing import Optional, Sequence

import pandas as pd


def transpose(
    data: pd.DataFrame,
    *,
    by: Optional[Sequence[str]] = None,
    var: Optional[Sequence[str]] = None,
    id_col: Optional[str] = None,
    sort: bool = True,
    copy: Optional[Sequence[str]] = None,
    name: Optional[str] = "_NAME_",
    label: Optional[str] = "_LABEL_",
    col: Optional[Sequence[str]] = None,
    where: Optional[str] = None,
) -> pd.DataFrame:
    """Transpose *data*, mirroring SAS ``PROC TRANSPOSE``.

    Parameters
    ----------
    data : DataFrame
        Input dataset.
    by : list[str], optional
        Grouping columns (equivalent to SAS ``BY`` statement).
    var : list[str], optional
        Columns to transpose.  If *None*, all numeric columns are used.
    id_col : str, optional
        Column whose values become output column names (SAS ``ID``).
    sort : bool
        Sort by *by* columns before transposing (default ``True``).
    copy : list[str], optional
        Columns copied through without transposing.
    name : str or None
        Name for the ``_NAME_`` column.  Pass *None* to drop it.
    label : str or None
        Name for the ``_LABEL_`` column.  Pass *None* to drop it.
    col : list[str], optional
        Rename the transposed value columns (``COL1``, ``COL2``, …).
    where : str, optional
        A pandas query expression applied to *data* before transposing.

    Returns
    -------
    DataFrame
    """
    df = data.copy()

    if where is not None:
        df = df.query(where)

    if var is None:
        var = list(df.select_dtypes(include="number").columns)

    if by is not None and sort:
        df = df.sort_values(list(by)).reset_index(drop=True)

    if id_col is not None:
        return _transpose_with_id(df, by=by, var=var, id_col=id_col)

    return _transpose_simple(df, by=by, var=var, copy=copy, name=name,
                             label=label, col=col)


def _transpose_simple(
    df: pd.DataFrame,
    *,
    by: Optional[Sequence[str]],
    var: Sequence[str],
    copy: Optional[Sequence[str]],
    name: Optional[str],
    label: Optional[str],
    col: Optional[Sequence[str]],
) -> pd.DataFrame:
    """Core transpose without an ID column (COL1..COLn output)."""
    if by:
        groups = df.groupby(list(by), sort=False)
    else:
        groups = [(None, df)]

    rows: list[dict] = []
    for key, grp in groups:
        by_vals: dict = {}
        if by:
            if not isinstance(key, tuple):
                key = (key,)
            by_vals = dict(zip(by, key))

        copy_vals: dict = {}
        if copy:
            copy_vals = {c: grp[c].iloc[0] for c in copy}

        for v in var:
            row: dict = {}
            row.update(by_vals)
            if name is not None:
                row[name] = v
            if label is not None:
                row[label] = v
            row.update(copy_vals)
            values = grp[v].tolist()
            for idx, val in enumerate(values, start=1):
                col_name = f"COL{idx}"
                row[col_name] = val
            rows.append(row)

    result = pd.DataFrame(rows)

    if col is not None:
        rename_map: dict[str, str] = {}
        for idx, new_name in enumerate(col, start=1):
            old = f"COL{idx}"
            if old in result.columns:
                rename_map[old] = new_name
        result = result.rename(columns=rename_map)

    return result.reset_index(drop=True)


def _transpose_with_id(
    df: pd.DataFrame,
    *,
    by: Optional[Sequence[str]],
    var: Sequence[str],
    id_col: str,
) -> pd.DataFrame:
    """Transpose using an ID column (pivot wider)."""
    index_cols = list(by) if by else None

    if len(var) == 1:
        if index_cols:
            result = df.pivot_table(
                index=index_cols, columns=id_col, values=var[0],
                aggfunc="last",
            ).reset_index()
        else:
            result = df.pivot_table(
                columns=id_col, values=var[0], aggfunc="last",
            ).reset_index(drop=True)
        result.columns.name = None
    else:
        pieces: list[pd.DataFrame] = []
        for v in var:
            if index_cols:
                piece = df.pivot_table(
                    index=index_cols, columns=id_col, values=v,
                    aggfunc="last",
                ).reset_index()
            else:
                piece = df.pivot_table(
                    columns=id_col, values=v, aggfunc="last",
                ).reset_index(drop=True)
            piece.columns.name = None
            pieces.append(piece)
        result = pd.concat(pieces, ignore_index=True)

    return result
