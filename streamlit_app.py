import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from Tabs import Settings, RLGDashboard, RevShare

import datetime
import numpy as np
import json


# ✅ Define logo path
logo_path = Path(__file__).parent / "data" / "resolution.png"

# ✅ Set Streamlit Page Config (Favicon only works with a string path)
st.set_page_config(
    page_title="RLG App",
    page_icon=str(logo_path) if logo_path.exists() else "📊",
    layout="wide"
) 


# ✅ Load Data Function
@st.cache_data(ttl=86400)  # Cache expires after 86400 seconds (24 hours)

def load_data():
    """Load datasets from the /data folder and preprocess dates."""
    data_path = Path(__file__).parent / "data"

    # Load CSVs
    revenue = pd.read_csv(data_path / "vTimeEntries.csv", parse_dates=["TimeEntryDate"])
    billable_hours = pd.read_csv(data_path / "vBillableHoursStaff.csv", parse_dates=["BillableHoursDate"])
    matters = pd.read_csv(data_path / "vMatters.csv", parse_dates=["MatterCreationDate"])

    # ✅ Apply Date Transformations Once (for efficiency)
    billable_hours["Month"] = billable_hours["BillableHoursDate"].dt.to_period("M").astype(str)
    billable_hours["Week"] = billable_hours["BillableHoursDate"] - pd.to_timedelta(billable_hours["BillableHoursDate"].dt.dayofweek, unit="D")

    revenue["Month"] = revenue["TimeEntryDate"].dt.to_period("M").astype(str)
    revenue["Week"] = revenue["TimeEntryDate"] - pd.to_timedelta(revenue["TimeEntryDate"].dt.dayofweek, unit="D")

    matters["Week"] = matters["MatterCreationDate"] - pd.to_timedelta(matters["MatterCreationDate"].dt.dayofweek, unit="D")

    return revenue, billable_hours, matters

# Load data
revenue, billable_hours, matters = load_data()
# ----------------------------------------------------------------------------
# ✅ HEADER WITH COMPANY LOGO
header_bg_color = "#052b48"  # Dark blue background for header
st.markdown(
    f"""
    <div style="background-color:{header_bg_color}; padding:20px; text-align:center; border-radius:5px;">
        <h1 style="color:white; margin-bottom:5px;">RLG Dashboard</h1>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# ----------------------------------------------------------------------------
# ✅ DATE FILTER
today = pd.Timestamp.today()
st.sidebar.header("Filter Data by Date")
page = st.sidebar.radio("Select Page", ["RLG Dashboard", "Settings", "Revenue Share"])
min_date = min(revenue["TimeEntryDate"].min(), billable_hours["BillableHoursDate"].min(), matters["MatterCreationDate"].min())
start_of_year = pd.Timestamp(today.year, 1, 1)
if min_date < pd.Timestamp("2020-01-01"):
    min_date = pd.Timestamp("2020-01-01")
max_date = max(revenue["TimeEntryDate"].max(), billable_hours["BillableHoursDate"].max(), matters["MatterCreationDate"].max())

# Make sure default_start_date and default_end_date are within bounds
default_start_date = max(start_of_year, min_date)
default_end_date = min(today, max_date)

date_range = st.sidebar.date_input(
    "Select Date Range",
    [default_start_date, default_end_date],
    min_value=min_date,
    max_value=max_date
)
show_goals = st.sidebar.checkbox("Show Goal Lines", value=True)
# Convert to Timestamp for filtering
start_date = pd.Timestamp(date_range[0])
end_date = pd.Timestamp(date_range[1])

st.markdown("---")
# ----------------------------------------------------------------------------
# ✅ DASHBOARD PAGE
if page == "RLG Dashboard":
   RLGDashboard.run_rlg_dashboard(start_date,end_date,show_goals)
   
# ----------------------------------------------------------------------------
elif page == "Settings":
  Settings.run_settings()  

# ----------------------------------------------------------------------------
elif page == "Revenue Share":
   RevShare.run_revshare(start_date, end_date)