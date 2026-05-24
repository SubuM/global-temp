"""Simple MS SQL Server table lister using pymssql."""

import os
import pathlib
import sys

try:
    import pymssql
except ImportError:
    raise ImportError(
        "pymssql is required to run this script. Install it with: pip install pymssql"
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


def list_tables(connection):
    """Query SQL Server for all user tables in the current database."""
    query = (
        "SELECT TABLE_SCHEMA, TABLE_NAME "
        "FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_TYPE = 'BASE TABLE' "
        "ORDER BY TABLE_SCHEMA, TABLE_NAME"
    )
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    finally:
        cursor.close()

    if not rows:
        print("No tables found in the target database.")
        if st is not None:
            st.warning("No tables found in the target database.")
        return

    print("Tables in the database:")
    for schema, table_name in rows:
        print(f"- {schema}.{table_name}")
    
    if st is not None:
        st.write("### Tables in the database:")
        for schema, table_name in rows:
            st.write(f"- {schema}.{table_name}")


def main():
    secrets = load_streamlit_secrets()

    server = os.environ.get("MSSQL_SERVER") or secrets.get("server")
    database = os.environ.get("MSSQL_DATABASE") or secrets.get("database")
    username = os.environ.get("MSSQL_USERNAME") or secrets.get("username")
    password = os.environ.get("MSSQL_PASSWORD") or secrets.get("password")
    port = os.environ.get("MSSQL_PORT") or secrets.get("port")

    if not server or not database:
        msg = (
            "Please set MSSQL_SERVER and MSSQL_DATABASE environment variables,"
            " or provide them in .streamlit/secrets.toml under [sqlserver]."
        )
        print(msg)
        if st is not None:
            st.error(msg)
        sys.exit(1)

    print("Connecting to SQL Server...")
    if st is not None:
        st.info("Connecting to SQL Server...")

    try:
        # Convert port to int if it's set
        port_val = int(port) if port else 1433
        
        # Connect using pymssql
        conn = pymssql.connect(
            server=server,
            user=username,
            password=password,
            database=database,
            port=port_val,
            timeout=10
        )
        with conn:
            list_tables(conn)
            
    except pymssql.Error as err:
        print("Failed to connect or query SQL Server:", err)
        if st is not None:
            st.error(f"Failed to connect or query SQL Server: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
