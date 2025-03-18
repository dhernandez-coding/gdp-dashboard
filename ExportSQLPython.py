import pyodbc
import pandas as pd
import os

# ✅ Define Export Path
EXPORT_PATH = r"C:\Users\v_rroberson\Report RLG\gdp-dashboard\data"

# ✅ Database Connection
try:
    conn = pyodbc.connect(
        "DRIVER={SQL Server};"
        "SERVER=RLGOKC-DB01;"
        "DATABASE=DW;"
        "Trusted_Connection=yes;",
        autocommit=True
    )
    cursor = conn.cursor()
    print("Connected to SQL Server")
except Exception as e:
    print(f"Connection Failed: {e}")
    exit()

# ✅ Define Tables to Export
TABLES = {
    "vMatters": "DW.rpt.vMatters",
    "RevShareNewLogic": "DW.dbo.RevShareNewLogic",
    "vBillableHoursStaff": "DW.dbo.vBillableHoursStaff"
}

# ✅ Ensure Export Directory Exists
os.makedirs(EXPORT_PATH, exist_ok=True)

# ✅ Export Each Table to CSV
for file_name, table_name in TABLES.items():
    print(f"Exporting {table_name}...")

    query = f"SELECT * FROM {table_name}"

    try:
        # ✅ Load Data into Pandas DataFrame
        df = pd.read_sql_query(query, conn)

        # ✅ Define CSV File Path
        file_path = os.path.join(EXPORT_PATH, f"{file_name}.csv")

        # ✅ Export to CSV (UTF-8, Handles Quotes & Commas)
        df.to_csv(file_path, index=False, encoding="utf-8", quoting=1)  # 1 = Quote non-numeric fields

        print(f"Successfully exported {file_name}.csv")
    
    except Exception as e:
        print(f"Failed to export {file_name}: {e}")

# ✅ Close Connection
cursor.close()
conn.close()
print("All Exports Completed!")
