import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine(
    "mssql+pyodbc://localhost/Customers1000db"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)

CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "raw"

def load_csv(path, table_name):
    df = pd.read_csv(path)
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    df.to_sql(table_name, engine, if_exists="replace", index=False)
    print(f"Loaded '{table_name}' — {len(df)} rows, {len(df.columns)} columns")

if __name__ == "__main__":
    if os.path.isfile(CSV_PATH) and CSV_PATH.endswith(".csv"):
        table_name = os.path.basename(CSV_PATH).replace(".csv", "").strip().replace(" ", "_").replace("-", "_").lower()
        load_csv(CSV_PATH, table_name)
    elif os.path.isdir(CSV_PATH):
        files = [f for f in os.listdir(CSV_PATH) if f.endswith(".csv")]
        if not files:
            print("No CSV files found.")
        else:
            print(f"Found {len(files)} CSV file(s). Loading...\n")
            for file in files:
                table_name = file.replace(".csv", "").strip().replace(" ", "_").replace("-", "_").lower()
                load_csv(os.path.join(CSV_PATH, file), table_name)
    else:
        print(f"Path '{CSV_PATH}' not found.")

    print("\nAll done. Your tables are ready in the database.")
