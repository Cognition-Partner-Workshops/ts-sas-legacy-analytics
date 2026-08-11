"""
String deduplication utility.

Migrated from: Macro/dedup_string.sas
Original author: Scott Bass (29AUG2011)

Removes duplicate tokens from a string while preserving order.
"""

from __future__ import annotations


def dedup_string(text: str, dlm: str = " ") -> str:
    """
    Remove duplicate tokens from a string, preserving first occurrence order.

    Parameters
    ----------
    text : str
        Input string.
    dlm : str
        Delimiter to split/join tokens. Default is space.

    Returns
    -------
    str
        Deduplicated string.
    """
    if not text:
        return text

    tokens = text.split(dlm)
    seen: set[str] = set()
    result = []
    for token in tokens:
        key = token.upper()
        if key not in seen:
            seen.add(key)
            result.append(token)

    return dlm.join(result)
