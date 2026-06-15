"""Tests for sas_transforms.subset_data — mirrors SAS %subset_data macro."""

import pandas as pd
import pytest

from sas_transforms.subset_data import subset_data


class TestObsFiltering:
    """SAS-style observation range filtering."""

    def test_single_range(self, class_df: pd.DataFrame):
        """``obs='1-5'`` keeps first 5 rows (1-based)."""
        result = subset_data(class_df, obs="1-5")
        assert len(result) == 5
        assert result["Name"].iloc[0] == "Alfred"
        assert result["Name"].iloc[4] == "Henry"

    def test_multiple_ranges_with_or(self, class_df: pd.DataFrame):
        """``obs='1-5 or 11-15'`` mirrors the SAS example."""
        result = subset_data(class_df, obs="1-5 or 11-15")
        assert len(result) == 10

    def test_out_of_bounds_range(self, class_df: pd.DataFrame):
        """Ranges beyond dataset length are silently clipped."""
        result = subset_data(class_df, obs="1-5 or 20-30")
        assert len(result) == 5

    def test_single_observation(self, class_df: pd.DataFrame):
        result = subset_data(class_df, obs="3")
        assert len(result) == 1
        assert result["Name"].iloc[0] == "Barbara"

    def test_obs_after_firstobs_no_index_error(self, class_df: pd.DataFrame):
        """obs indices should apply to the already-sliced frame, not original."""
        result = subset_data(class_df, firstobs=5, obs="1-3")
        assert len(result) == 3


class TestFirstLastObs:
    def test_firstobs(self, class_df: pd.DataFrame):
        result = subset_data(class_df, firstobs=5)
        assert result["Name"].iloc[0] == "Henry"

    def test_lastobs(self, class_df: pd.DataFrame):
        result = subset_data(class_df, lastobs=3)
        assert len(result) == 3

    def test_firstobs_and_lastobs(self, class_df: pd.DataFrame):
        result = subset_data(class_df, firstobs=2, lastobs=4)
        assert len(result) == 3
        assert result["Name"].iloc[0] == "Alice"


class TestColumnSubsetting:
    def test_keep(self, class_df: pd.DataFrame):
        result = subset_data(class_df, keep=["Name", "Age"])
        assert list(result.columns) == ["Name", "Age"]

    def test_drop(self, class_df: pd.DataFrame):
        result = subset_data(class_df, drop=["Height", "Weight"])
        assert "Height" not in result.columns
        assert "Weight" not in result.columns
        assert "Name" in result.columns


class TestRename:
    def test_rename_basic(self, class_df: pd.DataFrame):
        """Mirrors SAS ``rename=Sex=Gender``."""
        result = subset_data(class_df, rename={"Sex": "Gender"})
        assert "Gender" in result.columns
        assert "Sex" not in result.columns

    def test_rename_then_keep(self, class_df: pd.DataFrame):
        """Rename is applied before keep, matching SAS order."""
        result = subset_data(
            class_df, rename={"Sex": "Gender"}, keep=["Name", "Age", "Gender"]
        )
        assert list(result.columns) == ["Name", "Age", "Gender"]


class TestWhereAndIf:
    def test_where_clause(self, class_df: pd.DataFrame):
        result = subset_data(class_df, where='Sex == "F"')
        assert all(result["Sex"] == "F")
        assert len(result) == 9

    def test_if_expr(self, class_df: pd.DataFrame):
        result = subset_data(class_df, if_expr="Age > 14")
        assert all(result["Age"] > 14)

    def test_combined_rename_and_where(self, class_df: pd.DataFrame):
        """SAS: rename Sex=Gender then where Gender='F'."""
        result = subset_data(
            class_df,
            rename={"Sex": "Gender"},
            where='Gender == "F"',
        )
        assert len(result) == 9
        assert "Gender" in result.columns
