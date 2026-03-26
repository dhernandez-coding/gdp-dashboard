import pandas as pd
from pathlib import Path

def test_data():
    data_path = Path("data")
    billable_hours = pd.read_csv(data_path / "vBillableHoursStaff.csv", encoding="utf-8")
    billable_hours["BillableHoursDate"] = pd.to_datetime(billable_hours["BillableHoursDate"], errors="coerce")
    billable_hours = billable_hours.dropna(subset=["BillableHoursDate"])
    
    # Sort by date
    last_date = billable_hours["BillableHoursDate"].max()
    print(f"Latest date in dataset: {last_date}")
    
    # Check April 2026
    april_2026 = billable_hours[
        (billable_hours["BillableHoursDate"] >= "2026-04-01")
    ]
    print(f"Total rows for April 2026 and beyond: {len(april_2026)}")
    if len(april_2026) > 0:
        print(f"Total hours: {april_2026['BillableHoursAmount'].sum()}")

if __name__ == "__main__":
    test_data()
