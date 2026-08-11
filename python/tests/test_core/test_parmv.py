"""
Tests for sas_utils.core.parmv

Derived from Macro/parmv.sas Usage block (lines 68-92).
"""

import pytest

from sas_utils.core.parmv import (
    ParamValidationError,
    _normalize_bool,
    validate_params,
    validated,
)


# ====================================================================
# Test: required param missing -> raises error
# ====================================================================
class TestRequiredParams:
    def test_required_missing_raises(self):
        rules = {"INTERVAL": {"required": True, "words": False}}
        with pytest.raises(ParamValidationError, match="INTERVAL.*required"):
            validate_params({"INTERVAL": None}, rules)

    def test_required_empty_string_raises(self):
        rules = {"INTERVAL": {"required": True, "words": False}}
        with pytest.raises(ParamValidationError, match="INTERVAL.*required"):
            validate_params({"INTERVAL": ""}, rules)

    def test_required_blank_string_raises(self):
        rules = {"INTERVAL": {"required": True, "words": False}}
        with pytest.raises(ParamValidationError, match="INTERVAL.*required"):
            validate_params({"INTERVAL": "   "}, rules)

    def test_required_present_passes(self):
        rules = {"INTERVAL": {"required": True, "words": False}}
        result = validate_params({"INTERVAL": "MONTH"}, rules)
        assert result["INTERVAL"] == "MONTH"


# ====================================================================
# Test: invalid value not in allowed list -> raises error
# ====================================================================
class TestAllowedValues:
    def test_invalid_value_raises(self):
        rules = {"HIGH": {"required": True, "valid": ["0", "1"], "words": False}}
        with pytest.raises(ParamValidationError, match="not a valid value"):
            validate_params({"HIGH": "2"}, rules)

    def test_valid_value_passes(self):
        rules = {"HIGH": {"required": True, "valid": ["0", "1"], "words": False}}
        result = validate_params({"HIGH": "1"}, rules)
        assert result["HIGH"] == "1"

    def test_valid_value_zero(self):
        rules = {"PRINT": {"required": True, "valid": ["0", "1"], "words": False}}
        result = validate_params({"PRINT": "0"}, rules)
        assert result["PRINT"] == "0"


# ====================================================================
# Test: boolean aliases YES/Y/TRUE/T/ON -> True, NO/N/FALSE/F/OFF -> False
# ====================================================================
class TestBooleanAliases:
    @pytest.mark.parametrize("value", ["YES", "Y", "TRUE", "T", "ON", "1",
                                        "yes", "y", "true", "t", "on"])
    def test_true_aliases(self, value):
        rules = {"REPLACE": {"is_bool": True}}
        result = validate_params({"REPLACE": value}, rules)
        assert result["REPLACE"] is True

    @pytest.mark.parametrize("value", ["NO", "N", "FALSE", "F", "OFF", "0",
                                        "no", "n", "false", "f", "off"])
    def test_false_aliases(self, value):
        rules = {"REPLACE": {"is_bool": True}}
        result = validate_params({"REPLACE": value}, rules)
        assert result["REPLACE"] is False

    def test_invalid_boolean_raises(self):
        rules = {"REPLACE": {"is_bool": True}}
        with pytest.raises(ParamValidationError, match="not a valid boolean"):
            validate_params({"REPLACE": "MAYBE"}, rules)

    def test_bool_true_passthrough(self):
        assert _normalize_bool(True) is True
        assert _normalize_bool(False) is False


# ====================================================================
# Test: POSITIVE validation rejects 0 and negatives
# ====================================================================
class TestPositiveValidation:
    def test_positive_rejects_zero(self):
        rules = {"COUNT": {"required": True, "valid": "POSITIVE"}}
        with pytest.raises(ParamValidationError, match="positive integers"):
            validate_params({"COUNT": "0"}, rules)

    def test_positive_rejects_negative(self):
        rules = {"COUNT": {"required": True, "valid": "POSITIVE"}}
        with pytest.raises(ParamValidationError, match="positive integers"):
            validate_params({"COUNT": "-5"}, rules)

    def test_positive_accepts_positive(self):
        rules = {"COUNT": {"required": True, "valid": "POSITIVE"}}
        result = validate_params({"COUNT": "3"}, rules)
        assert result["COUNT"] == "3"

    def test_positive_rejects_non_numeric(self):
        rules = {"COUNT": {"required": True, "valid": "POSITIVE"}}
        with pytest.raises(ParamValidationError, match="positive integers"):
            validate_params({"COUNT": "abc"}, rules)


# ====================================================================
# Test: NONNEGATIVE validation accepts 0, rejects negatives
# ====================================================================
class TestNonnegativeValidation:
    def test_nonnegative_accepts_zero(self):
        rules = {"COUNT": {"required": True, "valid": "NONNEGATIVE"}}
        result = validate_params({"COUNT": "0"}, rules)
        assert result["COUNT"] == "0"

    def test_nonnegative_rejects_negative(self):
        rules = {"COUNT": {"required": True, "valid": "NONNEGATIVE"}}
        with pytest.raises(ParamValidationError, match="non-negative integers"):
            validate_params({"COUNT": "-1"}, rules)

    def test_nonnegative_accepts_positive(self):
        rules = {"COUNT": {"required": True, "valid": "NONNEGATIVE"}}
        result = validate_params({"COUNT": "5"}, rules)
        assert result["COUNT"] == "5"


# ====================================================================
# Test: case conversion (upper/lower)
# ====================================================================
class TestCaseConversion:
    def test_case_upper(self):
        rules = {"DBMS": {"case": "upper"}}
        result = validate_params({"DBMS": "xlsx"}, rules)
        assert result["DBMS"] == "XLSX"

    def test_case_lower(self):
        rules = {"NAME": {"case": "lower"}}
        result = validate_params({"NAME": "HELLO"}, rules)
        assert result["NAME"] == "hello"

    def test_case_none(self):
        rules = {"DATA": {"case": None}}
        result = validate_params({"DATA": "MixedCase"}, rules)
        assert result["DATA"] == "MixedCase"


# ====================================================================
# Test: _words=False rejects multi-word values
# ====================================================================
class TestWordsValidation:
    def test_words_false_rejects_multi_word(self):
        rules = {"INTERVAL": {"required": True, "words": False}}
        with pytest.raises(ParamValidationError, match="may not have multiple"):
            validate_params({"INTERVAL": "hello world"}, rules)

    def test_words_false_accepts_single_word(self):
        rules = {"INTERVAL": {"required": True, "words": False}}
        result = validate_params({"INTERVAL": "MONTH"}, rules)
        assert result["INTERVAL"] == "MONTH"

    def test_words_true_accepts_multi_word(self):
        rules = {"IVAR": {"required": True, "words": True}}
        result = validate_params({"IVAR": "hello world"}, rules)
        assert result["IVAR"] == "hello world"


# ====================================================================
# Test: default values
# ====================================================================
class TestDefaults:
    def test_default_applied_when_none(self):
        rules = {"REPLACE": {"default": "N"}}
        result = validate_params({"REPLACE": None}, rules)
        assert result["REPLACE"] == "N"

    def test_default_applied_when_empty(self):
        rules = {"REPLACE": {"default": "N"}}
        result = validate_params({"REPLACE": ""}, rules)
        assert result["REPLACE"] == "N"

    def test_default_not_applied_when_value_present(self):
        rules = {"REPLACE": {"default": "N"}}
        result = validate_params({"REPLACE": "Y"}, rules)
        assert result["REPLACE"] == "Y"


# ====================================================================
# Test: @validated decorator
# ====================================================================
class TestDecorator:
    def test_validated_decorator_passes(self):
        @validated({"name": {"required": True, "words": False}})
        def greet(name):
            return f"Hello, {name}"

        assert greet(name="World") == "Hello, World"

    def test_validated_decorator_raises_on_missing(self):
        @validated({"name": {"required": True}})
        def greet(name=None):
            return f"Hello, {name}"

        with pytest.raises(ParamValidationError):
            greet()

    def test_validated_decorator_with_case(self):
        @validated({"mode": {"case": "upper"}})
        def process(mode="default"):
            return mode

        assert process(mode="fast") == "FAST"
