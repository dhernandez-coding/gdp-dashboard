import pandas as pd
from pathlib import Path

def test_time_entries():
    data_path = Path("data")
    te = pd.read_csv(data_path / "vTimeEntries.csv", encoding="utf-8")
    te["TimeEntryDate"] = pd.to_datetime(te["TimeEntryDate"], errors="coerce")
    te = te.dropna(subset=["TimeEntryDate"])
    
    # Filter for March 2026
    march_2026 = te[
        (te["TimeEntryDate"] >= "2026-03-01") & 
        (te["TimeEntryDate"] <= "2026-03-31")
    ]
    
    print(f"Total rows in vTimeEntries for March 2026: {len(march_2026)}")
    
    # Billable Hours = Payable is True
    # Let's check the column name and values
    print(f"Columns: {te.columns.tolist()}")
    
    # Assuming TimeEntryPayable exists and is boolean or string 'True'/'False'
    if "TimeEntryPayable" in march_2026.columns:
        # Check unique values
        print(f"TimeEntryPayable values: {march_2026['TimeEntryPayable'].unique()}")
        
        billable = march_2026[march_2026["TimeEntryPayable"].astype(str).str.lower() == "true"]
        print(f"Billable hours (Payable=True): {billable['TimeEntryAmount'].sum()}")
        
        # Non-billable
        non_billable = march_2026[march_2026["TimeEntryPayable"].astype(str).str.lower() != "true"]
        print(f"Non-billable hours: {non_billable['TimeEntryAmount'].sum()}")
        
        # Per staff (billable)
        staff_list = ["AEZ", "BPL", "CAJ", "JER", "JRJ", "RAW", "TGF", "KWD", "JMG"]
        billable_staff = billable[billable["Staff"].isin(staff_list)]
        print("\nBillable hours per staff (in settings list):")
        print(billable_staff.groupby("Staff")["TimeEntryAmount"].sum())
    else:
        print("TimeEntryPayable column NOT found")

if __name__ == "__main__":
    test_time_entries()
