"""
Tests for sas_utils.string_utils.justify
"""

from sas_utils.string_utils.justify import justify


class TestJustify:
    def test_left_justify(self):
        assert justify("Hi", width=10, align="left") == "Hi        "

    def test_right_justify(self):
        assert justify("Hi", width=10, align="right") == "        Hi"

    def test_center_justify(self):
        result = justify("Hi", width=10, align="center")
        assert len(result) == 10
        assert "Hi" in result

    def test_width_zero(self):
        assert justify("Hello", width=0) == "Hello"

    def test_width_less_than_text(self):
        assert justify("Hello", width=3) == "Hello"
