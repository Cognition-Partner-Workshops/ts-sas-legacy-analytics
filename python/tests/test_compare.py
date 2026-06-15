"""Tests for sas_transforms.compare — mirrors SAS %compare macro."""

import pandas as pd
import pytest

from sas_transforms.compare import compare, CompareResult, LibraryCompareResult


class TestDatasetCompareIdentical:
    def test_identical_datasets(self, class_df: pd.DataFrame) -> None:
        result = compare(class_df, class_df.copy(), by=["Name"])
        assert isinstance(result, CompareResult)
        assert result.equal

    def test_identical_no_by(self, class_df: pd.DataFrame) -> None:
        result = compare(class_df, class_df.copy())
        assert result.equal


class TestDatasetCompareDifferences:
    def test_value_difference(self, class_df: pd.DataFrame) -> None:
        """Mimic SAS: if name='John' then age=99."""
        comp = class_df.copy()
        comp.loc[comp["Name"] == "John", "Age"] = 99
        result = compare(class_df, comp, by=["Name"])
        assert not result.equal
        assert len(result.value_diffs) >= 1
        age_diffs = result.value_diffs[result.value_diffs["variable"] == "Age"]
        assert len(age_diffs) == 1
        assert age_diffs.iloc[0]["base_value"] == 12
        assert age_diffs.iloc[0]["comp_value"] == 99

    def test_column_difference(self, class_df: pd.DataFrame) -> None:
        """Comp drops Sex column."""
        comp = class_df.drop(columns=["Sex"])
        result = compare(class_df, comp, by=["Name"])
        assert "Sex" in result.base_only_cols
        assert result.comp_only_cols == []

    def test_row_difference(self, class_df: pd.DataFrame) -> None:
        """Comp has fewer rows."""
        comp = class_df.iloc[:-2].copy()
        result = compare(class_df, comp, by=["Name"])
        assert len(result.base_only_rows) == 2


class TestNumericTolerance:
    def test_exact_finds_tiny_diff(self) -> None:
        base = pd.DataFrame({"key": [1], "val": [1.0]})
        comp = pd.DataFrame({"key": [1], "val": [1.0 + 1e-10]})
        result = compare(base, comp, by=["key"], method="exact")
        assert not result.equal

    def test_absolute_within_tolerance(self) -> None:
        base = pd.DataFrame({"key": [1], "val": [1.0]})
        comp = pd.DataFrame({"key": [1], "val": [1.0 + 1e-10]})
        result = compare(base, comp, by=["key"], method="absolute", criterion=1e-6)
        assert result.equal


class TestLibraryCompare:
    def test_matched_libraries(self, class_df: pd.DataFrame) -> None:
        lib_base = {"class": class_df}
        lib_comp = {"class": class_df.copy()}
        result = compare(lib_base, lib_comp)
        assert isinstance(result, LibraryCompareResult)
        assert result.matched_members == ["class"]
        assert result.member_results["class"].equal

    def test_unmatched_members(self, class_df: pd.DataFrame) -> None:
        lib_base = {"class": class_df, "extra": class_df}
        lib_comp = {"class": class_df.copy()}
        result = compare(lib_base, lib_comp)
        assert "extra" in result.base_only_members

    def test_filter(self, class_df: pd.DataFrame) -> None:
        lib_base = {"class": class_df, "shoes": class_df}
        lib_comp = {"class": class_df, "shoes": class_df}
        result = compare(lib_base, lib_comp, filter="class")
        assert "class" in result.matched_members
        assert "shoes" not in result.matched_members


class TestDuplicateByKeys:
    def test_duplicate_keys_warns(self) -> None:
        """Non-unique BY keys should emit a warning, not explode."""
        base = pd.DataFrame({"key": [1, 1, 2], "val": [10, 20, 30]})
        comp = pd.DataFrame({"key": [1, 1, 2], "val": [10, 20, 30]})
        with pytest.warns(UserWarning, match="do not uniquely identify"):
            result = compare(base, comp, by=["key"])
        assert result.value_diffs.empty

    def test_duplicate_keys_no_row_explosion(self) -> None:
        """Row count should not blow up from many-to-many join."""
        base = pd.DataFrame({"key": [1, 1, 2, 2], "val": [10, 20, 30, 40]})
        comp = pd.DataFrame({"key": [1, 1, 2, 2], "val": [10, 20, 30, 40]})
        with pytest.warns(UserWarning):
            result = compare(base, comp, by=["key"])
        assert result.value_diffs.empty


class TestValidation:
    def test_type_mismatch(self, class_df: pd.DataFrame) -> None:
        with pytest.raises(TypeError):
            compare(class_df, {"a": class_df})
