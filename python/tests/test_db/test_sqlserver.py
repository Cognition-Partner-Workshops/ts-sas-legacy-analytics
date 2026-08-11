"""
Tests for sas_utils.db.sqlserver

Derived from Macro/libname_sqlsvr.sas Usage block (lines 135-202).
Mock-based tests for connection string construction.
"""

import pytest

from sas_utils.db.sqlserver import build_connection_string, connect_sqlserver


# ====================================================================
# Test: connection string construction
# ====================================================================
class TestBuildConnectionString:
    def test_trusted_connection(self):
        cs = build_connection_string(database="mydb", server="myserver")
        assert "DRIVER={ODBC Driver 17 for SQL Server}" in cs
        assert "SERVER=myserver" in cs
        assert "DATABASE=mydb" in cs
        assert "Trusted_Connection=yes" in cs

    def test_sql_auth(self):
        cs = build_connection_string(
            database="mydb",
            server="myserver",
            trusted_connection=False,
            username="user",
            password="pass",
        )
        assert "UID=user" in cs
        assert "PWD=pass" in cs
        assert "Trusted_Connection" not in cs

    def test_with_port(self):
        cs = build_connection_string(
            database="mydb", server="myserver", port=1433,
        )
        assert "SERVER=myserver,1433" in cs

    def test_custom_driver(self):
        cs = build_connection_string(
            database="mydb",
            server="myserver",
            driver="ODBC Driver 18 for SQL Server",
        )
        assert "DRIVER={ODBC Driver 18 for SQL Server}" in cs


# ====================================================================
# Test: connect_sqlserver requires credentials for SQL auth
# ====================================================================
class TestConnectSqlserver:
    def test_sql_auth_missing_credentials(self):
        with pytest.raises(ValueError, match="username and password are required"):
            connect_sqlserver(
                database="mydb",
                trusted_connection=False,
            )
