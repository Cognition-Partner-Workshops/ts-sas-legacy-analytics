"""
Tests for sas_utils.framework.squote

Derived from Macro/squote.sas Usage block.
"""

from sas_utils.framework.squote import squote


class TestSquote:
    def test_basic(self):
        assert squote("Hello") == "'Hello'"

    def test_empty(self):
        assert squote("") == "''"

    def test_default(self):
        assert squote() == "''"

    def test_with_internal_quote(self):
        assert squote("it's") == "'it''s'"

    def test_numeric_string(self):
        assert squote("123") == "'123'"
