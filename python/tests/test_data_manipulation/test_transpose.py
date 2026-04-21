"""
Tests for sas_utils.data_manipulation.transpose

Derived from Macro/transpose.sas Usage block (lines 34-86).
"""

import pandas as pd
import pytest

from sas_utils.data_manipulation.transpose import transpose


# ====================================================================
# Test: transpose by groups with variable renaming
# From: transpose(data=in, out=out, by=studyid, var=diabp height...)
# ====================================================================
class TestTranspose:
    @pytest.fixture
    def wide_data(self):
        return pd.DataFrame({
            "subject": ["S1", "S1", "S2", "S2"],
            "visit": ["V1", "V2", "V1", "V2"],
            "diabp": [80, 82, 75, 78],
            "sysbp": [120, 122, 115, 118],
            "pulse": [72, 74, 68, 70],
        })

    def test_basic_transpose(self, wide_data):
        result = transpose(
            data=wide_data,
            var=["diabp", "sysbp", "pulse"],
            by=["subject", "visit"],
        )
        assert "_NAME_" in result.columns
        assert "COL1" in result.columns
        assert len(result) == 12  # 4 rows * 3 vars

    def test_custom_name_col(self, wide_data):
        result = transpose(
            data=wide_data,
            var=["diabp", "sysbp"],
            by=["subject", "visit"],
            name="measure",
            col="value",
        )
        assert "measure" in result.columns
        assert "value" in result.columns

    def test_single_var(self, wide_data):
        result = transpose(
            data=wide_data,
            var="diabp",
            by="subject visit",
        )
        assert len(result) == 4

    def test_no_by_vars(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6]})
        result = transpose(data=df, var=["a", "b", "c"])
        assert len(result) == 6  # 2 rows * 3 vars

    def test_notsorted(self, wide_data):
        result = transpose(
            data=wide_data,
            var=["diabp", "sysbp"],
            by=["subject", "visit"],
            notsorted=True,
        )
        assert len(result) == 8

    def test_string_var_input(self, wide_data):
        result = transpose(
            data=wide_data,
            var="diabp sysbp pulse",
            by="subject visit",
        )
        assert len(result) == 12
