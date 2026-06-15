"""Tests for sas_transforms.transpose — mirrors SAS %transpose macro."""

import pandas as pd
import pytest

from sas_transforms.transpose import transpose


class TestBasicTranspose:
    """Long-form transpose without ID (default COL1..COLn output)."""

    def test_simple_no_by(self, class_df: pd.DataFrame) -> None:
        """Transpose all numeric columns of sashelp.class without BY."""
        result = transpose(class_df, var=["Age", "Height", "Weight"])
        assert "_NAME_" in result.columns
        assert "COL1" in result.columns
        assert len(result) == 3  # one row per var

    def test_by_single_group(self, vitals_df: pd.DataFrame) -> None:
        """Transpose vitals by studyid + usubjid."""
        result = transpose(
            vitals_df,
            by=["studyid", "usubjid"],
            var=["diabp", "sysbp", "pulse"],
        )
        # 2 subjects x 3 vars = 6 rows
        assert len(result) == 6
        assert "studyid" in result.columns
        assert "usubjid" in result.columns
        assert "COL1" in result.columns  # visit V1
        assert "COL2" in result.columns  # visit V2
        assert "COL3" in result.columns  # visit V3

    def test_drop_name(self, class_df: pd.DataFrame) -> None:
        """Setting name=None drops the _NAME_ column."""
        result = transpose(class_df, var=["Age", "Height"], name=None)
        assert "_NAME_" not in result.columns

    def test_drop_label(self, class_df: pd.DataFrame) -> None:
        """Setting label=None drops the _LABEL_ column."""
        result = transpose(class_df, var=["Age"], label=None)
        assert "_LABEL_" not in result.columns

    def test_rename_name(self, class_df: pd.DataFrame) -> None:
        """Custom name for the _NAME_ column."""
        result = transpose(class_df, var=["Age"], name="MEASURE")
        assert "MEASURE" in result.columns
        assert result["MEASURE"].iloc[0] == "Age"

    def test_col_rename(self, vitals_df: pd.DataFrame) -> None:
        """COL parameter renames COL1..COLn output columns."""
        result = transpose(
            vitals_df,
            by=["studyid", "usubjid"],
            var=["diabp", "sysbp"],
            col=["Visit1", "Visit2", "Visit3"],
        )
        assert "Visit1" in result.columns
        assert "Visit2" in result.columns
        assert "Visit3" in result.columns

    def test_where_filter(self, vitals_df: pd.DataFrame) -> None:
        """WHERE clause filters input before transpose."""
        result = transpose(
            vitals_df,
            by=["studyid", "usubjid"],
            var=["diabp"],
            where="usubjid == 'P001'",
        )
        assert all(result["usubjid"] == "P001")


class TestIdTranspose:
    """Wide-form transpose using ID parameter."""

    def test_id_basic(self) -> None:
        df = pd.DataFrame({
            "region": ["East", "East", "West", "West"],
            "product": ["A", "B", "A", "B"],
            "sales": [100, 200, 150, 250],
        })
        result = transpose(df, by=["region"], var=["sales"], id="product")
        assert "A" in result.columns
        assert "B" in result.columns
        assert len(result) == 2


class TestSorting:
    """SORT and NOTSORTED options."""

    def test_notsorted_preserves_order(self) -> None:
        df = pd.DataFrame({
            "grp": ["B", "A", "B", "A"],
            "val": [1, 2, 3, 4],
        })
        result = transpose(df, by=["grp"], var=["val"], notsorted=True)
        # First group should be B since notsorted preserves input order
        assert result.iloc[0]["grp"] == "B"


class TestValidation:
    def test_col_and_id_exclusive(self, class_df: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="Only one of"):
            transpose(class_df, var=["Age"], id="Name", col=["x"])

    def test_idlabel_requires_id(self, class_df: pd.DataFrame) -> None:
        with pytest.raises(ValueError, match="'id_label' requires 'id'"):
            transpose(class_df, var=["Age"], id_label="foo")
