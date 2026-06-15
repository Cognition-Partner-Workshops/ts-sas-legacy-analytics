"""Tests for sas_transforms.dedup_string — mirrors SAS %dedup_string macro."""

import pandas as pd

from sas_transforms.dedup_string import dedup_string, dedup_string_series


class TestDedupString:
    def test_basic_space_delimited(self) -> None:
        """SAS: oldstring='C A B B A G E 3 2 1 1 2 3' → 'C A B G E 3 2 1'."""
        result = dedup_string("C A B B A G E 3 2 1 1 2 3")
        assert result == "C A B G E 3 2 1"

    def test_pipe_delimited(self) -> None:
        """SAS: dlm=| with 'C|A|B|B|A|G|E|3|2|1|1|2|3'."""
        result = dedup_string("C|A|B|B|A|G|E|3|2|1|1|2|3", dlm="|")
        assert result == "C A B G E 3 2 1"

    def test_case_insensitive(self) -> None:
        """SAS uses UPCASE for comparison — 'a' and 'A' are duplicates."""
        result = dedup_string("Hello hello HELLO world")
        assert result == "Hello world"

    def test_single_token(self) -> None:
        assert dedup_string("only") == "only"

    def test_empty_string(self) -> None:
        assert dedup_string("") == ""

    def test_all_duplicates(self) -> None:
        assert dedup_string("x x x x") == "x"

    def test_preserves_first_occurrence_case(self) -> None:
        """First occurrence's original case is kept."""
        result = dedup_string("Cat CAT cat Dog DOG")
        assert result == "Cat Dog"


class TestDedupStringSeries:
    def test_series_operation(self) -> None:
        s = pd.Series(["A B A", "X Y X Y", None, "Z Z"])
        result = dedup_string_series(s)
        assert result.iloc[0] == "A B"
        assert result.iloc[1] == "X Y"
        assert pd.isna(result.iloc[2])
        assert result.iloc[3] == "Z"
