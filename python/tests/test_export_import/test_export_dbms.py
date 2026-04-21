"""
Tests for sas_utils.export_import.export_dbms

Derived from Macro/export_dbms.sas Usage block (lines 39-260).
"""

import pandas as pd
import pytest

from sas_utils.export_import.export_dbms import export_dbms


# ====================================================================
# Test: export to XLSX (default)
# From: %export_dbms(data=sashelp.class, path="&path")
# ====================================================================
class TestExportXlsx:
    def test_export_xlsx_default(self, sashelp_class, tmp_path):
        df = sashelp_class.copy()
        df.attrs["name"] = "class"
        result = export_dbms(df, path=tmp_path, replace=True)
        assert result.exists()
        assert result.suffix == ".xlsx"
        assert result.name == "class.xlsx"

    def test_export_xlsx_explicit_filename(self, sashelp_class, tmp_path):
        result = export_dbms(
            sashelp_class, path=tmp_path / "myfile.xlsx", replace=True,
        )
        assert result.name == "myfile.xlsx"
        assert result.exists()

    def test_export_xlsx_replace(self, sashelp_class, tmp_path):
        path = tmp_path / "test.xlsx"
        export_dbms(sashelp_class, path=path, replace=True)
        export_dbms(sashelp_class, path=path, replace=True)
        assert path.exists()

    def test_export_xlsx_no_replace_raises(self, sashelp_class, tmp_path):
        path = tmp_path / "test.xlsx"
        export_dbms(sashelp_class, path=path, replace=True)
        with pytest.raises(FileExistsError, match="already exists"):
            export_dbms(sashelp_class, path=path, replace=False)


# ====================================================================
# Test: export with label=True
# From: %export_dbms(data=sashelp.shoes, path=..., label=Y)
# ====================================================================
class TestExportWithLabels:
    def test_export_with_labels(self, sashelp_shoes, tmp_path):
        df = sashelp_shoes.copy()
        df.attrs["labels"] = {"Sales": "Total Sales", "Returns": "Total Returns"}
        path = tmp_path / "labeled.xlsx"
        export_dbms(df, path=path, replace=True, label=True)
        assert path.exists()
        # Verify that labels were applied by reading back
        read_back = pd.read_excel(path)
        assert "Total Sales" in read_back.columns


# ====================================================================
# Test: error cases
# From: export_dbms.sas error checking section
# ====================================================================
class TestExportErrors:
    def test_directory_not_exists(self, sashelp_class):
        with pytest.raises(FileNotFoundError, match="does not exist"):
            export_dbms(
                sashelp_class,
                path="/nonexistent/path/file.xlsx",
                replace=True,
            )

    def test_invalid_dbms(self, sashelp_class, tmp_path):
        with pytest.raises(ValueError, match="not a valid DBMS"):
            export_dbms(sashelp_class, path=tmp_path / "test.csv", dbms="csv")

    def test_non_dataframe(self, tmp_path):
        with pytest.raises(ValueError, match="must be a pandas DataFrame"):
            export_dbms("not a df", path=tmp_path)


# ====================================================================
# Test: export to STATA
# From: %export_dbms(data=sashelp.class, path=..., dbms=stata)
# ====================================================================
class TestExportStata:
    def test_export_stata(self, sashelp_class, tmp_path):
        path = tmp_path / "test.dta"
        result = export_dbms(sashelp_class, path=path, dbms="stata", replace=True)
        assert result.exists()
        assert result.suffix == ".dta"
