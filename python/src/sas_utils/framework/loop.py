"""
Loop utility - execute a callback over a list of items.

Migrated from: Macro/loop.sas
Original author: Scott Bass (24APR2006)

In SAS, %loop iterates over a space-separated list and calls a nested macro.
In Python, this is a simple iteration helper with delimiter support.
"""

from __future__ import annotations

from typing import Any, Callable, Optional, Sequence, Union


def loop(
    items: Union[str, Sequence[str]],
    callback: Callable[[str], Any],
    dlm: str = " ",
) -> list[Any]:
    """
    Iterate over a list of items and call a callback for each.

    Parameters
    ----------
    items : str or list of str
        If a string, it is split by ``dlm``. If a list, used directly.
    callback : callable
        Called with each item as its single argument.
    dlm : str
        Delimiter used to split ``items`` when it is a string.
        Default is a space.

    Returns
    -------
    list
        List of return values from each callback invocation.
    """
    if isinstance(items, str):
        word_list = [w for w in items.split(dlm) if w.strip()]
    else:
        word_list = list(items)

    results = []
    for word in word_list:
        results.append(callback(word))
    return results
