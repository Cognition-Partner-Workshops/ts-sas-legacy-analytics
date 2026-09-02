"""Validation helpers corresponding to the SAS ``_parmv`` macro."""

from __future__ import annotations

import re
from collections.abc import Iterable


class ParamError(ValueError):
    """Raised when a macro parameter does not satisfy its contract."""


_ALIASES = {
    "N": "0",
    "NO": "0",
    "F": "0",
    "FALSE": "0",
    "OFF": "0",
    "Y": "1",
    "YES": "1",
    "T": "1",
    "TRUE": "1",
    "ON": "1",
}


def _format(value: str, case: str) -> str:
    if case.upper() == "U":
        return value.upper()
    if case.upper() == "L":
        return value.lower()
    return value


def validate_param(
    name: str,
    value: object,
    *,
    required: bool = False,
    allowed: Iterable[str] | str | None = None,
    words: bool = False,
    case: str = "U",
    default: object | None = None,
) -> str:
    """Normalize and validate a macro-like parameter value."""

    param_name = name.upper()
    raw = "" if value is None else str(value).strip()
    if not raw:
        if required:
            raise ParamError(f"Macro parameter {param_name} is required")
        if default is None:
            return ""
        raw = str(default).strip()
    if not words and re.search(r"\s", raw):
        raise ParamError(f"Macro parameter {param_name} must be a single word")

    normalized = _format(raw, case)
    alias = _ALIASES.get(normalized.upper())
    if alias is not None:
        normalized = alias

    if allowed is not None:
        if isinstance(allowed, str) and allowed.upper() in {"POSITIVE", "NONNEGATIVE"}:
            try:
                numeric = float(normalized)
            except ValueError as exc:
                raise ParamError(f"Macro parameter {param_name} must be numeric") from exc
            if allowed.upper() == "POSITIVE" and numeric <= 0:
                raise ParamError(f"Macro parameter {param_name} must be positive")
            if allowed.upper() == "NONNEGATIVE" and numeric < 0:
                raise ParamError(f"Macro parameter {param_name} must be nonnegative")
        else:
            choices = [str(item).strip() for item in allowed] if not isinstance(allowed, str) else allowed.split()
            normalized_choices = {_format(item, case) for item in choices}
            if normalized not in normalized_choices:
                raise ParamError(f"Allowable values are: {', '.join(choices)}")
    return normalized
