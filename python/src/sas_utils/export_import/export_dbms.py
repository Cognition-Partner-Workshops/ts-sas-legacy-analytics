"""
Export DBMS utility.

Migrated from: Macro/export_dbms.sas
Original author: Scott Bass (04SEP2019)

Wrapper for exporting a DataFrame to external files (XLSX, XLS, SPSS, STATA).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import pandas as pd


def export_dbms(
    data: pd.DataFrame,
    path: Union[str, Path],
    dbms: str = "xlsx",
    replace: bool = False,
    label: bool = False,
) -> Path:
    """
    Export a DataFrame to an external file.

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame to export.
    path : str or Path
        Output directory or file path. If a directory, the file
        is named after the DataFrame (from ``data.attrs.get("name")``)
        or defaults to ``"output"``.
    dbms : str
        Output format. One of ``"xlsx"``, ``"xls"``, ``"spss"``, ``"stata"``.
        Default ``"xlsx"``.
    replace : bool
        If True, overwrite existing file. Default False.
    label : bool
        If True, use column labels (from ``data.attrs.get("labels", {})``)
        as header names. Default False.

    Returns
    -------
    Path
        Path to the created file.

    Raises
    ------
    ValueError
        If data is not a DataFrame, dbms is invalid, or path issues.
    FileExistsError
        If file exists and replace is False.
    FileNotFoundError
        If output directory does not exist.
    """
    if not isinstance(data, pd.DataFrame):
        raise ValueError("data must be a pandas DataFrame")

    dbms = dbms.upper()
    ext_map = {"XLSX": ".xlsx", "XLS": ".xls", "SPSS": ".sav", "STATA": ".dta"}
    if dbms not in ext_map:
        raise ValueError(
            f"{dbms!r} is not a valid DBMS value. "
            f"Allowable values are: {', '.join(ext_map.keys())}."
        )

    ext = ext_map[dbms]
    path = Path(path)

    # Determine if path is a directory or file
    if path.is_dir() or (path.suffix == "" and not path.exists()):
        ds_name = data.attrs.get("name", "output")
        if not path.exists():
            raise FileNotFoundError(f"The directory {str(path)!r} does not exist.")
        path = path / f"{ds_name}{ext}"
    else:
        # It's a file path - check the parent directory exists
        if not path.parent.exists():
            raise FileNotFoundError(
                f'The directory "{path.parent}" does not exist. No output created'
            )

    # Check if file exists and replace flag
    if path.exists() and not replace:
        raise FileExistsError(
            f'"{path}" already exists. Specify replace=True to overwrite. '
            "No output created."
        )

    # Apply labels if requested
    export_df = data.copy()
    if label:
        labels = data.attrs.get("labels", {})
        if labels:
            rename_map = {col: labels.get(col, col) for col in export_df.columns}
            export_df = export_df.rename(columns=rename_map)

    # Export based on format
    if dbms in ("XLSX", "XLS"):
        export_df.to_excel(str(path), index=False, engine="openpyxl")
    elif dbms == "SPSS":
        import pyreadstat
        pyreadstat.write_sav(export_df, str(path))
    elif dbms == "STATA":
        export_df.to_stata(str(path), write_index=False)

    # Clean up backup files (mimics SAS behavior)
    bak_path = Path(f"{path}.bak")
    if bak_path.exists():
        bak_path.unlink()

    return path
