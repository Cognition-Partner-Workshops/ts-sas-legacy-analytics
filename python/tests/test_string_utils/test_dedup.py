"""
Tests for sas_utils.string_utils.dedup

Derived from Macro/dedup_string.sas Usage block (lines 37-61).
"""

from sas_utils.string_utils.dedup import dedup_string


# ====================================================================
# Test: dedup space-separated string
# From: oldstring="C A B B A G E 3 2 1 1 2 3" -> "C A B G E 3 2 1"
# ====================================================================
class TestDedupString:
    def test_basic_dedup(self):
        result = dedup_string("C A B B A G E 3 2 1 1 2 3")
        assert result == "C A B G E 3 2 1"

    def test_no_duplicates(self):
        result = dedup_string("A B C")
        assert result == "A B C"

    def test_all_same(self):
        result = dedup_string("A A A")
        assert result == "A"

    def test_empty_string(self):
        result = dedup_string("")
        assert result == ""


# ====================================================================
# Test: dedup with custom delimiter
# From: oldstring="C|A|B|B|A|G|E" with dlm=|
# ====================================================================
class TestDedupCustomDelimiter:
    def test_pipe_delimiter(self):
        result = dedup_string("C|A|B|B|A|G|E|3|2|1|1|2|3", dlm="|")
        assert result == "C|A|B|G|E|3|2|1"

    def test_comma_delimiter(self):
        result = dedup_string("X,Y,Z,X,Y", dlm=",")
        assert result == "X,Y,Z"


# ====================================================================
# Test: case-insensitive dedup (preserves first occurrence case)
# ====================================================================
class TestDedupCaseInsensitive:
    def test_mixed_case(self):
        result = dedup_string("Hello hello HELLO world")
        assert result == "Hello world"
