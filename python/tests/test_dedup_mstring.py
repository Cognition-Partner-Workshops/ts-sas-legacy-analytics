"""Tests for sas_transforms.dedup_mstring — mirrors SAS %dedup_mstring macro."""

from sas_transforms.dedup_mstring import dedup_mstring


class TestDedupMstring:
    def test_basic_space_delimited(self) -> None:
        """SAS: %let oldstring=C A B B A G E 3 2 1 1 2 3; → 'C A B G E 3 2 1'."""
        result = dedup_mstring("C A B B A G E 3 2 1 1 2 3")
        assert result == "C A B G E 3 2 1"

    def test_comma_delimited_input(self) -> None:
        """SAS: indlm=%str(,) with comma-separated input."""
        result = dedup_mstring(
            "C, A, B, B, A, G, E, 3, 2, 1, 1, 2, 3",
            indlm=",",
        )
        # Output uses same delimiter as input when indlm is single char
        assert result == "C,A,B,G,E,3,2,1"

    def test_comma_input_space_output(self) -> None:
        """SAS: indlm=%str(,), dlm=%str( ) → space-separated output."""
        result = dedup_mstring(
            "C, A, B, B, A, G, E",
            indlm=",",
            dlm=" ",
        )
        assert result == "C A B G E"

    def test_multiple_input_delimiters(self) -> None:
        """SAS: indlm=^#|* — each char is a separate delimiter."""
        result = dedup_mstring(
            "C^A^B^B^A#G#E#3|2|1*1*2*3",
            indlm="^#|*",
        )
        # Multiple indlm chars → output dlm defaults to space
        assert result == "C A B G E 3 2 1"

    def test_multiple_input_delimiters_comma_output(self) -> None:
        """SAS: indlm=^#|*, dlm=%str(,)."""
        result = dedup_mstring(
            "C^A^B^B^A#G#E#3|2|1*1*2*3",
            indlm="^#|*",
            dlm=",",
        )
        assert result == "C,A,B,G,E,3,2,1"

    def test_case_sensitive(self) -> None:
        """dedup_mstring is case-sensitive (matching SAS macro behaviour)."""
        result = dedup_mstring("Hello hello HELLO")
        assert result == "Hello hello HELLO"

    def test_empty_string(self) -> None:
        assert dedup_mstring("") == ""

    def test_multiple_spaces_collapsed(self) -> None:
        """Multiple spaces between tokens are normalised."""
        result = dedup_mstring("C  A  B  B  A  G  E")
        assert result == "C A B G E"

    def test_complex_string_with_quotes(self) -> None:
        """SAS: complex string with single/double quotes and macro keywords."""
        result = dedup_mstring(
            "'PERSON', \"ORGANISATION\",AND,OR,NOT, 'PERSON', 'ORGANISATION'",
            indlm=",",
        )
        assert "'PERSON'" in result
        assert result.count("'PERSON'") == 1
