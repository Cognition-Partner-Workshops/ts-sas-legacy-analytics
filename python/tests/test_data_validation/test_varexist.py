"""
Tests for sas_utils.data_validation.varexist

Derived from Macro/varexist.sas Usage block.
"""

import pandas as pd
import pytest

from sas_utils.data_validation.varexist import varexist


class TestVarexist:
    def test_column_exists(self, sashelp_class):
        assert varexist(sashelp_class, "Name") is True

    def test_column_not_exists(self, sashelp_class):
        assert varexist(sashelp_class, "DoesNotExist") is False

    def test_column_position(self, sashelp_class):
        assert varexist(sashelp_class, "Name", info="num") == 1
        assert varexist(sashelp_class, "Age", info="num") == 3

    def test_column_type_numeric(self, sashelp_class):
        assert varexist(sashelp_class, "Age", info="type") == "N"

    def test_column_type_character(self, sashelp_class):
        assert varexist(sashelp_class, "Name", info="type") == "C"

    def test_not_exists_with_info(self, sashelp_class):
        assert varexist(sashelp_class, "Missing", info="num") == 0

    def test_non_dataframe(self):
        assert varexist("not a df", "col") is False

    def test_dtype_info(self, sashelp_class):
        result = varexist(sashelp_class, "Age", info="dtype")
        assert "int" in result
