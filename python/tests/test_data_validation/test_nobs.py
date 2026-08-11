"""
Tests for sas_utils.data_validation.nobs

Derived from Macro/nobs.sas Usage block (lines 40-99).
"""

import pandas as pd
import pytest

from sas_utils.data_validation.nobs import nobs


# ====================================================================
# Test: basic observation count
# From: %let foo=%nobs(work.foo);
# ====================================================================
class TestNobs:
    def test_basic_count(self, sashelp_class):
        assert nobs(sashelp_class) == 19

    def test_shoes_count(self, sashelp_shoes):
        assert nobs(sashelp_shoes) == 20

    def test_stocks_count(self, sashelp_stocks):
        assert nobs(sashelp_stocks) == 12

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        assert nobs(df) == 0


# ====================================================================
# Test: with where clause
# From: %nobs(work.foo (where=(uniform(0) le .5)), mvar=mymvar)
# ====================================================================
class TestNobsWhere:
    def test_where_clause(self, sashelp_class):
        count = nobs(sashelp_class, where="Age > 13")
        assert count > 0
        assert count < 19

    def test_where_clause_all_match(self, sashelp_class):
        count = nobs(sashelp_class, where="Age > 0")
        assert count == 19

    def test_where_clause_none_match(self, sashelp_class):
        count = nobs(sashelp_class, where="Age > 100")
        assert count == 0

    def test_where_sex_filter(self, sashelp_class):
        count_m = nobs(sashelp_class, where='Sex == "M"')
        count_f = nobs(sashelp_class, where='Sex == "F"')
        assert count_m + count_f == 19

    def test_invalid_where_raises(self, sashelp_class):
        with pytest.raises(ValueError, match="Invalid where clause"):
            nobs(sashelp_class, where="INVALID SYNTAX !!!")


# ====================================================================
# Test: error handling
# ====================================================================
class TestNobsErrors:
    def test_non_dataframe_raises(self):
        with pytest.raises(TypeError, match="Expected a DataFrame"):
            nobs("not a dataframe")
