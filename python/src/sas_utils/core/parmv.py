"""
Parameter validation utility.

Migrated from: Macro/parmv.sas
Original author: Tom Hoffman (09SEP1996)

Provides validate_params() for validating function/method parameters
with support for required checks, allowed value lists, boolean aliases,
numeric validation, and case conversion.
"""

from __future__ import annotations

import functools
from typing import Any, Callable, Optional, Sequence, Union

_BOOL_TRUE = frozenset({"Y", "YES", "TRUE", "T", "ON", "1", True, 1})
_BOOL_FALSE = frozenset({"N", "NO", "FALSE", "F", "OFF", "0", False, 0})


class ParamValidationError(ValueError):
    """Raised when parameter validation fails."""


def _normalize_bool(value: Any) -> bool:
    """Map SAS boolean aliases to Python bool."""
    if isinstance(value, bool):
        return value
    check = str(value).upper().strip()
    if check in {"Y", "YES", "TRUE", "T", "ON", "1"}:
        return True
    if check in {"N", "NO", "FALSE", "F", "OFF", "0"}:
        return False
    raise ParamValidationError(
        f"{value!r} is not a valid boolean value. "
        "Acceptable aliases: Y/YES/TRUE/T/ON/1 or N/NO/FALSE/F/OFF/0"
    )


def validate_params(
    params: dict[str, Any],
    rules: dict[str, dict],
) -> dict[str, Any]:
    """
    Validate a dictionary of parameters against a set of rules.

    Each rule is a dict that may contain:
        - required (bool): If True, param must be non-None and non-empty-string.
        - valid (list): Allowed values. Special strings: "POSITIVE", "NONNEGATIVE".
        - case (str): "upper", "lower", or None.
        - words (bool): If False (default), multi-word values are rejected.
        - default: Default value when param is missing/None.
        - is_bool (bool): If True, normalize to Python bool via SAS aliases.

    Returns a new dict with validated/transformed parameter values.

    Raises ParamValidationError on any validation failure.
    """
    result = dict(params)

    for parm_name, rule in rules.items():
        value = result.get(parm_name)
        default = rule.get("default")
        required = rule.get("required", False)
        valid = rule.get("valid")
        case = rule.get("case")
        words = rule.get("words", True)
        is_bool = rule.get("is_bool", False)

        # Apply default if value is missing
        if value is None or (isinstance(value, str) and value.strip() == ""):
            if default is not None:
                value = default
                result[parm_name] = value

        # Check required
        if required:
            if value is None or (isinstance(value, str) and value.strip() == ""):
                raise ParamValidationError(
                    f"A value for the {parm_name} parameter is required."
                )

        # Nothing more to validate if value is None/empty
        if value is None or (isinstance(value, str) and value.strip() == ""):
            continue

        # Case conversion for strings
        if isinstance(value, str) and case:
            if case == "upper":
                value = value.upper()
            elif case == "lower":
                value = value.lower()
            result[parm_name] = value

        # Boolean alias handling
        if is_bool:
            value = _normalize_bool(value)
            result[parm_name] = value
            continue

        # String-specific validations
        if isinstance(value, str):
            # Multi-word check
            if not words and len(value.split()) > 1:
                raise ParamValidationError(
                    f"{value!r} is not a valid value for the {parm_name} parameter. "
                    f"The {parm_name} parameter may not have multiple values."
                )

            # Validate against allowed values or numeric rules
            if valid is not None:
                _validate_value(parm_name, value, valid, words)
        else:
            # Non-string validations (int/float)
            if valid is not None:
                _validate_value(parm_name, value, valid, words)

    return result


def _validate_value(
    parm_name: str,
    value: Any,
    valid: Union[list, str],
    words: bool,
) -> None:
    """Validate a single value against a valid list or numeric rule."""
    if isinstance(valid, str):
        valid_upper = valid.upper()
    elif isinstance(valid, list) and len(valid) == 1 and isinstance(valid[0], str):
        valid_upper = valid[0].upper()
    else:
        valid_upper = None

    # POSITIVE integer check
    if valid_upper == "POSITIVE":
        _check_positive(parm_name, value)
        return

    # NONNEGATIVE integer check
    if valid_upper == "NONNEGATIVE":
        _check_nonnegative(parm_name, value)
        return

    # List-of-allowed-values check
    if isinstance(valid, (list, tuple, set, frozenset)):
        if isinstance(value, str) and words:
            for word in value.split():
                if word not in valid:
                    raise ParamValidationError(
                        f"{word!r} is not a valid value for the {parm_name} parameter. "
                        f"Allowable values are: {', '.join(str(v) for v in valid)}."
                    )
        else:
            check_val = value
            if isinstance(check_val, str):
                check_val = check_val.strip()
            if check_val not in valid:
                raise ParamValidationError(
                    f"{value!r} is not a valid value for the {parm_name} parameter. "
                    f"Allowable values are: {', '.join(str(v) for v in valid)}."
                )


def _check_positive(parm_name: str, value: Any) -> None:
    """Validate that value is a positive integer."""
    try:
        int_val = int(value)
    except (ValueError, TypeError):
        raise ParamValidationError(
            f"{value!r} is not a valid value for the {parm_name} parameter. "
            "Only positive integers are allowed."
        )
    if int_val <= 0:
        raise ParamValidationError(
            f"{value!r} is not a valid value for the {parm_name} parameter. "
            "Only positive integers are allowed."
        )


def _check_nonnegative(parm_name: str, value: Any) -> None:
    """Validate that value is a non-negative integer."""
    try:
        int_val = int(value)
    except (ValueError, TypeError):
        raise ParamValidationError(
            f"{value!r} is not a valid value for the {parm_name} parameter. "
            "Only non-negative integers are allowed."
        )
    if int_val < 0:
        raise ParamValidationError(
            f"{value!r} is not a valid value for the {parm_name} parameter. "
            "Only non-negative integers are allowed."
        )


def validated(rules: dict[str, dict]) -> Callable:
    """
    Decorator that validates keyword arguments of a function using validate_params.

    Usage:
        @validated({"interval": {"required": True, "words": False},
                    "high": {"required": True, "is_bool": True}})
        def my_func(interval, high=False):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            validated_args = validate_params(dict(bound.arguments), rules)
            return func(**validated_args)
        return wrapper
    return decorator
