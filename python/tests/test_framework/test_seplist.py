"""
Tests for sas_utils.framework.seplist

Derived from Macro/seplist.sas Usage block (lines 50-78).
"""

import pytest

from sas_utils.framework.seplist import seplist


# ====================================================================
# Test: basic comma-separated output
# From: %put %seplist(Hello World); -> Hello,World
# ====================================================================
class TestBasicSeplist:
    def test_default_comma_separator(self):
        result = seplist("Hello World")
        assert result == "Hello,World"

    def test_three_items(self):
        result = seplist("A B C")
        assert result == "A,B,C"

    def test_single_item(self):
        result = seplist("Hello")
        assert result == "Hello"


# ====================================================================
# Test: nest=QQ (double quotes)
# From: %put %seplist(Hello World,nest=QQ); -> "Hello","World"
# ====================================================================
class TestNesting:
    def test_nest_qq(self):
        result = seplist("Hello World", nest="QQ")
        assert result == '"Hello","World"'

    def test_nest_q(self):
        result = seplist("Hello World", nest="Q")
        assert result == "'Hello','World'"

    def test_nest_p(self):
        result = seplist("Hello World", nest="P")
        assert result == "(Hello),(World)"

    def test_nest_b(self):
        result = seplist("Hello World", nest="B")
        assert result == "[Hello],[World]"

    def test_nest_c(self):
        result = seplist("Hello World", nest="C")
        assert result == "{Hello},{World}"


# ====================================================================
# Test: prefix and suffix
# From: %seplist(A B C,prefix=PREFIX_,suffix=_suffix)
#    -> PREFIX_A_suffix,PREFIX_B_suffix,PREFIX_C_suffix
# ====================================================================
class TestPrefixSuffix:
    def test_prefix_suffix(self):
        result = seplist("A B C", prefix="PREFIX_", suffix="_suffix")
        assert result == "PREFIX_A_suffix,PREFIX_B_suffix,PREFIX_C_suffix"

    def test_prefix_only(self):
        result = seplist("A B C", prefix="t.")
        assert result == "t.A,t.B,t.C"

    def test_suffix_only(self):
        result = seplist("A B C", suffix="_var")
        assert result == "A_var,B_var,C_var"


# ====================================================================
# Test: custom output and input delimiters
# ====================================================================
class TestDelimiters:
    def test_custom_output_delimiter(self):
        result = seplist("A B C", dlm=" and ")
        assert result == "A and B and C"

    def test_custom_input_delimiter(self):
        result = seplist("A,B,C", indlm=",")
        assert result == "A,B,C"

    def test_pipe_output(self):
        result = seplist("A B C", dlm="|")
        assert result == "A|B|C"


# ====================================================================
# Test: empty and whitespace
# ====================================================================
class TestEdgeCases:
    def test_empty_string(self):
        result = seplist("")
        assert result == ""

    def test_whitespace_only(self):
        result = seplist("   ")
        assert result == ""
