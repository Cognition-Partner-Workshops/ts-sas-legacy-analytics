"""
Number of observations utility.

Migrated from: Macro/nobs.sas
Original author: Scott Bass (01MAY2006)

Returns the number of rows in a DataFrame, with optional filtering.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd


def nobs(df: pd.DataFrame, where: Optional[str] = None) -> int:
    """
    Return the number of observations (rows) in a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    where : str, optional
        A pandas query string to filter before counting.
        Example: ``"x > 10"``

    Returns
    -------
    int
        Number of rows (after filtering, if applicable).

    Raises
    ------
    TypeError
        If df is not a DataFrame.
    ValueError
        If the where clause is invalid.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected a DataFrame, got {type(df).__name__}")

    if where:
        try:
            filtered = df.query(where)
        except Exception as e:
            raise ValueError(f"Invalid where clause: {where!r}") from e
        return len(filtered)

    return len(df)
