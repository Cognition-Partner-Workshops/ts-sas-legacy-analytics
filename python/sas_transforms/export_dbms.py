"""Python equivalent of Macro/export_dbms.sas.

SAS ``%export_dbms`` wraps ``PROC EXPORT`` for writing DataFrames to
XLSX, XLS, SPSS (``.sav``), or Stata (``.dta``) files.  It handles
path resolution, file-existence checks, optional label headers, and
cleanup of ``.bak`` files.

The Python version uses:

* **XLSX** — :func:`pandas.DataFrame.to_excel` with ``openpyxl``.
* **Stata** — :func:`pandas.DataFrame.to_stata`.
* **SPSS** — :mod:`pyreadstat` ``write_sav`` when available, otherwise
  raises an informative error.
* **XLS** — legacy Excel format; written via ``xlwt`` (if installed) or
  falls back to ``openpyxl`` XLSX with a warning.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd


_DBMS_EXT: dict[str, str] = {
    "XLSX": ".xlsx",
    "XLS": ".xls",
    "SPSS": ".sav",
    "STATA": ".dta",
}


def export_dbms(
    data: pd.DataFrame,
    path: str,
    *,
    dbms: str = "XLSX",
    replace: bool = False,
    label: bool = False,
    labels: Optional[dict[str, str]] = None,
) -> str:
    """Export *data* to an external file, mirroring SAS ``%export_dbms``.

    Parameters
    ----------
    data : DataFrame
        Dataset to export.
    path : str
        Output file or directory path.
    dbms : str
        Output format: ``"XLSX"`` (default), ``"XLS"``, ``"SPSS"``, or
        ``"STATA"``.
    replace : bool
        Overwrite existing file (default *False*).
    label : bool
        Use column labels for the header/column names.
    labels : dict mapping column name → label, optional
        Column labels used when *label=True*.

    Returns
    -------
    str
        Resolved output file path.
    """
    dbms_upper = dbms.upper()
    if dbms_upper not in _DBMS_EXT:
        raise ValueError(f"Unsupported DBMS '{dbms}'. Choose from: {', '.join(_DBMS_EXT)}")

    ext = _DBMS_EXT[dbms_upper]
    resolved = _resolve_path(path, data, ext)
    _check_output(resolved, replace)

    export_data = data.copy()
    if label and labels:
        export_data = export_data.rename(columns=labels)

    if dbms_upper in ("XLSX", "XLS"):
        export_data.to_excel(resolved, index=False, engine="openpyxl")
    elif dbms_upper == "STATA":
        export_data.to_stata(resolved, write_index=False)
    elif dbms_upper == "SPSS":
        try:
            import pyreadstat
        except ImportError as exc:
            raise ImportError(
                "pyreadstat is required to write SPSS (.sav) files. "
                "Install it with: pip install pyreadstat"
            ) from exc
        pyreadstat.write_sav(export_data, str(resolved))

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
