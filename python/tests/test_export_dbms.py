"""Tests for sas_transforms.export_dbms — mirrors SAS %export_dbms macro."""

import pandas as pd
import pytest

from sas_transforms.export_dbms import export_dbms


class TestExportDbmsXlsx:
    def test_basic_xlsx(self, class_df: pd.DataFrame, tmp_path) -> None:
        out = export_dbms(class_df, str(tmp_path / "class.xlsx"))
        result = pd.read_excel(out, engine="openpyxl")
        assert len(result) == len(class_df)

    def test_label_renames_columns(self, class_df: pd.DataFrame, tmp_path) -> None:
        labels = {"Name": "Student Name", "Age": "Age In Years"}
        out = export_dbms(
            class_df,
            str(tmp_path / "class.xlsx"),
            label=True,
            labels=labels,
        )
        result = pd.read_excel(out, engine="openpyxl")
        assert "Student Name" in result.columns

    def test_directory_path_auto_names(self, class_df: pd.DataFrame, tmp_path) -> None:
        class_df.name = "mydata"
        out = export_dbms(class_df, str(tmp_path), dbms="XLSX")
        assert out.endswith("mydata.xlsx")


class TestExportDbmsStata:
    def test_basic_stata(self, class_df: pd.DataFrame, tmp_path) -> None:
        out = export_dbms(class_df, str(tmp_path / "class.dta"), dbms="STATA")
        result = pd.read_stata(out)
        assert len(result) == len(class_df)


class TestExportDbmsXls:
    def test_xls_emits_warning(self, class_df: pd.DataFrame, tmp_path) -> None:
        """XLS format should warn about XLSX content in .xls extension."""
        with pytest.warns(UserWarning, match="Legacy XLS format"):
            out = export_dbms(class_df, str(tmp_path / "class.xls"), dbms="XLS", replace=True)
        assert out.endswith(".xls")


class TestExportDbmsErrorHandling:
    def test_invalid_dbms(self, class_df: pd.DataFrame, tmp_path) -> None:
        with pytest.raises(ValueError, match="Unsupported DBMS"):
            export_dbms(class_df, str(tmp_path / "x.foo"), dbms="PARQUET")

    def test_replace_false(self, class_df: pd.DataFrame, tmp_path) -> None:
        path = str(tmp_path / "class.xlsx")
        export_dbms(class_df, path, replace=True)
        with pytest.raises(FileExistsError):
            export_dbms(class_df, path, replace=False)

    def test_nonexistent_directory(self, class_df: pd.DataFrame, tmp_path) -> None:
        with pytest.raises(FileNotFoundError):
            export_dbms(class_df, str(tmp_path / "nodir" / "class.xlsx"))
