"""
Variable list utility.

Migrated from: Macro/varlist.sas
Original author: Scott Bass (06DEC2007)

Returns a space-separated list of column names from a DataFrame.
"""

from __future__ import annotations

import pandas as pd


def varlist(df: pd.DataFrame, upcase: bool = False) -> str:
    """
    Return a space-separated list of column names from a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    upcase : bool
        If True, uppercase all column names. Default False.

    Returns
    -------
    str
        Space-separated column names.

    Raises
    ------
    TypeError
        If df is not a DataFrame.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected a DataFrame, got {type(df).__name__}")

    names = list(df.columns)
    if upcase:
        names = [str(n).upper() for n in names]
    else:
        names = [str(n) for n in names]

    return " ".join(names)
