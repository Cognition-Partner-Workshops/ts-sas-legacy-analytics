"""Python equivalent of Macro/export_dbms.sas.

SAS macro signature:
    %export_dbms(DATA=, PATH=, DBMS=XLSX, REPLACE=N, LABEL=N)

Wraps ``PROC EXPORT`` for XLSX, XLS, SPSS, and STATA formats.
The Python translation uses pandas I/O writers (openpyxl for Excel).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import pandas as pd


_EXTENSION_MAP: dict[str, str] = {
    "xlsx": ".xlsx",
    "spss": ".sav",
    "stata": ".dta",
}

_DEPRECATED_FORMATS: dict[str, str] = {
    "xls": "Legacy .xls (Excel 97-2003) format is not supported by modern "
           "Python libraries. Use dbms='xlsx' instead.",
}


def export_dbms(
    data: pd.DataFrame,
    path: str | os.PathLike[str],
    *,
    dbms: str = "xlsx",
    replace: bool = False,
    label: bool = False,
    sheet_name: str = "Sheet1",
) -> Path:
    """Export *data* to an external file, mirroring SAS ``PROC EXPORT``.

    Parameters
    ----------
    data : DataFrame
        Dataset to export.
    path : str or Path
        Output directory **or** full file path.
        * If a directory, the filename is derived from the DataFrame name
          attribute (falling back to ``"data"``).
        * If a file path, it is used as-is.
    dbms : str
        ``"xlsx"`` (default), ``"spss"``, or ``"stata"``.
        Legacy ``"xls"`` raises ``ValueError`` (no modern Python writer).
    replace : bool
        Overwrite an existing file (default ``False``).
    label : bool
        Use column labels (from ``DataFrame.attrs`` or a ``_labels``
        dict stored in ``data.attrs``) as header names instead of
        column names.
    sheet_name : str
        Worksheet name for Excel formats (default ``"Sheet1"``).

    Returns
    -------
    Path
        Resolved path to the written file.

    Raises
    ------
    FileExistsError
        If the output file already exists and *replace* is ``False``.
    ValueError
        If *dbms* is not a recognised format.
    """
    dbms_lower = dbms.lower()
    if dbms_lower in _DEPRECATED_FORMATS:
        raise ValueError(_DEPRECATED_FORMATS[dbms_lower])
    if dbms_lower not in _EXTENSION_MAP:
        raise ValueError(
            f"Unsupported dbms '{dbms}'. Choose from: {', '.join(_EXTENSION_MAP)}"
        )

    out_path = Path(path)
    if out_path.is_dir():
        ds_name = getattr(data, "name", None) or "data"
        out_path = out_path / f"{ds_name}{_EXTENSION_MAP[dbms_lower]}"
    elif out_path.suffix == "":
        out_path = out_path.with_suffix(_EXTENSION_MAP[dbms_lower])

    if out_path.exists() and not replace:
        raise FileExistsError(
            f"{out_path} already exists. Specify replace=True to overwrite."
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = data.copy()
    if label:
        labels_map: dict[str, str] = data.attrs.get("_labels", {})
        df = df.rename(columns=lambda c: labels_map.get(c, c))

    if dbms_lower == "xlsx":
        df.to_excel(out_path, index=False, sheet_name=sheet_name, engine="openpyxl")
    elif dbms_lower == "stata":
        df.to_stata(out_path, write_index=False)
    elif dbms_lower == "spss":
        try:
            import pyreadstat
            pyreadstat.write_sav(df, str(out_path))
        except ImportError:
            raise ImportError(
                "pyreadstat is required for SPSS export. "
                "Install it with: pip install pyreadstat"
            )

    bak_path = out_path.with_suffix(out_path.suffix + ".bak")
    if bak_path.exists():
        bak_path.unlink()

    return out_path
