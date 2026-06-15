"""Python equivalent of Macro/dedup_string.sas.

SAS ``%dedup_string`` is a DATA-step macro that removes duplicate tokens
from a character variable, preserving the order of first appearance.
It uses ``INDEXW`` on the accumulated output to detect duplicates
(case-insensitive).

The Python version operates on a plain ``str`` and returns a new ``str``.
It can also be applied element-wise to a :class:`pandas.Series` via
:func:`dedup_string_series`.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd


def dedup_string(
    invar: str,
    *,
    dlm: Optional[str] = None,
) -> str:
    """Remove duplicate tokens from *invar*, preserving first occurrence.

    Parameters
    ----------
    invar : str
        Input string containing tokens separated by *dlm*.
    dlm : str or None
        Delimiter used to split tokens.  Defaults to a single space.

    Returns
    -------
    str
        Deduplicated string with tokens separated by a single space.

    Notes
    -----
    Comparison is case-insensitive, matching SAS ``INDEXW(UPCASE(...))``.
    """
    if dlm is None:
        dlm = " "

    tokens = invar.split(dlm)
    seen: set[str] = set()
    result: list[str] = []
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        key = token.upper()
        if key not in seen:
            seen.add(key)
            result.append(token)
    return " ".join(result)


def dedup_string_series(
    series: pd.Series,
    *,
    dlm: Optional[str] = None,
) -> pd.Series:
    """Apply :func:`dedup_string` element-wise to a pandas Series.

    Useful when the SAS macro is called inside a DATA step that
    processes many rows.
    """
    return series.apply(lambda s: dedup_string(str(s), dlm=dlm) if pd.notna(s) else s)
