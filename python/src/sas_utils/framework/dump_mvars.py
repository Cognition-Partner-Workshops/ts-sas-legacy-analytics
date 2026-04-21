"""
Dump macro variables utility.

Migrated from: Macro/dump_mvars.sas
Original author: Scott Bass (11MAY2011)

Dumps variable names and values to a formatted string or log output.
"""

from __future__ import annotations

import sys
from typing import Any, Optional, TextIO


def dump_mvars(
    variables: dict[str, Any],
    names: Optional[list[str]] = None,
    sort: bool = False,
    file: Optional[TextIO] = None,
) -> str:
    """
    Dump variables to a formatted string (and optionally a file/stream).

    Parameters
    ----------
    variables : dict
        Dictionary of variable names to values.
    names : list of str, optional
        If provided, only dump these variables (in order given).
        If None, dump all variables.
    sort : bool
        If True, sort output by variable name. Default False.
    file : TextIO, optional
        If provided, also write output to this stream.

    Returns
    -------
    str
        Formatted string with variable dump.
    """
    separator = "=" * 80

    if names is None:
        keys = list(variables.keys())
    else:
        keys = list(names)

    if sort:
        keys = sorted(keys, key=str.upper)

    lines = [separator]
    for key in keys:
        if key in variables:
            value = variables[key]
            lines.append(f"{key:<32} = {value}")
        else:
            lines.append(f"{key:<32} = ***VARIABLE UNDEFINED***")
    lines.append(separator)

    output = "\n".join(lines)

    if file is not None:
        file.write(output + "\n")

    return output
