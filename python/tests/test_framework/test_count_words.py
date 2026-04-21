"""
Tests for sas_utils.framework.count_words

Derived from Macro/count_words.sas Usage block.
"""

import pytest

from sas_utils.framework.count_words import count_words


class TestCountWords:
    def test_space_separated(self):
        assert count_words("Hello World") == 2

    def test_three_words(self):
        assert count_words("A B C") == 3

    def test_single_word(self):
        assert count_words("Hello") == 1

    def test_empty_string(self):
        assert count_words("") == 0

    def test_blank_string(self):
        assert count_words("   ") == 0

    def test_custom_delimiter(self):
        assert count_words("A,B,C", dlm=",") == 3

    def test_multiple_delimiters(self):
        assert count_words("A,B;C", dlm=",;") == 3

    def test_extra_spaces(self):
        assert count_words("  A  B  C  ") == 3
