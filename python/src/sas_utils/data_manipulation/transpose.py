"""
Transpose utility.

Migrated from: Macro/transpose.sas
Original author: Scott Bass (01JAN2010)

Wraps pandas melt/pivot with a SAS PROC TRANSPOSE-like parameter interface.
"""

from __future__ import annotations

from typing import Optional, Sequence, Union

import pandas as pd


def transpose(
    data: pd.DataFrame,
    var: Union[str, list[str]],
    by: Optional[Union[str, list[str]]] = None,
    name: str = "_NAME_",
    label: Optional[str] = None,
    col: str = "COL1",
    notsorted: bool = False,
) -> pd.DataFrame:
    """
    Transpose a DataFrame from wide to long or long to wide format.

    This implements the same semantics as SAS ``PROC TRANSPOSE``
    with the ``BY``, ``VAR``, ``ID`` parameters.

    Parameters
    ----------
    data : pd.DataFrame
        Input DataFrame.
    var : str or list of str
        Column(s) to transpose (unpivot).
    by : str or list of str, optional
        Group-by column(s) kept as identifiers.
    name : str
        Name for the column that stores the original variable names.
        Default ``"_NAME_"``.
    label : str or None
        If provided, column name for variable labels. Not used in base impl.
    col : str
        Name for the value column. Default ``"COL1"``.
    notsorted : bool
        If True, preserve the original row order of groups.
        Default False.

    Returns
    -------
    pd.DataFrame
        Transposed DataFrame.
    """
    if isinstance(var, str):
        var = var.split()

    if isinstance(by, str):
        by = by.split()

    id_vars = by if by else []

    melted = data.melt(
        id_vars=id_vars,
        value_vars=var,
        var_name=name,
        value_name=col,
    )

    if not notsorted and by:
        melted = melted.sort_values(by + [name]).reset_index(drop=True)
    else:
        melted = melted.reset_index(drop=True)

    return melted
