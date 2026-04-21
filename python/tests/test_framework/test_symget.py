"""
Tests for sas_utils.framework.symget (VariableRegistry)

Derived from Macro/symget.sas Usage block.
"""

import pytest

from sas_utils.framework.symget import VariableRegistry


class TestVariableRegistry:
    def test_set_and_get_global(self):
        reg = VariableRegistry()
        reg.set_var("X", 42)
        assert reg.get_var("X") == 42

    def test_case_insensitive(self):
        reg = VariableRegistry()
        reg.set_var("MyVar", "hello")
        assert reg.get_var("myvar") == "hello"

    def test_scoped_variable(self):
        reg = VariableRegistry()
        reg.set_var("X", "global", scope="GLOBAL")
        reg.set_var("X", "local", scope="LOCAL")
        assert reg.get_var("X", include=["LOCAL"]) == "local"
        assert reg.get_var("X", include=["GLOBAL"]) == "global"

    def test_exclude_scope(self):
        reg = VariableRegistry()
        reg.set_var("X", "global", scope="GLOBAL")
        reg.set_var("X", "local", scope="LOCAL")
        assert reg.get_var("X", exclude=["LOCAL"]) == "global"

    def test_not_found_raises(self):
        reg = VariableRegistry()
        with pytest.raises(KeyError):
            reg.get_var("MISSING")

    def test_exists(self):
        reg = VariableRegistry()
        reg.set_var("X", 1)
        assert reg.exists("X") is True
        assert reg.exists("Y") is False

    def test_exists_in_scope(self):
        reg = VariableRegistry()
        reg.set_var("X", 1, scope="LOCAL")
        assert reg.exists("X", scope="LOCAL") is True
        assert reg.exists("X", scope="GLOBAL") is False

    def test_list_vars(self):
        reg = VariableRegistry()
        reg.set_var("A", 1)
        reg.set_var("B", 2)
        result = reg.list_vars()
        assert result == {"A": 1, "B": 2}

    def test_list_vars_scoped(self):
        reg = VariableRegistry()
        reg.set_var("A", 1, scope="GLOBAL")
        reg.set_var("B", 2, scope="LOCAL")
        assert reg.list_vars(scope="GLOBAL") == {"A": 1}
        assert reg.list_vars(scope="LOCAL") == {"B": 2}
