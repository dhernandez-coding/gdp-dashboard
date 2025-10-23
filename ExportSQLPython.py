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
except Exception as e:
    print(f"Connection Failed: {e}")
    exit()

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
print("Running stored procedures to refresh data...")
for proc_key, proc_name in STORED_PROCS.items():
    try:
        print(f"Executing {proc_name}...")
        cursor.execute(f"EXEC {proc_name}")
        cursor.commit()  # commit changes in case proc does inserts/updates
        print(f"{proc_name} executed successfully")
    except Exception as e:
        print(f"Failed to execute {proc_name}: {e}")

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

# # -----------------------------------------------------------------------
# # STEP 3: Write setting.json
# # -----------------------------------------------------------------------
# print("\nBuilding settings.json from StaffGoalsSettings...")
# try:
#     # Pull StaffGoalsSettings table from SQL
#     query = "SELECT StaffAbbreviation, WeeklyGoalHours FROM DW.dim.StaffGoalsSettings"
#     df_goals = pd.read_sql_query(query, conn)

#     # Convert staff abbreviations to list
#     custom_staff_list = df_goals["StaffAbbreviation"].tolist()

#     # Convert to dict of { StaffAbbreviation: WeeklyGoalHours }
#     staff_weekly_goals = dict(zip(df_goals["StaffAbbreviation"], df_goals["WeeklyGoalHours"]))

#     # Define static threshold values
#     settings_json = {
#         "treshold_hours": 185,
#         "treshold_revenue": 2200000,
#         "custom_staff_list": custom_staff_list,
#         "staff_weekly_goals": staff_weekly_goals
#     }

#     # Define file path
#     settings_path = os.path.join(EXPORT_PATH, "settings.json")

#     # Write JSON file
#     with open(settings_path, "w", encoding="utf-8") as f:
#         json.dump(settings_json, f, indent=4)

#     print(f"settings.json created successfully at: {settings_path}")

# except Exception as e:
#     print(f"Failed to create settings.json: {e}")