"""
Tests for sas_utils.framework.dump_mvars

Derived from Macro/dump_mvars.sas Usage block.
"""

import io

from sas_utils.framework.dump_mvars import dump_mvars


class TestDumpMvars:
    def test_basic_dump(self):
        result = dump_mvars({"X": 1, "Y": "hello"})
        assert "X" in result
        assert "1" in result
        assert "Y" in result
        assert "hello" in result

    def test_selected_names(self):
        result = dump_mvars({"X": 1, "Y": 2, "Z": 3}, names=["X", "Z"])
        assert "X" in result
        assert "Z" in result
        assert "Y" not in result

    def test_sorted_output(self):
        result = dump_mvars({"C": 3, "A": 1, "B": 2}, sort=True)
        pos_a = result.index("A")
        pos_b = result.index("B")
        pos_c = result.index("C")
        assert pos_a < pos_b < pos_c

    def test_undefined_variable(self):
        result = dump_mvars({"X": 1}, names=["X", "MISSING"])
        assert "UNDEFINED" in result

    def test_file_output(self):
        buf = io.StringIO()
        dump_mvars({"X": 1}, file=buf)
        assert "X" in buf.getvalue()

    def test_separator_lines(self):
        result = dump_mvars({"X": 1})
        assert result.startswith("=" * 80)
        assert result.endswith("=" * 80)
