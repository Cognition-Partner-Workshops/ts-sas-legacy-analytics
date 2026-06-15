"""Python equivalent of Macro/subset_data.sas.

SAS macro signature:
    %subset_data(DATA=, OUT=, WHERE=, IF=, FIRSTOBS=, LASTOBS=, OBS=,
                 KEEP=, DROP=, RENAME=)

The SAS OBS parameter supports ranges like ``1-5 or 11-15 or 20-30``.
"""

from __future__ import annotations

import re
from typing import Optional, Sequence

import pandas as pd


def subset_data(
    data: pd.DataFrame,
    *,
    where: Optional[str] = None,
    if_expr: Optional[str] = None,
    firstobs: Optional[int] = None,
    lastobs: Optional[int] = None,
    obs: Optional[str] = None,
    keep: Optional[Sequence[str]] = None,
    drop: Optional[Sequence[str]] = None,
    rename: Optional[dict[str, str]] = None,
) -> pd.DataFrame:
    """Subset *data* by rows and columns, mirroring SAS ``%subset_data``.

    Parameters
    ----------
    data : DataFrame
        Input dataset.
    where : str, optional
        A pandas query expression applied as a row filter.
    if_expr : str, optional
        A pandas ``eval``-compatible expression used as a subsetting-if.
    firstobs : int, optional
        1-based first observation to keep.
    lastobs : int, optional
        1-based last observation to keep.
    obs : str, optional
        Non-contiguous observation ranges, e.g. ``"1-5 or 11-15"``.
        Uses 1-based indexing to match SAS behaviour.
    keep : list[str], optional
        Columns to keep.
    drop : list[str], optional
        Columns to drop.
    rename : dict[str, str], optional
        Mapping of ``{old_name: new_name}`` for column renames.
        Applied **before** keep/drop filtering, matching SAS semantics.

    Returns
    -------
    DataFrame
    """
    df = data.copy()

    if rename:
        df = df.rename(columns=rename)

    if firstobs is not None or lastobs is not None:
        start = (firstobs - 1) if firstobs is not None else 0
        end = lastobs if lastobs is not None else len(df)
        df = df.iloc[start:end]

    if obs is not None:
        mask = _parse_obs(obs, len(df))
        df = df.iloc[mask]

    if where is not None:
        df = df.query(where)

    if if_expr is not None:
        df = df.loc[df.eval(if_expr)]

    if keep is not None:
        df = df[list(keep)]
    elif drop is not None:
        df = df.drop(columns=list(drop), errors="ignore")

    return df.reset_index(drop=True)


def _parse_obs(obs_str: str, n: int) -> list[int]:
    """Parse a SAS-style observation list into 0-based integer indices.

    Examples
    --------
    >>> _parse_obs("1-5 or 11-15 or 20-30", 100)
    [0, 1, 2, 3, 4, 10, 11, 12, 13, 14, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]
    """
    indices: list[int] = []
    parts = re.split(r"\s+or\s+", obs_str.strip(), flags=re.IGNORECASE)
    for part in parts:
        part = part.strip()
        m = re.match(r"^(\d+)\s*-\s*(\d+)$", part)
        if m:
            lo = int(m.group(1))
            hi = int(m.group(2))
        else:
            lo = hi = int(part)
        for i in range(lo, min(hi, n) + 1):
            indices.append(i - 1)
    return indices
