"""
SQL Server connectivity utility.

Migrated from: Macro/libname_sqlsvr.sas
Original author: Scott Bass (01APR2016)

Creates a SQLAlchemy engine for connecting to SQL Server databases.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def connect_sqlserver(
    database: str,
    schema: str = "dbo",
    server: str = "localhost",
    port: Optional[int] = None,
    driver: str = "ODBC Driver 17 for SQL Server",
    trusted_connection: bool = True,
    username: Optional[str] = None,
    password: Optional[str] = None,
    **engine_kwargs,
) -> Engine:
    """
    Create a SQLAlchemy engine connected to a SQL Server database.

    Parameters
    ----------
    database : str
        Database name.
    schema : str
        Default schema. Default ``"dbo"``.
    server : str
        Server hostname or IP. Default ``"localhost"``.
    port : int, optional
        Server port. If None, uses default SQL Server port.
    driver : str
        ODBC driver name. Default ``"ODBC Driver 17 for SQL Server"``.
    trusted_connection : bool
        If True, use Windows/Kerberos authentication. Default True.
    username : str, optional
        SQL Server username (when ``trusted_connection=False``).
    password : str, optional
        SQL Server password (when ``trusted_connection=False``).
    **engine_kwargs
        Additional keyword arguments passed to ``create_engine()``.

    Returns
    -------
    sqlalchemy.engine.Engine
        Configured SQLAlchemy engine.
    """
    driver_encoded = driver.replace(" ", "+")

    if port:
        server_part = f"{server},{port}"
    else:
        server_part = server

    if trusted_connection:
        conn_str = (
            f"mssql+pyodbc://{server_part}/{database}"
            f"?driver={driver_encoded}&trusted_connection=yes"
        )
    else:
        if not username or not password:
            raise ValueError(
                "username and password are required when "
                "trusted_connection is False."
            )
        conn_str = (
            f"mssql+pyodbc://{username}:{password}@{server_part}/{database}"
            f"?driver={driver_encoded}"
        )

    engine_kwargs.setdefault("connect_args", {})

    return create_engine(conn_str, **engine_kwargs)


def build_connection_string(
    database: str,
    server: str = "localhost",
    port: Optional[int] = None,
    driver: str = "ODBC Driver 17 for SQL Server",
    trusted_connection: bool = True,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> str:
    """
    Build an ODBC connection string without creating an engine.

    Returns
    -------
    str
        The ODBC-style connection string.
    """
    parts = [f"DRIVER={{{driver}}}"]
    if port:
        parts.append(f"SERVER={server},{port}")
    else:
        parts.append(f"SERVER={server}")
    parts.append(f"DATABASE={database}")

    if trusted_connection:
        parts.append("Trusted_Connection=yes")
    else:
        parts.append(f"UID={username}")
        parts.append(f"PWD={password}")

    return ";".join(parts)
