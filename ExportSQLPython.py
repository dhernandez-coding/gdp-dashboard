import pyodbc
import pandas as pd
import os
import json

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
    # ✅ Set Lock Timeout (10 seconds) to prevent hanging
    cursor.execute("SET LOCK_TIMEOUT 10000;") 
    print("Lock Timeout set to 10 seconds.")

except Exception as e:
    print(f"Connection Failed: {e}")
    exit(1)

# ✅ Stored Procedures to Run (update tables before export)
STORED_PROCS = {
    "TimeSolvClients":   "dbo.spLoadGetTimeSolvClients",
    "TimeSolvContacts":  "dbo.spLoadGetTimeSolvContacts",
    "TimeSolvFirmUsers": "dbo.spLoadGetTimeSolvFirmUsers",
    "TimeSolvInvoices":  "dbo.spLoadGetTimeSolvInvoices",
    "TimeSolvMatters":   "dbo.spLoadGetTimeSolvMatters",
    "TimeSolvPayments":  "dbo.spLoadGetTimeSolvPayments",
    "TimeSolvProjects":  "dbo.spLoadGetTimeSolvProjects",
    "TimeSolvTimeCards": "dbo.spLoadGetTimeSolvTimeCards",
}

# ✅ Tables/Views to Export after procs are run
TABLES = {
    "vMatters": "DW.rpt.vMatters",
    "RevShareNewLogic": "DW.dbo.RevShareNewLogic",
    "vBillableHoursStaff": "DW.dbo.vBillableHoursStaff",
    "vTimeEntries": "DW.dbo.vTimeEntries",
    "vwTimeEntriesType1": "DW.dbo.vwTimeEntriesType1",
    "vwTimeEntriesType2": "DW.dbo.vwTimeEntriesType2",
    "vwTimeEntriesType3": "DW.dbo.vwTimeEntriesType3",
    "StaffGoalsSettings": "DW.dim.StaffGoalsSettings"
}

# ✅ Ensure Export Directory Exists
os.makedirs(EXPORT_PATH, exist_ok=True)

# --------------------------------------------------------------------
# STEP 1: Run all stored procedures
# --------------------------------------------------------------------
# NOTE: TimeSolv SPs are now run via SQL Agent Job 'TimeSolv_Data_Load'
# Uncomment below if you need to run them manually from this script
"""
print("Running stored procedures to refresh data...")
for proc_key, proc_name in STORED_PROCS.items():
    try:
        print(f"Executing {proc_name}...")
        cursor.execute(f"EXEC {proc_name}")
        # cursor.commit()  # Not needed with autocommit=True, removing for clarity
        print(f"{proc_name} executed successfully")
    except Exception as e:
        print(f"Failed to execute {proc_name}: {e}")
        # Detect Lock Timeout Error
        if "1222" in str(e): # SQL Error 1222 is Lock Timeout
            print("ALERT: Execution timed out due to a TABLE LOCK. Please check for open sessions blocking this table.")
"""
print("Skipping SP execution - handled by SQL Agent Job 'TimeSolv_Data_Load'")

# --------------------------------------------------------------------
# STEP 2: Export tables/views to CSV
# --------------------------------------------------------------------
print("\nExporting tables/views to CSV...")
for file_name, table_name in TABLES.items():
    print(f"Exporting {table_name}...")

    query = f"SELECT * FROM {table_name}"

    try:
        df = pd.read_sql_query(query, conn)
        file_path = os.path.join(EXPORT_PATH, f"{file_name}.csv")
        df.to_csv(file_path, index=False, encoding="utf-8", quoting=1)  # 1 = quote non-numeric
        print(f" Successfully exported {file_name}.csv")
    except Exception as e:
        print(f"Failed to export {file_name}: {e}")

# ✅ Close Connection
cursor.close()
conn.close()
print("\n All Stored Procedures Executed and Exports Completed!")

