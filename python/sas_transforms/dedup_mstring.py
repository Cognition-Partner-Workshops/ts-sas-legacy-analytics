"""Python equivalent of Macro/dedup_mstring.sas.

SAS ``%dedup_mstring`` is a *pure macro* (runs at compile time) that
removes duplicate words from a macro-variable string.  Unlike
``%dedup_string`` it supports configurable input *and* output delimiters
and strips leading/trailing whitespace from each token.

The Python translation is a simple string function.
"""

from __future__ import annotations

from typing import Optional


def dedup_mstring(
    in_: str,
    *,
    indlm: Optional[str] = None,
    dlm: Optional[str] = None,
) -> str:
    """Remove duplicate tokens from *in_*, preserving first occurrence.

    Parameters
    ----------
    in_ : str
        Input string.
    indlm : str or None
        Input delimiter(s).  When the string contains multiple distinct
        delimiter characters (e.g. ``"^#|*"``), *any* of them will
        split the input — mirroring SAS ``%SCAN`` behaviour.  Defaults
        to a single space.
    dlm : str or None
        Output delimiter.  Defaults to *indlm* when *indlm* is a
        single character, otherwise defaults to a single space.

    Returns
    -------
    str
        Deduplicated string with tokens joined by *dlm*.

    Notes
    -----
    The SAS macro performs case-sensitive comparison via ``INDEXW``.
    However, the SAS ``INDEXW`` function with a delimiter argument is
    case-sensitive (unlike the space-delimited overload).  This
    implementation preserves case-sensitive comparison to match the
    SAS behaviour for the macro-variable context.
    """
    if indlm is None:
        indlm = " "

    # Determine output delimiter
    if dlm is None:
        dlm = indlm if len(indlm) == 1 else " "

    # Split using any character in indlm as a delimiter
    if len(indlm) == 1:
        tokens = in_.split(indlm)
    else:
        # Multi-char indlm: each character is a separate delimiter
        import re
        pattern = "[" + re.escape(indlm) + "]"
        tokens = re.split(pattern, in_)

    seen: set[str] = set()
    result: list[str] = []
    for token in tokens:
        word = token.strip()
        if not word:
            continue
        if word not in seen:
            seen.add(word)
            result.append(word)
    return dlm.join(result)
