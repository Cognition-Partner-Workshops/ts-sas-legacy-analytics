"""
Single-quote wrapper utility.

Migrated from: Macro/squote.sas
Original author: Scott Bass (28OCT2016)

Wraps a value in single quotes, escaping internal single quotes.
"""

from __future__ import annotations


def squote(value: str = "") -> str:
    """
    Wrap the argument in single quotes.

    Internal single quotes are doubled (escaped) to produce valid
    SQL-style quoting.

    Parameters
    ----------
    value : str
        The value to wrap. Default is empty string.

    Returns
    -------
    str
        The single-quoted string.
    """
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"
