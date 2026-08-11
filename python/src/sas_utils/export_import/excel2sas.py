"""
Excel to DataFrame import utility.

Migrated from: Macro/excel2sas.sas
Original author: Scott Bass (14MAR2014)

Reads an Excel file into a pandas DataFrame, with options for
sheet selection and column type handling.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import pandas as pd


def excel2sas(
    path: Union[str, Path],
    sheet: Union[str, int, None] = None,
    header: int = 0,
    skiprows: Optional[int] = None,
    nrows: Optional[int] = None,
    rename: Optional[dict[str, str]] = None,
) -> pd.DataFrame:
    """
    Read an Excel file into a DataFrame.

    Parameters
    ----------
    path : str or Path
        Path to the Excel file.
    sheet : str, int, or None
        Sheet name or index. Default reads the first sheet.
    header : int
        Row to use as column headers (0-indexed). Default 0.
    skiprows : int, optional
        Number of rows to skip from the top.
    nrows : int, optional
        Max number of rows to read.
    rename : dict, optional
        Rename columns: ``{old_name: new_name}``.

    Returns
    -------
    pd.DataFrame
        The imported data.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File {str(path)!r} does not exist.")

    kwargs = {"header": header}
    if sheet is not None:
        kwargs["sheet_name"] = sheet
    if skiprows is not None:
        kwargs["skiprows"] = skiprows
    if nrows is not None:
        kwargs["nrows"] = nrows

    df = pd.read_excel(path, **kwargs)

    if rename:
        df = df.rename(columns=rename)

    return df
