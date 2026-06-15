"""Python equivalent of Macro/export_xlsx.sas.

SAS macro signature:
    %export_xlsx(DATA=, PATH=, REPLACE=N, LABEL=N)

Thin wrapper around ``%export_dbms`` with ``DBMS=XLSX``.
The Python translation delegates to :func:`export_dbms.export_dbms`.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from sas_transforms.export_dbms import export_dbms


def export_xlsx(
    data: pd.DataFrame,
    path: str | os.PathLike[str],
    *,
    replace: bool = False,
    label: bool = False,
    sheet_name: str = "Sheet1",
) -> Path:
    """Export *data* to an XLSX file, mirroring SAS ``%export_xlsx``.

    Parameters
    ----------
    data : DataFrame
    path : str or Path
    replace : bool
    label : bool
    sheet_name : str

    Returns
    -------
    Path
    """
    return export_dbms(
        data, path, dbms="xlsx", replace=replace, label=label,
        sheet_name=sheet_name,
    )
