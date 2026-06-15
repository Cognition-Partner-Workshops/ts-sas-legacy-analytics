"""Python equivalent of Macro/dedup_string.sas.

SAS macro signature (data-step macro):
    %dedup_string(INVAR=, OUTVAR=, DLM=)

Operates on a single string value, removing duplicate tokens while
preserving first-occurrence order.  The SAS version uses ``indexw``
with case-insensitive comparison; the Python version follows suit.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd


def dedup_string(
    value: str,
    *,
    dlm: Optional[str] = None,
    case_sensitive: bool = False,
) -> str:
    """Remove duplicate tokens from *value*.

    Parameters
    ----------
    value : str
        Input string containing possibly duplicated tokens.
    dlm : str, optional
        Token delimiter.  Defaults to a single space.
    case_sensitive : bool
        If ``False`` (default, matching SAS), duplicates are detected
        case-insensitively, but the first occurrence's original casing
        is preserved.

    Returns
    -------
    str
        The deduplicated string, joined with a single space (matching SAS
        output behaviour where ``catx`` always uses a single delimiter).
    """
    if dlm is None:
        dlm = " "

    tokens = value.split(dlm)
    seen: set[str] = set()
    result: list[str] = []
    for token in tokens:
        if not token:
            continue
        key = token if case_sensitive else token.upper()
        if key not in seen:
            seen.add(key)
            result.append(token)

    return " ".join(result)


def dedup_string_series(
    series: pd.Series,
    *,
    dlm: Optional[str] = None,
    case_sensitive: bool = False,
) -> pd.Series:
    """Vectorised wrapper: apply :func:`dedup_string` to every row.

    This mirrors the SAS pattern of calling ``%dedup_string`` inside a
    DATA step that processes many observations.
    """
    return series.apply(
        lambda v: dedup_string(str(v), dlm=dlm, case_sensitive=case_sensitive)
        if pd.notna(v) else v
    )
