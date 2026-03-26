import pandas as pd
from pathlib import Path

def test_data():
    data_path = Path("data")
    billable_hours = pd.read_csv(data_path / "vBillableHoursStaff.csv", encoding="utf-8")
    billable_hours["BillableHoursDate"] = pd.to_datetime(billable_hours["BillableHoursDate"], errors="coerce")
    billable_hours = billable_hours.dropna(subset=["BillableHoursDate"])
    
    # Filter for March 2026
    march_2026 = billable_hours[
        (billable_hours["BillableHoursDate"] >= "2026-03-01") & 
        (billable_hours["BillableHoursDate"] <= "2026-03-31")
    ]
    
    print(f"Total rows for March 2026: {len(march_2026)}")
    total_hours = march_2026["BillableHoursAmount"].sum()
    print(f"Total hours for March 2026: {total_hours}")
    
    # Per staff
    staff_hours = march_2026.groupby("StaffAbbreviation")["BillableHoursAmount"].sum()
    print("\nHours per staff:")
    print(staff_hours)

if __name__ == "__main__":
    test_data()
