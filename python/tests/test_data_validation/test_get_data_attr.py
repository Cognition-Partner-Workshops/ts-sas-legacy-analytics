"""
Tests for sas_utils.data_validation.get_data_attr

Derived from Macro/get_data_attr.sas Usage block.
"""

import pandas as pd
import pytest

from sas_utils.data_validation.get_data_attr import get_data_attr


class TestGetDataAttr:
    def test_nobs(self, sashelp_class):
        assert get_data_attr(sashelp_class, "nobs") == 19

    def test_nvars(self, sashelp_class):
        assert get_data_attr(sashelp_class, "nvars") == 5

    def test_type(self, sashelp_class):
        assert get_data_attr(sashelp_class, "type") == "DATA"

    def test_label(self):
        df = pd.DataFrame({"x": [1]})
        df.attrs["label"] = "Test Dataset"
        assert get_data_attr(df, "label") == "Test Dataset"

    def test_label_default(self, sashelp_class):
        assert get_data_attr(sashelp_class, "label") == ""

    def test_engine(self, sashelp_class):
        assert get_data_attr(sashelp_class, "engine") == "PANDAS"

    def test_invalid_attr(self, sashelp_class):
        with pytest.raises(ValueError, match="not a recognized attribute"):
            get_data_attr(sashelp_class, "invalid")

    def test_non_dataframe(self):
        with pytest.raises(TypeError):
            get_data_attr("not a df", "nobs")
