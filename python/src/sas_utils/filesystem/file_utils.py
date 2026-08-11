"""
File system utility functions.

Migrated from: Macro/create_directory.sas, Macro/delete_file.sas
Original author: Scott Bass

Thin wrappers around pathlib operations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union


def create_directory(path: Union[str, Path], parents: bool = True) -> Path:
    """
    Create a directory, optionally including parents.

    Parameters
    ----------
    path : str or Path
        Directory path to create.
    parents : bool
        If True, create parent directories. Default True.

    Returns
    -------
    Path
        The created directory path.
    """
    path = Path(path)
    path.mkdir(parents=parents, exist_ok=True)
    return path


def delete_file(path: Union[str, Path], missing_ok: bool = True) -> bool:
    """
    Delete a file.

    Parameters
    ----------
    path : str or Path
        File path to delete.
    missing_ok : bool
        If True, do not raise an error if the file does not exist.
        Default True.

    Returns
    -------
    bool
        True if the file was deleted, False if it did not exist.
    """
    path = Path(path)
    if path.exists():
        path.unlink()
        return True
    if not missing_ok:
        raise FileNotFoundError(f"{str(path)} does not exist")
    return False
