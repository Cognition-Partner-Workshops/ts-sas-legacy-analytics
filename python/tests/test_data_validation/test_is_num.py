"""
Tests for sas_utils.data_validation.is_num

Derived from Macro/IsNum.sas Usage block (lines 46-84).
"""

import pandas as pd
import pytest

from sas_utils.data_validation.is_num import is_num


# ====================================================================
# Test data from IsNum.sas datalines block
# ====================================================================
class TestIsNum:
    @pytest.fixture
    def test_series(self):
        return pd.Series([
            ".", "._", ".A", "-1", "0", "1", "1.1",
            "-1.1", "1.1.1", "1A", "A", "", " ", "1 000",
        ])

    def test_integer_one(self):
        result = is_num(pd.Series(["1"]))
        assert result["IsNum"].iloc[0] == True
        assert result["IsInt"].iloc[0] == True
        assert result["IsFloat"].iloc[0] == False
        assert result["IsPos"].iloc[0] == True
        assert result["IsNonNeg"].iloc[0] == True

    def test_float_1_1(self):
        result = is_num(pd.Series(["1.1"]))
        assert result["IsNum"].iloc[0] == True
        assert result["IsInt"].iloc[0] == False
        assert result["IsFloat"].iloc[0] == True
        assert result["IsPos"].iloc[0] == True

    def test_negative_one(self):
        result = is_num(pd.Series(["-1"]))
        assert result["IsNum"].iloc[0] == True
        assert result["IsNonNeg"].iloc[0] == False
        assert result["IsPos"].iloc[0] == False

    def test_zero(self):
        result = is_num(pd.Series(["0"]))
        assert result["IsNum"].iloc[0] == True
        assert result["IsInt"].iloc[0] == True
        assert result["IsNonNeg"].iloc[0] == True
        assert result["IsPos"].iloc[0] == False

    def test_letter_a(self):
        result = is_num(pd.Series(["A"]))
        assert result["IsNum"].iloc[0] == False
        assert result["IsNum2"].iloc[0] == False
        assert result["IsInt"].iloc[0] == False

    def test_sas_missing_dot(self):
        """SAS missing value '.' should be IsNum=False, IsNum2=True."""
        result = is_num(pd.Series(["."]))
        assert result["IsNum"].iloc[0] == False
        assert result["IsNum2"].iloc[0] == True

    def test_sas_missing_dot_underscore(self):
        """SAS special missing '._' should be IsNum=False, IsNum2=True."""
        result = is_num(pd.Series(["._"]))
        assert result["IsNum"].iloc[0] == False
        assert result["IsNum2"].iloc[0] == True

    def test_sas_missing_dot_letter(self):
        """SAS special missing '.A' should be IsNum=False, IsNum2=True."""
        result = is_num(pd.Series([".A"]))
        assert result["IsNum"].iloc[0] == False
        assert result["IsNum2"].iloc[0] == True

    def test_empty_string(self):
        """Empty string should be IsNum=False, IsNum2=True."""
        result = is_num(pd.Series([""]))
        assert result["IsNum"].iloc[0] == False
        assert result["IsNum2"].iloc[0] == True

    def test_invalid_number_format(self):
        """'1.1.1' is not a valid number."""
        result = is_num(pd.Series(["1.1.1"]))
        assert result["IsNum"].iloc[0] == False

    def test_mixed_alpha_numeric(self):
        """'1A' is not a valid number."""
        result = is_num(pd.Series(["1A"]))
        assert result["IsNum"].iloc[0] == False

    def test_negative_float(self):
        result = is_num(pd.Series(["-1.1"]))
        assert result["IsNum"].iloc[0] == True
        assert result["IsFloat"].iloc[0] == True
        assert result["IsNonNeg"].iloc[0] == False

    def test_batch_processing(self, test_series):
        result = is_num(test_series)
        assert len(result) == len(test_series)
        assert list(result.columns) == [
            "IsNum", "IsNum2", "IsInt", "IsFloat", "IsNonNeg", "IsPos",
        ]
