"""
Check if empty utility.

Migrated from: Macro/check_if_empty.sas
Original author: Scott Bass (04MAR2016)

Checks if a DataFrame is empty (has zero rows).
"""

from __future__ import annotations

from typing import Optional

import pandas as pd


def check_if_empty(df: pd.DataFrame, where: Optional[str] = None) -> bool:
    """
    Check if a DataFrame is empty.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    where : str, optional
        If provided, apply this query filter before checking.

    Returns
    -------
    bool
        True if the DataFrame (after optional filtering) has zero rows.

    Raises
    ------
    TypeError
        If df is not a DataFrame.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected a DataFrame, got {type(df).__name__}")

    if where:
        try:
            filtered = df.query(where)
        except Exception:
            return True
        return len(filtered) == 0

    return len(df) == 0
