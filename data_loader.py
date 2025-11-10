# data_loader.py
import pandas as pd
from pathlib import Path
import streamlit as st

@st.cache_data(ttl=0)
def load_data():
    data_path = Path(__file__).parent / "data"

    csv_files = [
        data_path / "RevShareNewLogic.csv",
        data_path / "vBillableHoursStaff.csv",
        data_path / "vMatters.csv",
    ]
    mtime_key = tuple(f.stat().st_mtime for f in csv_files)

    # ------ CSV Files ------
    revenue = pd.read_csv(data_path / "RevShareNewLogic.csv", parse_dates=["RevShareDate"])
    billable_hours = pd.read_csv(data_path / "vBillableHoursStaff.csv", parse_dates=["BillableHoursDate"])
    matters = pd.read_csv(data_path / "vMatters.csv", parse_dates=["MatterCreationDate"])

    # ✅ Ensure MatterCreationDate is really datetime (handles blank or bad rows)
    matters["MatterCreationDate"] = pd.to_datetime(matters["MatterCreationDate"], errors="coerce")

    # ------ Date Features ------
    billable_hours["Month"] = billable_hours["BillableHoursDate"].dt.to_period("M").astype(str)
    billable_hours["Week"] = billable_hours["BillableHoursDate"] - pd.to_timedelta(
        billable_hours["BillableHoursDate"].dt.dayofweek, unit="D"
    )

    revenue["MonthDate"] = revenue["RevShareDate"].dt.to_period("M").dt.to_timestamp()
    revenue["WeekDate"] = revenue["RevShareDate"] - pd.to_timedelta(revenue["RevShareDate"].dt.dayofweek, unit="D")
    revenue["Month"] = revenue["RevShareDate"].dt.to_period("M").astype(str)
    revenue["Week"] = revenue["RevShareDate"] - pd.to_timedelta(
        revenue["RevShareDate"].dt.dayofweek, unit="D"
    )

    # ✅ This line will now work safely
    matters["Week"] = matters["MatterCreationDate"] - pd.to_timedelta(
        matters["MatterCreationDate"].dt.dayofweek, unit="D"
    )

    return revenue, billable_hours, matters, mtime_key
