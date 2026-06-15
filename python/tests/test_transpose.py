"""Tests for sas_transforms.transpose — mirrors SAS %transpose macro."""

import pandas as pd
import pytest

from sas_transforms.transpose import transpose


class TestSimpleTranspose:
    """Basic transpose without BY groups."""

    def test_all_numeric_columns_transposed_by_default(self, class_df: pd.DataFrame):
        """No ``var`` → all numeric columns transposed (SAS default)."""
        result = transpose(class_df)
        assert "_NAME_" in result.columns
        assert set(result["_NAME_"].unique()) == {"Age", "Height", "Weight"}

    def test_var_selects_specific_columns(self, class_df: pd.DataFrame):
        result = transpose(class_df, var=["Height", "Weight"])
        assert set(result["_NAME_"].unique()) == {"Height", "Weight"}

    def test_drop_name_column(self, class_df: pd.DataFrame):
        result = transpose(class_df, var=["Age"], name=None)
        assert "_NAME_" not in result.columns

    def test_drop_label_column(self, class_df: pd.DataFrame):
        result = transpose(class_df, var=["Age"], label=None)
        assert "_LABEL_" not in result.columns

    def test_col_rename(self, class_df: pd.DataFrame):
        result = transpose(class_df, var=["Age"], col=["measures"])
        assert "measures" in result.columns
        assert "COL1" not in result.columns


class TestTransposeWithBy:
    """Transpose with BY grouping variables."""

    def test_by_groups_preserved(self, vitals_df: pd.DataFrame):
        wide = pd.DataFrame({
            "subject": ["S1", "S1", "S2", "S2"],
            "visit": ["V1", "V1", "V1", "V1"],
            "param": ["DIABP", "SYSBP", "DIABP", "SYSBP"],
            "value": [80, 120, 75, 115],
        })
        result = transpose(wide, by=["subject", "visit"], var=["value"])
        assert "subject" in result.columns
        assert "visit" in result.columns
        subjects = result["subject"].unique()
        assert set(subjects) == {"S1", "S2"}

    def test_by_with_where(self, vitals_df: pd.DataFrame):
        result = transpose(
            vitals_df,
            by=["subject"],
            var=["value"],
            where='param == "SYSBP"',
        )
        assert len(result) > 0
        assert "subject" in result.columns


class TestTransposeWithId:
    """Transpose using an ID column (pivot wider)."""

    def test_id_creates_named_columns(self, vitals_df: pd.DataFrame):
        result = transpose(
            vitals_df,
            by=["subject", "visit"],
            var=["value"],
            id_col="param",
        )
        assert "DIABP" in result.columns
        assert "SYSBP" in result.columns
        assert "TEMP" in result.columns
        assert len(result) == 2

    def test_id_values_match_source(self, vitals_df: pd.DataFrame):
        result = transpose(
            vitals_df,
            by=["subject", "visit"],
            var=["value"],
            id_col="param",
        )
        s1 = result.loc[result["subject"] == "S1"].iloc[0]
        assert s1["DIABP"] == 80
        assert s1["SYSBP"] == 120
        assert s1["TEMP"] == pytest.approx(36.6)


class TestTransposeSorting:
    """Sorting behaviour matches SAS SORT/NOTSORTED options."""

    def test_sort_true_reorders_by(self):
        df = pd.DataFrame({
            "grp": ["B", "A", "B", "A"],
            "val": [1, 2, 3, 4],
        })
        result = transpose(df, by=["grp"], var=["val"], sort=True)
        assert result["grp"].iloc[0] == "A"

    def test_sort_false_preserves_order(self):
        df = pd.DataFrame({
            "grp": ["B", "A", "B", "A"],
            "val": [1, 2, 3, 4],
        })
        result = transpose(df, by=["grp"], var=["val"], sort=False)
        assert result["grp"].iloc[0] == "B"
