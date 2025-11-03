import streamlit as st
from pathlib import Path
# ----------------------------------------------------------------------------
# ✅ Page Configuration
logo_path = Path(__file__).parent / "data" / "resolution.png"

st.set_page_config(
    page_title="RLG App",
    page_icon=str(logo_path) if logo_path.exists() else "📊",
    layout="wide",
)

# ----------------------------------------------------------------------------

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from Tabs import Settings, RLGDashboard, RevShare
from auth import login, logout
import datetime
import numpy as np
import json
import pytz
from data_loader import load_data

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


# ✅ Authentication Logic
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    login()
    st.stop()  # Prevent loading dashboard code before login
else:
    logout()  # Sidebar logout button

# ----------------------------------------------------------------------------

# ✅ Load Data
revenue, billable_hours, matters, mtime_key = load_data()

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
# st.sidebar.header("Filter Data by Date")

username = st.session_state.get("username", "User")
allowed_tabs = st.session_state.get("allowed_tabs", [])

# --- Show last data update timestamp ---
try:
    last_update = None
    if "mtime_key" in locals() and mtime_key:
        # If mtime_key is a tuple (multiple file modification times)
        if isinstance(mtime_key, (tuple, list)):
            mtime_key = max(mtime_key)  # use the most recent one

        # Convert UNIX timestamp or datetime
        if isinstance(mtime_key, (int, float)):
            last_update = datetime.datetime.fromtimestamp(mtime_key, tz=local_tz)
        else:
            last_update = pd.to_datetime(mtime_key, errors="coerce")

    if last_update is not None and pd.notna(last_update):
        formatted_time = last_update.strftime("%b %d, %Y %I:%M %p")
        st.sidebar.markdown(
            f"<p style='font-size:11px; color:gray; margin-top:-8px;'>Last data update: {formatted_time}</p>",
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            "<p style='font-size:11px; color:gray; margin-top:-8px;'>Last data update: Unknown</p>",
            unsafe_allow_html=True,
        )

except Exception as e:
    st.sidebar.markdown(
        f"<p style='font-size:11px; color:gray;'>Last data update: Error</p>",
        unsafe_allow_html=True,
    )

st.sidebar.markdown(f"**Logged in as:** {username}")

# --- Button ---
if st.sidebar.button("🔄 Reload data"):
    st.session_state["reload_triggered"] = True
    st.session_state["reload_time"] = time.time()
    st.cache_data.clear()
    st.rerun()

# --- During reload ---
if st.session_state.get("reload_triggered"):
    elapsed = time.time() - st.session_state.get("reload_time", 0)
    if elapsed < 2:  # show spinner for ~2s
        with st.sidebar:
            st.info("♻️ Reloading data... please wait.")
            st.progress(min(int(elapsed * 50), 100))  # simple animation
        time.sleep(0.5)
        st.rerun()
    else:
        st.session_state["reload_triggered"] = False

# Define all available tabs with their display names
tab_options = {
    "RLGDashboard": ("RLG Dashboard", lambda: RLGDashboard.run_rlg_dashboard(start_date, end_date, show_goals)),
    "RevShare": ("Revenue Share", lambda: RevShare.run_revshare(start_date, end_date)),
    "Settings": ("Settings", lambda: Settings.run_settings()),
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
ensure_tz(revenue, "RevShareDate")
ensure_tz(billable_hours, "BillableHoursDate")
ensure_tz(matters, "MatterCreationDate")

# ✅ Compute min/max
min_date = min(
    revenue["RevShareDate"].min(),
    billable_hours["BillableHoursDate"].min(),
    matters["MatterCreationDate"].min(),
)
max_date = max(
    revenue["RevShareDate"].max(),
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
