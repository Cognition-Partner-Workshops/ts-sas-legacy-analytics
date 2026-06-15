"""Tests for sas_transforms.dedup_string — mirrors SAS %dedup_string macro."""

import pandas as pd
import pytest

from sas_transforms.dedup_string import dedup_string, dedup_string_series


class TestDedupString:
    def test_basic_space_delimited(self):
        """SAS example: 'C A B B A G E 3 2 1 1 2 3' → 'C A B G E 3 2 1'."""
        result = dedup_string("C A B B A G E 3 2 1 1 2 3")
        assert result == "C A B G E 3 2 1"

    def test_case_insensitive_default(self):
        """SAS uses ``upcase`` comparison — 'a' and 'A' are duplicates."""
        result = dedup_string("a A b B")
        assert result == "a b"

    def test_case_sensitive(self):
        result = dedup_string("a A b B", case_sensitive=True)
        assert result == "a A b B"

    def test_custom_delimiter(self):
        """SAS example with pipe delimiter."""
        result = dedup_string("C|A|B|B|A|G|E|3|2|1|1|2|3", dlm="|")
        assert result == "C A B G E 3 2 1"

    def test_single_token(self):
        assert dedup_string("hello") == "hello"

    def test_empty_string(self):
        assert dedup_string("") == ""

    def test_all_duplicates(self):
        assert dedup_string("x x x x") == "x"


class TestDedupStringSeries:
    def test_vectorised_apply(self):
        s = pd.Series(["A B A", "X Y X Y", "one two one"])
        result = dedup_string_series(s)
        assert result.iloc[0] == "A B"
        assert result.iloc[1] == "X Y"
        assert result.iloc[2] == "one two"

    def test_handles_nan(self):
        s = pd.Series(["A B A", None, "X X"])
        result = dedup_string_series(s)
        assert pd.isna(result.iloc[1])
        assert result.iloc[2] == "X"
