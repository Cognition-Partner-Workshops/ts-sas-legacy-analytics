"""
Directory listing utility.

Migrated from: Macro/dirlist.sas
Original author: Scott Bass (28SEP2016)

Creates a DataFrame containing a directory listing with file metadata.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Union

import pandas as pd


def dirlist(
    directory: Union[str, Path],
    type: Optional[str] = None,
    filter_fn: Optional[Callable[[pd.Series], bool]] = None,
) -> pd.DataFrame:
    """
    Create a DataFrame containing a directory listing.

    Parameters
    ----------
    directory : str or Path
        Path to the directory to list.
    type : str, optional
        Filter by type: ``"f"`` for files only, ``"d"`` for dirs only.
        Case-insensitive.
    filter_fn : callable, optional
        A function that takes a row (pd.Series) and returns True to
        include, False to exclude.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: fullname, pathname, filename, basename,
        ext, type, filesize, createtime, lastmodified.

    Raises
    ------
    FileNotFoundError
        If the directory does not exist.
    NotADirectoryError
        If the path exists but is not a directory.
    """
    directory = Path(directory)

    if not directory.exists():
        raise FileNotFoundError(f"{str(directory)} does not exist")

    if not directory.is_dir():
        raise NotADirectoryError(
            f"Unable to open {str(directory)} as a directory."
        )

    records = []

    for entry in os.scandir(directory):
        stat = entry.stat(follow_symlinks=False)

        fullname = str(Path(entry.path).resolve())
        pathname = str(directory.resolve())
        filename = entry.name

        if entry.is_file():
            entry_type = "F"
            parts = filename.rsplit(".", 1)
            if len(parts) == 2:
                basename_val = parts[0]
                ext_val = parts[1]
            else:
                basename_val = filename
                ext_val = ""
            filesize = stat.st_size
        else:
            entry_type = "D"
            basename_val = filename
            ext_val = ""
            filesize = 0

        createtime = datetime.fromtimestamp(stat.st_ctime)
        lastmodified = datetime.fromtimestamp(stat.st_mtime)

        records.append({
            "fullname": fullname,
            "pathname": pathname,
            "filename": filename,
            "basename": basename_val,
            "ext": ext_val,
            "type": entry_type,
            "filesize": filesize,
            "createtime": createtime,
            "lastmodified": lastmodified,
        })

    df = pd.DataFrame(records)

    if df.empty:
        return pd.DataFrame(columns=[
            "fullname", "pathname", "filename", "basename",
            "ext", "type", "filesize", "createtime", "lastmodified",
        ])

    # Apply type filter
    if type is not None:
        type_upper = type.upper()
        df = df[df["type"] == type_upper].reset_index(drop=True)

    # Apply custom filter
    if filter_fn is not None:
        mask = df.apply(filter_fn, axis=1)
        df = df[mask].reset_index(drop=True)

    return df
