"""
Tests for sas_utils.data_manipulation.hash_lookup

Derived from Macro/hash_define.sas Usage block (lines 56-199).
"""

import pandas as pd
import pytest

from sas_utils.data_manipulation.hash_lookup import hash_define, hash_lookup


# ====================================================================
# Test: simple key lookup
# From: hash_define.sas test data (key1 key2 -> svar1 svar2)
# ====================================================================
class TestHashLookup:
    @pytest.fixture
    def source_df(self):
        return pd.DataFrame({
            "key1": ["E", "A", "C"],
            "key2": ["F", "B", "D"],
            "svar1": ["1", "3", "5"],
            "svar2": ["2", "4", "6"],
        })

    @pytest.fixture
    def target_df(self):
        return pd.DataFrame({
            "key1": ["A", "C", "E", "X"],
            "key2": ["B", "D", "F", "Y"],
            "tvar1": ["a", "b", "c", "d"],
        })

    def test_simple_lookup(self, source_df, target_df):
        hdef = hash_define(source_df, keys=["key1", "key2"])
        result = hash_lookup(target_df, hdef)
        assert "svar1" in result.columns
        assert "svar2" in result.columns
        assert len(result) == 4  # left join keeps all target rows

    def test_lookup_values_match(self, source_df, target_df):
        hdef = hash_define(source_df, keys=["key1", "key2"])
        result = hash_lookup(target_df, hdef)
        row_a = result[result["key1"] == "A"].iloc[0]
        assert row_a["svar1"] == "3"
        assert row_a["svar2"] == "4"

    def test_unmatched_returns_nan(self, source_df, target_df):
        hdef = hash_define(source_df, keys=["key1", "key2"])
        result = hash_lookup(target_df, hdef)
        row_x = result[result["key1"] == "X"].iloc[0]
        assert pd.isna(row_x["svar1"])


# ====================================================================
# Test: lookup with renames
# ====================================================================
class TestHashLookupRename:
    def test_rename(self):
        source = pd.DataFrame({
            "id": [1, 2, 3],
            "value": ["a", "b", "c"],
        })
        target = pd.DataFrame({
            "id": [1, 2, 4],
            "other": ["x", "y", "z"],
        })
        hdef = hash_define(source, keys="id", rename={"value": "renamed_val"})
        result = hash_lookup(target, hdef)
        assert "renamed_val" in result.columns
        assert result[result["id"] == 1]["renamed_val"].iloc[0] == "a"


# ====================================================================
# Test: single key (string input)
# ====================================================================
class TestHashDefineSingleKey:
    def test_string_key_input(self):
        source = pd.DataFrame({
            "id": [1, 2],
            "name": ["Alice", "Bob"],
        })
        hdef = hash_define(source, keys="id")
        assert hdef["keys"] == ["id"]
        assert hdef["data_vars"] == ["name"]

    def test_specific_data_vars(self):
        source = pd.DataFrame({
            "id": [1, 2],
            "name": ["Alice", "Bob"],
            "age": [30, 25],
        })
        hdef = hash_define(source, keys="id", data_vars="name")
        assert hdef["data_vars"] == ["name"]
        assert "age" not in hdef["source"].columns
