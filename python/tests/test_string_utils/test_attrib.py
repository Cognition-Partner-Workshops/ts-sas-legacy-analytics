"""
Tests for sas_utils.string_utils.attrib
"""

import pandas as pd

from sas_utils.string_utils.attrib import get_label, set_formats, set_labels


class TestAttrib:
    def test_set_and_get_labels(self):
        df = pd.DataFrame({"x": [1], "y": [2]})
        set_labels(df, {"x": "X Variable", "y": "Y Variable"})
        assert get_label(df, "x") == "X Variable"
        assert get_label(df, "y") == "Y Variable"

    def test_get_label_default(self):
        df = pd.DataFrame({"x": [1]})
        assert get_label(df, "x") == "x"

    def test_set_formats(self):
        df = pd.DataFrame({"x": [1.0]})
        set_formats(df, {"x": "8.2"})
        assert df.attrs["formats"]["x"] == "8.2"

    def test_set_labels_chaining(self):
        df = pd.DataFrame({"x": [1]})
        result = set_labels(df, {"x": "Label"})
        assert result is df
