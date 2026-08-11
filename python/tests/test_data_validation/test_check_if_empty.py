"""
Tests for sas_utils.data_validation.check_if_empty

Derived from Macro/check_if_empty.sas Usage block.
"""

import pandas as pd
import pytest

from sas_utils.data_validation.check_if_empty import check_if_empty


class TestCheckIfEmpty:
    def test_non_empty(self, sashelp_class):
        assert check_if_empty(sashelp_class) is False

    def test_empty(self):
        df = pd.DataFrame({"x": []})
        assert check_if_empty(df) is True

    def test_with_where_returns_empty(self, sashelp_class):
        assert check_if_empty(sashelp_class, where="Age > 100") is True

    def test_with_where_returns_non_empty(self, sashelp_class):
        assert check_if_empty(sashelp_class, where="Age > 13") is False

    def test_non_dataframe_raises(self):
        with pytest.raises(TypeError, match="Expected a DataFrame"):
            check_if_empty("not a df")
