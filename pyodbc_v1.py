"""Simple MS SQL Server table lister using pyodbc."""

import os
import pathlib
import sys

try:
    import pyodbc
except ImportError:
    raise ImportError(
        "pyodbc is required to run this script. Install it with: pip install pyodbc"
    )

try:
    import streamlit as st
except ImportError:
    st = None

try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None


def load_streamlit_secrets():
    """Load Streamlit secrets from the current environment or .streamlit/secrets.toml."""
    if st is not None and hasattr(st, "secrets"):
        sql_secrets = st.secrets.get("sqlserver", {}) if st.secrets else {}
        if sql_secrets:
            return sql_secrets

    secret_file = pathlib.Path(".streamlit/secrets.toml")
    if secret_file.exists() and tomllib is not None:
        try:
            parsed = tomllib.loads(secret_file.read_text(encoding="utf-8"))
            return parsed.get("sqlserver", {}) or {}
        except Exception:
            pass

    return {}


def find_fallback_driver(preferred_driver: str) -> str:
    """Resolve a driver name or path for the current system."""
    available = [d.strip() for d in pyodbc.drivers() if d and d.strip()]
    if preferred_driver in available:
        return preferred_driver

    known_drivers = [
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 13 for SQL Server",
        "ODBC Driver 11 for SQL Server",
        "SQL Server",
        "FreeTDS",
    ]
    for driver_name in known_drivers:
        if driver_name in available:
            return driver_name

    fallback_paths = [
        "/usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so",
        "/usr/lib/odbc/libtdsodbc.so",
    ]
    for path in fallback_paths:
        if pathlib.Path(path).exists():
            return path

    if available:
        return available[0]

    return preferred_driver


def get_connection_string():
    """Build a connection string from environment variables or Streamlit secrets."""
    secrets = load_streamlit_secrets()

    server = os.environ.get("MSSQL_SERVER") or secrets.get("server")
    database = os.environ.get("MSSQL_DATABASE") or secrets.get("database")
    username = os.environ.get("MSSQL_USERNAME") or secrets.get("username")
    password = os.environ.get("MSSQL_PASSWORD") or secrets.get("password")
    driver = os.environ.get("MSSQL_DRIVER") or secrets.get("driver") or "ODBC Driver 18 for SQL Server"
    port = os.environ.get("MSSQL_PORT") or secrets.get("port")
    tds_version = os.environ.get("MSSQL_TDS_VERSION") or secrets.get("tds_version")
    trusted_connection = (
        os.environ.get("MSSQL_TRUSTED_CONNECTION") or secrets.get("trusted_connection")
    )
    encrypt = os.environ.get("MSSQL_ENCRYPT") or secrets.get("encrypt")
    trust_server_certificate = (
        os.environ.get("MSSQL_TRUST_SERVER_CERTIFICATE")
        or secrets.get("trust_server_certificate")
    )

    if not server or not database:
        print(
            "Please set MSSQL_SERVER and MSSQL_DATABASE environment variables,"
            " or provide them in .streamlit/secrets.toml under [sqlserver]."
        )
        sys.exit(1)

    if username and password:
        auth = f"UID={username};PWD={password};"
    elif str(trusted_connection).lower() in ("1", "true", "yes", "y"):  # trusted connection flag
        auth = "Trusted_Connection=yes;"
    else:
        print(
            "Please provide MSSQL_USERNAME and MSSQL_PASSWORD, or set"
            " sqlserver.trusted_connection = true in Streamlit secrets."
        )
        sys.exit(1)

    if not driver:
        driver = "ODBC Driver 18 for SQL Server"
    resolved_driver = find_fallback_driver(driver)
    if resolved_driver != driver:
        print(f"Using ODBC driver: {resolved_driver}")

    extras = []
    if port:
        extras.append(f"PORT={port}")
    if resolved_driver.endswith("libtdsodbc.so") or resolved_driver == "FreeTDS":
        extras.append(f"TDS_Version={tds_version or '7.4'}")
    if encrypt is not None:
        encrypt_value = str(encrypt).lower()
        extras.append(f"Encrypt={'yes' if encrypt_value in ('1', 'true', 'yes', 'y') else 'no'}")
    if trust_server_certificate is not None:
        trust_value = str(trust_server_certificate).lower()
        extras.append(
            f"TrustServerCertificate={'yes' if trust_value in ('1', 'true', 'yes', 'y') else 'no'}"
        )

    extra_string = ";".join(extras) + (";" if extras else "")

    return (
        f"DRIVER={{{resolved_driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"{auth}"
        f"{extra_string}"
    )


def list_tables(connection):
    """Query SQL Server for all user tables in the current database."""
    query = (
        "SELECT TABLE_SCHEMA, TABLE_NAME "
        "FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_TYPE = 'BASE TABLE' "
        "ORDER BY TABLE_SCHEMA, TABLE_NAME"
    )
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    if not rows:
        print("No tables found in the target database.")
        return

    print("Tables in the database:")
    for schema, table_name in rows:
        print(f"- {schema}.{table_name}")


def main():
    connection_string = get_connection_string()
    print("Connecting to SQL Server...")

    try:
        with pyodbc.connect(connection_string, timeout=10) as conn:
            list_tables(conn)
    except pyodbc.Error as err:
        print("Failed to connect or query SQL Server:", err)
        sys.exit(1)


if __name__ == "__main__":
    main()
