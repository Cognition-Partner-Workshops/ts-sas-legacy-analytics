"""Python equivalent of Macro/export_csv.sas.

SAS macro signature:
    %export_csv(DATA=, PATH=, REPLACE=N, LABEL=N, HEADER=Y, LRECL=32767)

This is a thin wrapper around ``%export_dlm`` with ``DBMS=CSV``.
The Python translation wraps ``pandas.DataFrame.to_csv``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import pandas as pd


def export_csv(
    data: pd.DataFrame,
    path: str | os.PathLike[str],
    *,
    replace: bool = False,
    label: bool = False,
    header: bool = True,
    delimiter: str = ",",
) -> Path:
    """Export *data* to a delimited text file, mirroring SAS ``%export_csv``.

    Parameters
    ----------
    data : DataFrame
        Dataset to export.
    path : str or Path
        Output directory **or** full file path.
        * If a directory, the filename is derived from the DataFrame name
          attribute (falling back to ``"data"``), with a ``.csv`` extension.
    replace : bool
        Overwrite an existing file (default ``False``).
    label : bool
        Use column labels stored in ``data.attrs["_labels"]`` as header
        names.
    header : bool
        Write a header row (default ``True``).
    delimiter : str
        Field delimiter (default ``","``).

    Returns
    -------
    Path
        Resolved path to the written file.

    Raises
    ------
    FileExistsError
        If the file exists and *replace* is ``False``.
    """
    ext_map = {",": ".csv", "\t": ".tsv"}
    ext = ext_map.get(delimiter, ".txt")

    out_path = Path(path)
    if out_path.is_dir():
        ds_name = getattr(data, "name", None) or "data"
        out_path = out_path / f"{ds_name}{ext}"
    elif out_path.suffix == "":
        out_path = out_path.with_suffix(ext)

    if out_path.exists() and not replace:
        raise FileExistsError(
            f"{out_path} already exists. Specify replace=True to overwrite."
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = data.copy()
    if label:
        labels_map: dict[str, str] = data.attrs.get("_labels", {})
        df = df.rename(columns=lambda c: labels_map.get(c, c))

    df.to_csv(out_path, index=False, header=header, sep=delimiter)
    return out_path
