import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from Tabs import Settings, RLGDashboard, RevShare
from auth import login, logout
import datetime
import numpy as np
import json
import pytz

local_tz = pytz.timezone("America/Chicago")


# ----------------------------------------------------------------------------
# ✅ Initialize Session State for Threshold Settings
SETTINGS_FILE = Path(__file__).parent / "data" / "settings.json"

def load_threshold_settings():
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {
        "treshold_hours": 910,
        "treshold_revenue": 2000000,
        "custom_staff_list": ["AEZ", "BPL", "CAJ", "JER", "JRJ", "RAW", "TGF", "KWD", "JMG"],
        "staff_weekly_goals": {
            "AEZ": 20, "BPL": 20, "CAJ": 20,
            "JER": 20, "JRJ": 20, "RAW": 20,
            "TGF": 20, "KWD": 20, "JMG": 20,
        },
    }


if (
    "treshold_hours" not in st.session_state
    or "treshold_revenue" not in st.session_state
    or "custom_staff_list" not in st.session_state
    or "staff_weekly_goals" not in st.session_state
):
    saved_settings = load_threshold_settings()
    st.session_state["treshold_hours"] = saved_settings.get("treshold_hours", 910)
    st.session_state["treshold_revenue"] = saved_settings.get("treshold_revenue", 2000000)
    st.session_state["custom_staff_list"] = saved_settings.get(
        "custom_staff_list", list(Settings.DEFAULT_STAFF_WEEKLY_GOALS.keys())
    )
    st.session_state["staff_weekly_goals"] = saved_settings.get(
        "staff_weekly_goals", Settings.DEFAULT_STAFF_WEEKLY_GOALS.copy()
    )

# ----------------------------------------------------------------------------
# ✅ Page Configuration
logo_path = Path(__file__).parent / "data" / "resolution.png"

st.set_page_config(
    page_title="RLG App",
    page_icon=str(logo_path) if logo_path.exists() else "📊",
    layout="wide",
)

# ----------------------------------------------------------------------------
# ✅ Authentication Logic
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    login()
    st.stop()  # Prevent loading dashboard code before login
else:
    logout()  # Sidebar logout button

# ----------------------------------------------------------------------------
# ✅ Load Data Function
@st.cache_data(ttl=0)  # Cache for 24 hours
def load_data():
    data_path = Path(__file__).parent / "data"
    revenue = pd.read_csv(data_path / "vTimeEntries.csv", parse_dates=["TimeEntryDate"])
    billable_hours = pd.read_csv(data_path / "vBillableHoursStaff.csv", parse_dates=["BillableHoursDate"])
    matters = pd.read_csv(data_path / "vMatters.csv", parse_dates=["MatterCreationDate"])

    billable_hours["Month"] = billable_hours["BillableHoursDate"].dt.to_period("M").astype(str)
    billable_hours["Week"] = billable_hours["BillableHoursDate"] - pd.to_timedelta(
        billable_hours["BillableHoursDate"].dt.dayofweek, unit="D"
    )

    revenue["Month"] = revenue["TimeEntryDate"].dt.to_period("M").astype(str)
    revenue["Week"] = revenue["TimeEntryDate"] - pd.to_timedelta(
        revenue["TimeEntryDate"].dt.dayofweek, unit="D"
    )

    matters["Week"] = matters["MatterCreationDate"] - pd.to_timedelta(
        matters["MatterCreationDate"].dt.dayofweek, unit="D"
    )

    return revenue, billable_hours, matters


# ✅ Load Data
revenue, billable_hours, matters = load_data()

# ----------------------------------------------------------------------------
# ✅ HEADER WITH COMPANY LOGO
header_bg_color = "#052b48"
st.markdown(
    f"""
    <div style="background-color:{header_bg_color}; padding:20px; text-align:center; border-radius:5px;">
        <h1 style="color:white; margin-bottom:5px;">RLG Dashboard</h1>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")

# ----------------------------------------------------------------------------
# ✅ Sidebar Navigation & Filters
today = pd.Timestamp.now(tz=local_tz).normalize()
st.sidebar.header("Filter Data by Date")

username = st.session_state.get("username", "User")
allowed_tabs = st.session_state.get("allowed_tabs", [])

st.sidebar.markdown(f"**Logged in as:** {username}")

# Define all available tabs with their display names
tab_options = {
    "RLGDashboard": ("RLG Dashboard", lambda: RLGDashboard.run_rlg_dashboard(start_date, end_date, show_goals)),
    "Settings": ("Settings", lambda: Settings.run_settings()),
    "RevShare": ("Revenue Share", lambda: RevShare.run_revshare(start_date, end_date)),
}

# Filter visible tabs based on permissions
visible_tabs = [v[0] for k, v in tab_options.items() if k in allowed_tabs]

# Prevent crash if allowed_tabs is empty
if not visible_tabs:
    st.warning("⚠️ You don’t have access to any dashboards.")
    st.stop()

def ensure_tz(df, col):
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

        # ✅ Remove any implicit UTC meaning — treat as local timestamps
        df[col] = df[col].dt.tz_localize(None)

        # ✅ Now tag as America/Chicago (no shifting)
        df[col] = df[col].dt.tz_localize("America/Chicago")

        # ✅ Don't floor here — keep actual times (important!)
        # df[col] = df[col].dt.floor("D")   


# ✅ Localize all relevant columns
ensure_tz(revenue, "TimeEntryDate")
ensure_tz(billable_hours, "BillableHoursDate")
ensure_tz(matters, "MatterCreationDate")

# ✅ Compute min/max
min_date = min(
    revenue["TimeEntryDate"].min(),
    billable_hours["BillableHoursDate"].min(),
    matters["MatterCreationDate"].min(),
)
max_date = max(
    revenue["TimeEntryDate"].max(),
    billable_hours["BillableHoursDate"].max(),
    matters["MatterCreationDate"].max(),
)

# ✅ Adjust for inclusivity and timezone
max_date = max_date.tz_convert(local_tz) + pd.Timedelta(days=1)
min_date = min_date.tz_convert(local_tz)

# ✅ Define bounds
start_of_year = pd.Timestamp(today.year, 1, 1, tz=local_tz)
baseline = pd.Timestamp("2025-01-01", tz=local_tz)

min_date = max(min_date, baseline)
default_start_date = max(start_of_year, min_date)
default_end_date = min(today, max_date)

# ✅ Streamlit date picker (naive dates)
date_range = st.sidebar.date_input(
    "Select Date Range",
    [default_start_date.date(), default_end_date.date()],
    min_value=min_date.date(),
    max_value=max_date.date(),
)


show_goals = st.sidebar.checkbox("Show Goal Lines", value=True)

start_date = pd.Timestamp(date_range[0])
end_date = pd.Timestamp(date_range[1])

# Sidebar tab selector (only visible tabs)
selected_tab_label = st.sidebar.radio("Select Page", visible_tabs)

# Reverse lookup to match tab key from display label
selected_tab_key = next(k for k, v in tab_options.items() if v[0] == selected_tab_label)

# Run selected tab
tab_options[selected_tab_key][1]()
