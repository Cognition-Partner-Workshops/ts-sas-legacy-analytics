"""
Variable scope lookup utility.

Migrated from: Macro/symget.sas
Original author: Tom Abernathy / Scott Bass (08APR2011)

In SAS, %symget retrieves a global macro variable hidden by a local one.
In Python, this maps to a namespace/scope registry for variable lookup.
"""

from __future__ import annotations

from typing import Any, Optional


class VariableRegistry:
    """
    A scoped variable registry mimicking SAS macro variable scoping.

    Supports GLOBAL and named scopes, with include/exclude filtering.
    """

    def __init__(self) -> None:
        self._scopes: dict[str, dict[str, Any]] = {"GLOBAL": {}}

    def set_var(self, name: str, value: Any, scope: str = "GLOBAL") -> None:
        """Set a variable in the given scope."""
        scope = scope.upper()
        if scope not in self._scopes:
            self._scopes[scope] = {}
        self._scopes[scope][name.upper()] = value

    def get_var(
        self,
        name: str,
        include: Optional[list[str]] = None,
        exclude: Optional[list[str]] = None,
    ) -> Any:
        """
        Get a variable value, searching scopes with optional filtering.

        Parameters
        ----------
        name : str
            Variable name to look up (case-insensitive).
        include : list of str, optional
            If provided, only search these scopes.
        exclude : list of str, optional
            If provided, skip these scopes during search.

        Returns
        -------
        Any
            The variable value.

        Raises
        ------
        KeyError
            If the variable is not found in any searched scope.
        """
        name_upper = name.upper()

        if include:
            search_scopes = [s.upper() for s in include]
        elif exclude:
            exclude_upper = {s.upper() for s in exclude}
            search_scopes = [s for s in self._scopes if s not in exclude_upper]
        else:
            search_scopes = ["GLOBAL"]

        for scope in search_scopes:
            if scope in self._scopes and name_upper in self._scopes[scope]:
                return self._scopes[scope][name_upper]

        raise KeyError(f"Variable {name!r} not found in searched scopes")

    def exists(self, name: str, scope: Optional[str] = None) -> bool:
        """Check if a variable exists in any scope or a specific scope."""
        name_upper = name.upper()
        if scope:
            return name_upper in self._scopes.get(scope.upper(), {})
        return any(name_upper in vars_ for vars_ in self._scopes.values())

    def list_vars(self, scope: Optional[str] = None) -> dict[str, Any]:
        """List all variables, optionally filtered by scope."""
        if scope:
            return dict(self._scopes.get(scope.upper(), {}))
        result = {}
        for scope_vars in self._scopes.values():
            result.update(scope_vars)
        return result
