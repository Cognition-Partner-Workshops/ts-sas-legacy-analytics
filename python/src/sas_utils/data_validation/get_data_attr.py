"""
Get dataset attribute utility.

Migrated from: Macro/get_data_attr.sas
Original author: Scott Bass (09MAY2011)

Function-style utility to return a DataFrame attribute (nobs, nvars,
label, etc.).
"""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd


def get_data_attr(df: pd.DataFrame, attr: str) -> Any:
    """
    Return a DataFrame attribute.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    attr : str
        Attribute to retrieve. Valid values (case-insensitive):
        - ``"nobs"`` : number of observations (rows)
        - ``"nvars"`` : number of variables (columns)
        - ``"label"`` : dataset label (from df.attrs)
        - ``"mem"`` : dataset name (from df.attrs)
        - ``"sortedby"`` : sort columns (from df.attrs)
        - ``"type"`` : always "DATA" for DataFrames

    Returns
    -------
    Any
        The requested attribute value.

    Raises
    ------
    TypeError
        If df is not a DataFrame.
    ValueError
        If attr is not a recognized attribute.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected a DataFrame, got {type(df).__name__}")

    attr_upper = attr.upper()

    if attr_upper == "NOBS":
        return len(df)

    if attr_upper == "NVARS":
        return len(df.columns)

    if attr_upper == "LABEL":
        return df.attrs.get("label", "")

    if attr_upper == "MEM":
        return df.attrs.get("name", "")

    if attr_upper == "SORTEDBY":
        return df.attrs.get("sortedby", "")

    if attr_upper == "TYPE":
        return "DATA"

    if attr_upper in ("CRDTE", "MODTE"):
        return df.attrs.get(attr.lower(), None)

    if attr_upper == "ENGINE":
        return "PANDAS"

    valid_attrs = [
        "NOBS", "NVARS", "LABEL", "MEM", "SORTEDBY", "TYPE",
        "CRDTE", "MODTE", "ENGINE",
    ]
    raise ValueError(
        f"{attr!r} is not a recognized attribute. "
        f"Valid values: {', '.join(valid_attrs)}"
    )
