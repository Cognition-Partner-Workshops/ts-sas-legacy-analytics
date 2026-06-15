"""Python equivalent of Macro/subset_data.sas.

SAS ``%subset_data`` applies row-level filtering (``WHERE``, subsetting
``IF``, observation ranges) and column-level operations (``KEEP``,
``DROP``, ``RENAME``) in a single DATA step.

This module mirrors that with standard pandas operations:
``DataFrame.query``, ``DataFrame.iloc``, ``DataFrame.rename``,
column selection, and column dropping.
"""

from __future__ import annotations

import re
from typing import Optional, Sequence

import pandas as pd


def subset_data(
    data: pd.DataFrame,
    *,
    where: Optional[str] = None,
    if_: Optional[str] = None,
    firstobs: Optional[int] = None,
    lastobs: Optional[int] = None,
    obs: Optional[str] = None,
    keep: Optional[Sequence[str]] = None,
    drop: Optional[Sequence[str]] = None,
    rename: Optional[dict[str, str]] = None,
) -> pd.DataFrame:
    """Subset *data*, mirroring SAS ``%subset_data``.

    Parameters
    ----------
    data : DataFrame
        Input dataset.
    where : str, optional
        Pandas query expression for row filtering (``WHERE`` clause).
    if_ : str, optional
        Pandas query expression evaluated after ``where`` (SAS subsetting
        ``IF``).  Separate from *where* because in SAS the ``IF``
        statement executes after the ``SET`` statement (including
        ``RENAME``), while ``WHERE`` operates directly on the input.
    firstobs : int, optional
        1-based index of the first observation to keep.
    lastobs : int, optional
        1-based index of the last observation to keep.
    obs : str, optional
        Non-contiguous observation ranges separated by ``" or "``, e.g.
        ``"1-5 or 11-15 or 20-30"``.  Ranges and single numbers are
        both supported.  Uses 1-based indexing.
    keep : sequence of str, optional
        Columns to keep.  Applied after ``rename``.
    drop : sequence of str, optional
        Columns to drop.  Applied after ``rename``.
    rename : dict mapping old → new, optional
        Column rename mapping.  Applied before ``keep``/``drop`` and
        ``where``/``if_`` to match SAS evaluation order (RENAME is a
        dataset option applied at the SET statement).

    Returns
    -------
    DataFrame
        Subsetted dataset.
    """
    df = data.copy()

    # RENAME is a dataset option — applied during SET (before IF/WHERE)
    if rename:
        df = df.rename(columns=rename)

    # FIRSTOBS / LASTOBS (1-based, inclusive)
    if firstobs is not None or lastobs is not None:
        start = (firstobs - 1) if firstobs is not None else 0
        end = lastobs if lastobs is not None else len(df)
        df = df.iloc[start:end].reset_index(drop=True)

    # OBS ranges
    if obs is not None:
        mask = _parse_obs_ranges(obs, len(df))
        df = df.iloc[mask].reset_index(drop=True)

    # WHERE clause
    if where is not None:
        df = df.query(where).reset_index(drop=True)

    # Subsetting IF
    if if_ is not None:
        df = df.query(if_).reset_index(drop=True)

    # KEEP / DROP
    if keep is not None:
        df = df[list(keep)]
    if drop is not None:
        df = df.drop(columns=list(drop), errors="ignore")

    return df


def _parse_obs_ranges(obs_str: str, n_obs: int) -> list[int]:
    """Parse a SAS-style obs range string into 0-based row indices.

    Examples
    --------
    >>> _parse_obs_ranges("1-5 or 11-15 or 20-30", 25)
    [0, 1, 2, 3, 4, 10, 11, 12, 13, 14, 19, 20, 21, 22, 23, 24]
    """
    indices: list[int] = []
    parts = re.split(r"\s+or\s+", obs_str, flags=re.IGNORECASE)
    for part in parts:
        part = part.strip()
        m = re.match(r"^(\d+)\s*-\s*(\d+)$", part)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
        else:
            lo = hi = int(part)
        # Clamp to dataset length; 1-based → 0-based
        lo_idx = max(lo - 1, 0)
        hi_idx = min(hi, n_obs)
        indices.extend(range(lo_idx, hi_idx))
    return indices
