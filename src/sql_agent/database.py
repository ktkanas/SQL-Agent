from sqlalchemy import create_engine

engine = create_engine(
    "mssql+pyodbc://localhost/visaDB_copy"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)