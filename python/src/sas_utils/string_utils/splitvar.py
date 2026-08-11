"""
Split variable utility.

Migrated from: Macro/splitvar.sas
Original author: Scott Bass

Splits a string into a list of substrings based on a delimiter or width.
"""

from __future__ import annotations

from typing import Optional


def splitvar(
    text: str,
    dlm: Optional[str] = None,
    width: Optional[int] = None,
) -> list[str]:
    """
    Split a string into parts.

    Parameters
    ----------
    text : str
        Input string.
    dlm : str, optional
        Delimiter to split on. Default splits on whitespace.
    width : int, optional
        If provided, split into fixed-width chunks instead.

    Returns
    -------
    list of str
        List of parts.
    """
    if width is not None and width > 0:
        return [text[i:i + width] for i in range(0, len(text), width)]

    if dlm is None:
        return text.split()

    return text.split(dlm)
