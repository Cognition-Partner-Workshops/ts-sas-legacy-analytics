"""
Variable existence check utility.

Migrated from: Macro/varexist.sas
Original author: Scott Bass (27APR2007)

Check for the existence of a column in a DataFrame, optionally returning
column attributes (dtype, position, etc.).
"""

from __future__ import annotations

from typing import Any, Optional, Union

import pandas as pd


def varexist(
    df: pd.DataFrame,
    var: str,
    info: Optional[str] = None,
) -> Union[bool, int, str, Any]:
    """
    Check for the existence of a column, optionally returning attributes.

    Parameters
    ----------
    df : pd.DataFrame
        Source DataFrame.
    var : str
        Column name to check.
    info : str, optional
        If provided, return a specific attribute instead of a boolean.
        Valid values:
        - ``"num"`` : column position (1-indexed)
        - ``"len"`` : max string length or dtype itemsize
        - ``"type"`` : ``"N"`` for numeric, ``"C"`` for character/object
        - ``"label"`` : column label (from attrs if available)
        - ``"dtype"`` : pandas dtype as string

    Returns
    -------
    bool or int or str
        - If ``info`` is None: True if column exists, False otherwise.
        - If ``info`` is specified: the requested attribute value.
        - Returns 0 or False if column does not exist.
    """
    if not isinstance(df, pd.DataFrame):
        return False if info is None else 0

    if var not in df.columns:
        return False if info is None else 0

    if info is None:
        return True

    info_upper = info.upper()

    if info_upper == "NUM":
        return list(df.columns).index(var) + 1

    if info_upper == "LEN":
        dtype = df[var].dtype
        if dtype == object or pd.api.types.is_string_dtype(dtype):
            non_null = df[var].dropna()
            if len(non_null) == 0:
                return 0
            return int(non_null.astype(str).str.len().max())
        return df[var].dtype.itemsize

    if info_upper == "TYPE":
        dtype = df[var].dtype
        if dtype == object or pd.api.types.is_string_dtype(dtype):
            return "C"
        return "N"

    if info_upper == "LABEL":
        labels = df.attrs.get("labels", {})
        return labels.get(var, var)

    if info_upper == "DTYPE":
        return str(df[var].dtype)

    return 0
