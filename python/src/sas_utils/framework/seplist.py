"""
Separated list utility - emit a delimited string from a list of words.

Migrated from: Macro/seplist.sas
Original author: Richard Devenezia (02SEP1999)

Produces a delimited string with optional prefix, suffix, and nesting
(quoting) of each item.
"""

from __future__ import annotations

from typing import Optional


_NEST_MAP = {
    "Q": ("'", "'"),
    "QQ": ('"', '"'),
    "P": ("(", ")"),
    "C": ("{", "}"),
    "B": ("[", "]"),
}


def seplist(
    items: str,
    dlm: str = ",",
    prefix: str = "",
    suffix: str = "",
    nest: Optional[str] = None,
    indlm: str = " ",
    trim: bool = True,
) -> str:
    """
    Emit a list of words separated by a delimiter.

    Parameters
    ----------
    items : str
        Input string of items separated by ``indlm``.
    dlm : str
        Output delimiter between items. Default is comma.
    prefix : str
        String to place before each item.
    suffix : str
        String to place after each item.
    nest : str or None
        Quoting style shortcut. Overrides prefix/suffix nesting chars.
        Valid values: ``Q`` (single quotes), ``QQ`` (double quotes),
        ``P`` (parentheses), ``C`` (curly braces), ``B`` (brackets).
    indlm : str
        Input delimiter separating items in the input string.
        Default is a space.
    trim : bool
        Whether to strip whitespace from each item. Default True.

    Returns
    -------
    str
        The delimited string.
    """
    if nest is not None:
        nest_upper = nest.upper()
        if nest_upper in _NEST_MAP:
            nest_prefix, nest_suffix = _NEST_MAP[nest_upper]
            prefix = prefix + nest_prefix
            suffix = nest_suffix + suffix

    parts = items.split(indlm)

    result_parts = []
    for i, part in enumerate(parts):
        if trim:
            part = part.strip()
        if not part and trim:
            continue

        # Support incremented prefix/suffix with &n placeholder
        current_prefix = prefix.replace("&n", str(i + 1))
        current_suffix = suffix.replace("&n", str(i + 1))

        result_parts.append(f"{current_prefix}{part}{current_suffix}")

    return dlm.join(result_parts)
