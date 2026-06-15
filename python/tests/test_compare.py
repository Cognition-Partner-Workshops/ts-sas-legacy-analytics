"""Tests for sas_transforms.compare — mirrors SAS %compare macro."""

import pandas as pd
import pytest

from sas_transforms.compare import compare, compare_datasets, CompareResult


class TestIdenticalDatasets:
    def test_perfect_match(self, class_df: pd.DataFrame):
        result = compare_datasets(class_df, class_df.copy(), by=["Name"])
        assert result.match is True
        assert len(result.value_diffs) == 0
        assert len(result.base_only_rows) == 0
        assert len(result.comp_only_rows) == 0

    def test_positional_match_no_by(self, class_df: pd.DataFrame):
        result = compare_datasets(class_df, class_df.copy())
        assert result.match is True


class TestValueDifferences:
    def test_single_value_changed(self, class_df: pd.DataFrame):
        """Mirrors SAS example: change John's age to 99."""
        comp = class_df.copy()
        comp.loc[comp["Name"] == "John", "Age"] = 99
        result = compare_datasets(class_df, comp, by=["Name"])
        assert result.match is False
        assert len(result.value_diffs) == 1
        diff = result.value_diffs.iloc[0]
        assert diff["_VAR_"] == "Age"
        assert diff["_BASE_"] == 12
        assert diff["_COMP_"] == 99

    def test_numeric_tolerance_absolute(self, class_df: pd.DataFrame):
        comp = class_df.copy()
        comp.loc[comp["Name"] == "Alfred", "Height"] = 69.0 + 1e-8
        result = compare_datasets(
            class_df, comp, by=["Name"], method="absolute", criterion=1e-6
        )
        assert result.match is True

    def test_numeric_tolerance_exceeded(self, class_df: pd.DataFrame):
        comp = class_df.copy()
        comp.loc[comp["Name"] == "Alfred", "Height"] = 70.0
        result = compare_datasets(
            class_df, comp, by=["Name"], method="absolute", criterion=1e-6
        )
        assert result.match is False


class TestColumnDifferences:
    def test_base_only_column(self, class_df: pd.DataFrame):
        """Mirrors SAS example: comp drops Sex."""
        comp = class_df.drop(columns=["Sex"])
        result = compare_datasets(class_df, comp, by=["Name"])
        assert result.match is False
        assert "Sex" in result.base_only_columns

    def test_comp_only_column(self, class_df: pd.DataFrame):
        comp = class_df.copy()
        comp["Extra"] = 0
        result = compare_datasets(class_df, comp, by=["Name"])
        assert result.match is False
        assert "Extra" in result.comp_only_columns


class TestRowDifferences:
    def test_base_has_extra_row(self, class_df: pd.DataFrame):
        comp = class_df.iloc[:-1].copy()
        result = compare_datasets(class_df, comp, by=["Name"])
        assert result.match is False
        assert len(result.base_only_rows) == 1

    def test_comp_has_extra_row(self, class_df: pd.DataFrame):
        comp = class_df.copy()
        new_row = pd.DataFrame(
            [{"Name": "Zara", "Sex": "F", "Age": 13, "Height": 60.0, "Weight": 90.0}]
        )
        comp = pd.concat([comp, new_row], ignore_index=True)
        result = compare_datasets(class_df, comp, by=["Name"])
        assert result.match is False
        assert len(result.comp_only_rows) == 1


class TestLibraryComparison:
    def test_dict_comparison(self, class_df: pd.DataFrame):
        base_lib = {"class": class_df, "extra": class_df.copy()}
        comp_lib = {"class": class_df.copy()}
        results = compare(base_lib, comp_lib)
        assert isinstance(results, dict)
        assert "class" in results
        assert results["class"].match is True

    def test_filter_pattern(self, class_df: pd.DataFrame):
        base_lib = {"class": class_df, "shoes": class_df.copy()}
        comp_lib = {"class": class_df.copy(), "shoes": class_df.copy()}
        results = compare(base_lib, comp_lib, filter_pattern="class")
        assert "class" in results
        assert "shoes" not in results


class TestSummaryOutput:
    def test_summary_string(self, class_df: pd.DataFrame):
        result = compare_datasets(class_df, class_df.copy(), by=["Name"])
        text = result.summary()
        assert "Datasets match" in text
        assert "True" in text
