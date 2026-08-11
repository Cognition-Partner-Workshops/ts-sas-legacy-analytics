"""
Hash define / hash lookup utility.

Migrated from: Macro/hash_define.sas, Macro/hash_lookup.sas
Original author: Scott Bass (06JAN2016)

Maps SAS hash object lookups to pandas merge operations.
"""

from __future__ import annotations

from typing import Optional, Union

import pandas as pd


def hash_define(
    source: pd.DataFrame,
    keys: Union[str, list[str]],
    data_vars: Optional[Union[str, list[str]]] = None,
    rename: Optional[dict[str, str]] = None,
    multidata: bool = False,
) -> dict:
    """
    Define a hash table (lookup dictionary) from a source DataFrame.

    Parameters
    ----------
    source : pd.DataFrame
        The lookup dataset.
    keys : str or list of str
        Column name(s) used as lookup keys.
    data_vars : str or list of str, optional
        Column(s) to include in the lookup result. Default: all non-key columns.
    rename : dict, optional
        Rename lookup columns: ``{old_name: new_name}``.
    multidata : bool
        If True, allow multiple matches per key. Default False.

    Returns
    -------
    dict
        A hash definition object used by ``hash_lookup()``.
    """
    if isinstance(keys, str):
        keys = keys.split()
    if isinstance(data_vars, str):
        data_vars = data_vars.split()

    if data_vars is None:
        data_vars = [c for c in source.columns if c not in keys]

    keep_cols = list(keys) + list(data_vars)
    lookup_df = source[keep_cols].copy()

    if rename:
        lookup_df = lookup_df.rename(columns=rename)
        data_vars = [rename.get(v, v) for v in data_vars]

    return {
        "source": lookup_df,
        "keys": keys,
        "data_vars": data_vars,
        "multidata": multidata,
    }


def hash_lookup(
    target: pd.DataFrame,
    hash_def: dict,
    how: str = "left",
) -> pd.DataFrame:
    """
    Perform a hash lookup (merge) against a target DataFrame.

    Parameters
    ----------
    target : pd.DataFrame
        The target DataFrame to augment with lookup data.
    hash_def : dict
        Hash definition from ``hash_define()``.
    how : str
        Merge type. Default ``"left"`` (left join, matching SAS hash behaviour).

    Returns
    -------
    pd.DataFrame
        Merged DataFrame with lookup columns added.
    """
    lookup_df = hash_def["source"]
    keys = hash_def["keys"]

    result = target.merge(lookup_df, on=keys, how=how)

    return result
