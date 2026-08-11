"""
Attribute / column metadata utility.

Migrated from: Macro/attrib.sas
Original author: Scott Bass

Manages DataFrame column metadata (labels, formats, lengths).
"""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd


def set_labels(df: pd.DataFrame, labels: dict[str, str]) -> pd.DataFrame:
    """
    Set column labels on a DataFrame.

    Labels are stored in ``df.attrs["labels"]``.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame (modified in place).
    labels : dict
        Mapping of column name to label string.

    Returns
    -------
    pd.DataFrame
        The same DataFrame (for chaining).
    """
    if "labels" not in df.attrs:
        df.attrs["labels"] = {}
    df.attrs["labels"].update(labels)
    return df


def get_label(df: pd.DataFrame, column: str) -> str:
    """
    Get the label for a column.

    Returns the column name itself if no label is set.
    """
    labels = df.attrs.get("labels", {})
    return labels.get(column, column)


def set_formats(df: pd.DataFrame, formats: dict[str, str]) -> pd.DataFrame:
    """
    Set display formats on a DataFrame.

    Formats are stored in ``df.attrs["formats"]``.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    formats : dict
        Mapping of column name to format string.

    Returns
    -------
    pd.DataFrame
    """
    if "formats" not in df.attrs:
        df.attrs["formats"] = {}
    df.attrs["formats"].update(formats)
    return df
