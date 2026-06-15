"""Python equivalent of Macro/export_xlsx.sas.

SAS ``%export_xlsx`` is a thin wrapper around ``%export_dbms`` that
sets ``DBMS=XLSX``.  The underlying macro calls ``PROC EXPORT`` and
then cleans up ``.bak`` files.

The Python equivalent delegates to :func:`pandas.DataFrame.to_excel`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd


def export_xlsx(
    data: pd.DataFrame,
    path: str,
    *,
    replace: bool = False,
    label: bool = False,
    labels: Optional[dict[str, str]] = None,
) -> str:
    """Export *data* to an XLSX file, mirroring SAS ``%export_xlsx``.

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
    labels : dict mapping column name → label, optional
        Column labels used when *label=True*.

    Returns
    -------
    str
        Resolved output file path.
    """
    resolved = _resolve_path(path, data, ext=".xlsx")
    _check_output(resolved, replace)

    col_header: list[str] | bool
    if label and labels:
        col_header = [labels.get(c, c) for c in data.columns]
    else:
        col_header = True

    data.to_excel(resolved, index=False, header=col_header, engine="openpyxl")
    return str(resolved)


def _resolve_path(path: str, data: pd.DataFrame, ext: str) -> Path:
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
