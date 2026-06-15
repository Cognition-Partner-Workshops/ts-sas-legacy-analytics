"""Python equivalent of Macro/export_csv.sas.

SAS ``%export_csv`` is a thin wrapper around ``%export_dlm`` that sets
``DBMS=CSV``.  The underlying ``%export_dlm`` macro uses a DATA step
(not PROC EXPORT) to write a delimited file, giving control over the
header row (label vs. name), logical record length, and delimiter.

The Python equivalent delegates to :func:`pandas.DataFrame.to_csv`.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import pandas as pd


def export_csv(
    data: pd.DataFrame,
    path: str,
    *,
    replace: bool = False,
    label: bool = False,
    header: bool = True,
    labels: Optional[dict[str, str]] = None,
    lrecl: int = 32767,
) -> str:
    """Export *data* to a CSV file, mirroring SAS ``%export_csv``.

    Parameters
    ----------
    data : DataFrame
        Dataset to export.
    path : str
        Output file or directory path.  If a directory, the filename is
        derived from the DataFrame's ``name`` attribute (falling back to
        ``"data"``).
    replace : bool
        Overwrite the file if it already exists (default *False*).
    label : bool
        Use column labels instead of names for the header row.
        Labels are supplied via the *labels* mapping.
    header : bool
        Write a header row (default *True*).
    labels : dict mapping column name → label, optional
        Column labels used when *label=True*.
    lrecl : int
        Ignored in the Python version (pandas handles line length).
        Kept for signature parity.

    Returns
    -------
    str
        Resolved output file path.

    Raises
    ------
    FileExistsError
        If the output file exists and *replace* is *False*.
    FileNotFoundError
        If the parent directory of the output path does not exist.
    """
    resolved = _resolve_path(path, data, ext=".csv")
    _check_output(resolved, replace)

    col_header: object
    if header:
        if label and labels:
            col_header = [labels.get(c, c) for c in data.columns]
        else:
            col_header = True
    else:
        col_header = False

    data.to_csv(resolved, index=False, header=col_header)
    return str(resolved)


def _resolve_path(path: str, data: pd.DataFrame, ext: str) -> Path:
    """Derive the full file path when only a directory was given."""
    p = Path(path)
    if p.is_dir():
        ds_name = getattr(data, "name", None) or "data"
        p = p / f"{ds_name}{ext}"
    return p


def _check_output(path: Path, replace: bool) -> None:
    parent = path.parent
    if not parent.exists():
        raise FileNotFoundError(f"Directory '{parent}' does not exist.")
    if path.exists() and not replace:
        raise FileExistsError(
            f"'{path}' already exists. Specify replace=True to overwrite."
        )
