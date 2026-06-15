"""Python equivalent of Macro/dedup_mstring.sas.

SAS macro signature:
    %dedup_mstring(IN, INDLM=, DLM=)

This is a *macro-level* dedup (operates during SAS compilation, not at
data-step runtime).  In Python the distinction is irrelevant — both
``dedup_string`` and ``dedup_mstring`` reduce to the same algorithm on
a plain string.  The key behavioural difference is that dedup_mstring
supports separate input and output delimiters and works on arbitrary
text (not tied to a DataFrame row).
"""

from __future__ import annotations

from typing import Optional


def dedup_mstring(
    value: str,
    *,
    indlm: Optional[str] = None,
    dlm: Optional[str] = None,
) -> str:
    """Remove duplicate tokens from a macro-variable-style string.

    Parameters
    ----------
    value : str
        Input string.
    indlm : str, optional
        Input delimiter(s).  If the string is ``None`` or empty a single
        space is used.  When *indlm* contains multiple characters, each
        character is treated as a potential delimiter (matching SAS
        ``%scan`` behaviour with a multi-char delimiter list).
    dlm : str, optional
        Output delimiter.  If not specified:
        * len(indlm) == 1 → use *indlm*.
        * len(indlm) > 1  → use a single space.

    Returns
    -------
    str
        Deduplicated string joined by *dlm*.
    """
    if indlm is None or indlm == "":
        indlm = " "

    if dlm is None:
        dlm = indlm if len(indlm) == 1 else " "

    import re
    if len(indlm) == 1:
        tokens = value.split(indlm)
    else:
        pattern = "[" + re.escape(indlm) + "]"
        tokens = re.split(pattern, value)

    seen: set[str] = set()
    result: list[str] = []
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        key = token.upper()
        if key not in seen:
            seen.add(key)
            result.append(token)

    return dlm.join(result)
