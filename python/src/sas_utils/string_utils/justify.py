"""
Justify text utility.

Migrated from: Macro/justify.sas
Original author: Scott Bass

Left, right, or center justify text within a given width.
"""

from __future__ import annotations


def justify(text: str, width: int = 0, align: str = "left") -> str:
    """
    Justify text within a field width.

    Parameters
    ----------
    text : str
        Input text.
    width : int
        Field width. If 0 or less than text length, returns text as-is.
    align : str
        Alignment: ``"left"``, ``"right"``, or ``"center"``.
        Default ``"left"``.

    Returns
    -------
    str
        Justified text.
    """
    if width <= 0 or width <= len(text):
        return text

    align_lower = align.lower()
    if align_lower == "right":
        return text.rjust(width)
    elif align_lower == "center":
        return text.center(width)
    else:
        return text.ljust(width)
