"""Tests for sas_transforms.subset_data — mirrors SAS %subset_data macro."""

import pandas as pd
import pytest

from sas_transforms.subset_data import subset_data


class TestWhereClause:
    def test_simple_where(self, class_df: pd.DataFrame) -> None:
        result = subset_data(class_df, where='Sex == "F"')
        assert all(result["Sex"] == "F")
        assert len(result) == 9  # 9 females in sashelp.class

    def test_compound_where(self, class_df: pd.DataFrame) -> None:
        result = subset_data(class_df, where='Sex == "M" and Age > 13')
        assert all((result["Sex"] == "M") & (result["Age"] > 13))


class TestSubsettingIf:
    def test_if_after_rename(self, class_df: pd.DataFrame) -> None:
        """IF uses renamed column names (applied after RENAME)."""
        result = subset_data(
            class_df,
            rename={"Sex": "Gender"},
            if_='Gender == "F"',
        )
        assert "Gender" in result.columns
        assert all(result["Gender"] == "F")


class TestObsRanges:
    def test_contiguous_range(self, class_df: pd.DataFrame) -> None:
        result = subset_data(class_df, obs="1-5")
        assert len(result) == 5

    def test_non_contiguous_ranges(self, class_df: pd.DataFrame) -> None:
        """SAS: obs=%str(1-5 or 11-15)."""
        result = subset_data(class_df, obs="1-5 or 11-15")
        assert len(result) == 10

    def test_range_exceeding_nobs(self, class_df: pd.DataFrame) -> None:
        """Ranges beyond dataset length are silently clamped."""
        result = subset_data(class_df, obs="1-5 or 20-30")
        # 5 from first range, 0 from second (class has only 19 rows)
        assert len(result) == 5

    def test_single_obs(self, class_df: pd.DataFrame) -> None:
        result = subset_data(class_df, obs="3")
        assert len(result) == 1


class TestFirstobsLastobs:
    def test_firstobs(self, class_df: pd.DataFrame) -> None:
        result = subset_data(class_df, firstobs=5)
        assert len(result) == 15  # rows 5..19

    def test_lastobs(self, class_df: pd.DataFrame) -> None:
        result = subset_data(class_df, lastobs=5)
        assert len(result) == 5

    def test_firstobs_and_lastobs(self, class_df: pd.DataFrame) -> None:
        result = subset_data(class_df, firstobs=3, lastobs=7)
        assert len(result) == 5  # rows 3..7


class TestKeepDrop:
    def test_keep(self, class_df: pd.DataFrame) -> None:
        result = subset_data(class_df, keep=["Name", "Age"])
        assert list(result.columns) == ["Name", "Age"]

    def test_drop(self, class_df: pd.DataFrame) -> None:
        result = subset_data(class_df, drop=["Height", "Weight"])
        assert "Height" not in result.columns
        assert "Weight" not in result.columns

    def test_keep_with_rename(self, class_df: pd.DataFrame) -> None:
        """KEEP uses the renamed column name."""
        result = subset_data(
            class_df,
            rename={"Sex": "Gender"},
            keep=["Name", "Age", "Gender"],
        )
        assert list(result.columns) == ["Name", "Age", "Gender"]


class TestRename:
    def test_rename_single(self, class_df: pd.DataFrame) -> None:
        result = subset_data(class_df, rename={"Sex": "Gender"})
        assert "Gender" in result.columns
        assert "Sex" not in result.columns

    def test_rename_multiple(self, class_df: pd.DataFrame) -> None:
        result = subset_data(
            class_df,
            rename={"Sex": "Gender", "Age": "AgeInYears"},
        )
        assert "Gender" in result.columns
        assert "AgeInYears" in result.columns


class TestCombined:
    def test_rename_where_keep(self, class_df: pd.DataFrame) -> None:
        """Full pipeline: rename → where → keep."""
        result = subset_data(
            class_df,
            rename={"Sex": "Gender"},
            where='Gender == "F"',
            keep=["Name", "Age", "Gender"],
        )
        assert list(result.columns) == ["Name", "Age", "Gender"]
        assert all(result["Gender"] == "F")
        assert len(result) == 9

    def test_rename_preserved_with_obs(self, class_df: pd.DataFrame) -> None:
        """OBS should operate on already-renamed df, not original data."""
        result = subset_data(class_df, rename={"Sex": "Gender"}, obs="1-3")
        assert "Gender" in result.columns
        assert "Sex" not in result.columns
        assert len(result) == 3

    def test_firstobs_then_obs(self, class_df: pd.DataFrame) -> None:
        """OBS applied after FIRSTOBS — both should take effect."""
        result = subset_data(class_df, firstobs=5, obs="1-3")
        # firstobs=5 keeps rows 5..19 (15 rows), then obs="1-3" keeps first 3
        assert len(result) == 3
