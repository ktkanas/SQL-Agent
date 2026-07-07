import os

from sqlalchemy import create_engine

DATABASE_URL = os.getenv(
    "SQL_AGENT_DATABASE_URL",
    "mssql+pyodbc://localhost/visaDB_copy"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes",
)

engine = create_engine(DATABASE_URL)
