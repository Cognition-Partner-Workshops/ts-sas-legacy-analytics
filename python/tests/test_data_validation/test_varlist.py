"""
Tests for sas_utils.data_validation.varlist

Derived from Macro/varlist.sas Usage block (lines 40-69).
"""

import pandas as pd
import pytest

from sas_utils.data_validation.varlist import varlist


# ====================================================================
# Test: basic varlist extraction
# From: %put %varlist(sashelp.shoes);
# ====================================================================
class TestVarlist:
    def test_basic_varlist(self, sashelp_shoes):
        result = varlist(sashelp_shoes)
        expected = "Region Product Subsidiary Stores Sales Inventory Returns"
        assert result == expected

    def test_varlist_class(self, sashelp_class):
        result = varlist(sashelp_class)
        assert result == "Name Sex Age Height Weight"

    def test_upcase(self, sashelp_shoes):
        result = varlist(sashelp_shoes, upcase=True)
        expected = "REGION PRODUCT SUBSIDIARY STORES SALES INVENTORY RETURNS"
        assert result == expected

    def test_upcase_class(self, sashelp_class):
        result = varlist(sashelp_class, upcase=True)
        assert result == "NAME SEX AGE HEIGHT WEIGHT"

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = varlist(df)
        assert result == ""

    def test_non_dataframe_raises(self):
        with pytest.raises(TypeError, match="Expected a DataFrame"):
            varlist("not a dataframe")
