import pandas as pd
from pathlib import Path

# Mock data loading
data_path = Path("data")
revshare = pd.read_csv("data/RevShareNewLogic.csv")
revshare["RevShareDate"] = pd.to_datetime(revshare["RevShareDate"], errors="coerce")

# Params
start_date = "2025-01-01"
end_date = "2025-12-31"
staff_selected = "JRJ" # Test with JRJ

# Logic from RevShare.py
filtered_rev = (
    revshare[
        (revshare["RevShareDate"] >= pd.to_datetime(start_date)) &
        (revshare["RevShareDate"] <= pd.to_datetime(end_date)) &
        (revshare["Staff"] == staff_selected)
    ]
    .drop(columns=[col for col in revshare.columns if col.startswith("Unnamed")])
    .sort_values("RevShareDate")
)

# Calculate new columns
filtered_rev["Flat Fee Hours"] = filtered_rev["FONEHours"] + filtered_rev["FMONHours"]
filtered_rev["Flat Fee Revenue"] = filtered_rev["FONERevenue"] + filtered_rev["FMONRevenue"]
filtered_rev["Threshold"] = 14000.0
filtered_rev["Eligible for Revenue Share"] = (filtered_rev["TotalRevShareMonth"] - filtered_rev["Threshold"]).clip(lower=0)

# Rename columns
filtered_rev = filtered_rev.rename(columns={
    "RevShareMonth": "Month",
    "RevShareYear": "Year",
    "RevShareDate": "Date",
    "AverageRate": "Average Collection Rate",
    "HourlyHours": "Hourly Hours Collected",
    "HourlyRevenue": "Hourly Revenue",
    "TotalRevShareMonth": "Total Production Revenue",
    "RevTier1": "Tier 1 Share",
    "RevTier2": "Tier 2 Share",
    "RevTier3": "Tier 3 Share",
    "RevTierTotal": "Production Revenue Share",
    "OriginationFees": "Origination Revenue Share",
    "RevShareTotal": "Total Revenue Share"
})

# Step 4: Reorder columns explicitly
desired_order = [
    "Staff",
    "Month", 
    "Flat Fee Hours",
    "Average Collection Rate",
    "Flat Fee Revenue",
    "Hourly Hours Collected",
    "Hourly Revenue",
    "Total Production Revenue",
    "Threshold",
    "Eligible for Revenue Share",
    "Tier 1 Share",
    "Tier 2 Share",
    "Tier 3 Share",
    "Production Revenue Share",
    "Origination Revenue Share",
    "Total Revenue Share"
]

# Use Date for display in Month column
filtered_rev["Month"] = filtered_rev["Date"].dt.strftime("%m/%d/%Y")

# Ensure all desired columns are in filtered_rev
final_cols = [col for col in desired_order if col in filtered_rev.columns]
filtered_rev = filtered_rev[final_cols]

print("FINAL COLUMNS:")
print(filtered_rev.columns.tolist())
print("-" * 20)
print("SAMPLE ROW:")
print(filtered_rev.iloc[0])
