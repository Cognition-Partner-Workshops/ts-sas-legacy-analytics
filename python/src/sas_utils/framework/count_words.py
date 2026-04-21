"""
Count words utility.

Migrated from: Macro/count_words.sas
Original author: Scott Bass (16APR2011)

Returns the number of words/tokens in a string, split by a delimiter.
"""

from __future__ import annotations


def count_words(text: str, dlm: str = " ") -> int:
    """
    Return the number of words delimited by a delimiter or set of delimiters.

    Parameters
    ----------
    text : str
        Input string. If empty/blank, returns 0.
    dlm : str
        Delimiter character(s). Each character in the string is treated
        as a separate delimiter. Default is a space.

    Returns
    -------
    int
        Number of words found.
    """
    if not text or not text.strip():
        return 0

    import re
    pattern = "[" + re.escape(dlm) + "]+"
    tokens = re.split(pattern, text.strip())
    return len([t for t in tokens if t])
