"""
Tests for sas_utils.string_utils.splitvar
"""

from sas_utils.string_utils.splitvar import splitvar


class TestSplitvar:
    def test_whitespace_split(self):
        assert splitvar("A B C") == ["A", "B", "C"]

    def test_custom_delimiter(self):
        assert splitvar("A,B,C", dlm=",") == ["A", "B", "C"]

    def test_fixed_width(self):
        assert splitvar("AABBCC", width=2) == ["AA", "BB", "CC"]

    def test_single_item(self):
        assert splitvar("Hello") == ["Hello"]

    def test_empty_string(self):
        assert splitvar("") == []
