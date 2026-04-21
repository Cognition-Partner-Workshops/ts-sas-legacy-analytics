"""
Numeric validation utility.

Migrated from: Macro/IsNum.sas
Original author: Scott Bass (16FEB2016)

Checks if string input represents valid numeric data and sets
classification flags (IsNum, IsInt, IsFloat, IsNonNeg, IsPos).
"""

from __future__ import annotations

import math
from typing import Union

import pandas as pd


# SAS special missing values: ., ._, .A-.Z
_SAS_MISSING = frozenset({".", "._"} | {f".{chr(c)}" for c in range(ord("A"), ord("Z") + 1)})


def is_num(series: pd.Series) -> pd.DataFrame:
    """
    Check if string values represent valid numeric data.

    Parameters
    ----------
    series : pd.Series
        Series of string values to check.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns:
        - IsNum: True if valid numeric (excluding blank/missing/special missing)
        - IsNum2: True if valid numeric OR blank/missing/special missing
        - IsInt: True if valid integer
        - IsFloat: True if valid float (has fractional part)
        - IsNonNeg: True if numeric and >= 0
        - IsPos: True if numeric and > 0
    """
    results = {
        "IsNum": [],
        "IsNum2": [],
        "IsInt": [],
        "IsFloat": [],
        "IsNonNeg": [],
        "IsPos": [],
    }

    for val in series:
        val_str = str(val).strip() if val is not None else ""

        # Try parsing as number
        num = _try_parse_number(val_str)

        if num is not None and not math.isnan(num):
            results["IsNum"].append(True)
            results["IsNum2"].append(True)
            results["IsInt"].append(float(num) == int(num))
            results["IsFloat"].append(abs(num - int(num)) > 0)
            results["IsNonNeg"].append(num >= 0)
            results["IsPos"].append(num > 0)
        else:
            # Not a valid number - check for SAS missing/blank
            is_sas_missing = val_str in _SAS_MISSING or val_str == ""
            results["IsNum"].append(False)
            results["IsNum2"].append(is_sas_missing)
            results["IsInt"].append(False)
            results["IsFloat"].append(False)
            results["IsNonNeg"].append(False)
            results["IsPos"].append(False)

    return pd.DataFrame(results)


def _try_parse_number(s: str) -> Union[float, None]:
    """Try to parse a string as a number. Returns None on failure."""
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None
