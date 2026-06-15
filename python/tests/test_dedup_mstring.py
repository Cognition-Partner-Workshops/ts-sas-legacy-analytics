"""Tests for sas_transforms.dedup_mstring — mirrors SAS %dedup_mstring macro."""

import pytest

from sas_transforms.dedup_mstring import dedup_mstring


class TestDedupMstring:
    def test_space_delimited(self):
        """SAS example: 'C A B B A G E 3 2 1 1 2 3' → 'C A B G E 3 2 1'."""
        result = dedup_mstring("C A B B A G E 3 2 1 1 2 3")
        assert result == "C A B G E 3 2 1"

    def test_comma_delimited(self):
        """SAS example with comma input delimiter."""
        result = dedup_mstring("C, A, B, B, A, G, E, 3, 2, 1, 1, 2, 3", indlm=",")
        assert result == "C,A,B,G,E,3,2,1"

    def test_comma_indlm_space_outdlm(self):
        """SAS: indlm=comma, dlm=space."""
        result = dedup_mstring(
            "C, A, B, B, A, G, E, 3, 2, 1, 1, 2, 3",
            indlm=",", dlm=" ",
        )
        assert result == "C A B G E 3 2 1"

    def test_multi_char_delimiter(self):
        """SAS example: multiple input delimiters '^#|*'."""
        result = dedup_mstring("C^A^B^B^A#G#E#3|2|1*1*2*3", indlm="^#|*")
        assert result == "C A B G E 3 2 1"

    def test_multi_char_indlm_comma_outdlm(self):
        result = dedup_mstring(
            "C^A^B^B^A#G#E#3|2|1*1*2*3", indlm="^#|*", dlm=","
        )
        assert result == "C,A,B,G,E,3,2,1"

    def test_case_insensitive(self):
        """SAS %dedup_mstring is case-insensitive (indexw/upcase)."""
        result = dedup_mstring("hello Hello HELLO world")
        assert result == "hello world"

    def test_empty_string(self):
        assert dedup_mstring("") == ""

    def test_no_duplicates(self):
        assert dedup_mstring("A B C") == "A B C"

    def test_single_char_indlm_becomes_outdlm(self):
        """When indlm is single char and dlm not specified, output uses indlm."""
        result = dedup_mstring("a|b|a", indlm="|")
        assert result == "a|b"

    def test_complex_quoted_string(self):
        """SAS example with quoted strings and macro keywords."""
        result = dedup_mstring(
            "'PERSON', \"ORGANISATION\",AND,OR,NOT, 'PERSON', 'ORGANISATION'",
            indlm=",",
        )
        assert "'PERSON'" in result
        assert result.count("'PERSON'") == 1
