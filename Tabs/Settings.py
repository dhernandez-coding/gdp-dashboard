# Tabs/Settings.py

import streamlit as st
import json
from pathlib import Path
import pandas as pd

SETTINGS_FILE = Path(__file__).parents[1] / "data" / "settings.json"
DATA_PATH = Path(__file__).parents[1] / "data" / "vBillableHoursStaff.csv"

# Build selectable staff list from data
df_time_entries = pd.read_csv(DATA_PATH)
unique_staff_list = sorted(df_time_entries["StaffAbbreviation"].dropna().unique().tolist())

# Default weekly goals (used on first run or when a staff is missing)
DEFAULT_STAFF_WEEKLY_GOALS = {
    "AEZ": 20,
    "BPL": 20,
    "CAJ": 20,
    "JER": 20,
    "JRJ": 20,
    "RAW": 20,
    "TGF": 20,
    "KWD": 20,
    "JMG": 20,
}

def load_threshold_settings():
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {
        "treshold_hours": 910,
        "treshold_revenue": 2_000_000,
        "custom_staff_list": ["AEZ", "BPL", "CAJ", "JER", "JRJ", "RAW", "TGF", "KWD", "JMG"],
        "staff_weekly_goals": DEFAULT_STAFF_WEEKLY_GOALS.copy(),
    }

def save_threshold_settings(thresholds: dict):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(thresholds, f, indent=4)

def _ensure_session_defaults():
    saved = load_threshold_settings()
    if "treshold_hours" not in st.session_state:
        st.session_state["treshold_hours"] = saved.get("treshold_hours", 910)
    if "treshold_revenue" not in st.session_state:
        st.session_state["treshold_revenue"] = saved.get("treshold_revenue", 2_000_000)
    if "custom_staff_list" not in st.session_state:
        st.session_state["custom_staff_list"] = saved.get("custom_staff_list", list(DEFAULT_STAFF_WEEKLY_GOALS.keys()))
    if "staff_weekly_goals" not in st.session_state:
        st.session_state["staff_weekly_goals"] = saved.get("staff_weekly_goals", DEFAULT_STAFF_WEEKLY_GOALS.copy())

def run_settings():
    _ensure_session_defaults()

    st.title("🔧 Dashboard Settings")

    # Current settings from session
    current_hours = st.session_state["treshold_hours"]
    current_revenue = st.session_state["treshold_revenue"]
    current_staff_list = st.session_state["custom_staff_list"]
    current_goals = st.session_state["staff_weekly_goals"]

    # Staff selection
    st.markdown("### Select Staff for the Dashboard")
    updated_staff_list = st.multiselect(
        "Choose the staff to include:",
        options=unique_staff_list,
        default=current_staff_list
    )

    # Team thresholds
    col1, col2 = st.columns(2)
    with col1:
        new_hours = st.number_input(
            "Team Goal: Total Billable Hours (Annual)",
            min_value=0,
            value=int(current_hours),
            step=10
        )
    with col2:
        new_revenue = st.number_input(
            "Team Goal: Total Revenue ($)",
            min_value=0,
            value=int(current_revenue),
            step=10_000
        )

    # Weekly goals per staff
    st.markdown("### Weekly Goals per Staff")
    updated_goals = {}
    if updated_staff_list:
        # Create a compact grid of inputs
        cols = st.columns(3)
        for i, staff in enumerate(updated_staff_list):
            with cols[i % 3]:
                updated_goals[staff] = st.number_input(
                    f"{staff} weekly goal (hours)",
                    min_value=0,
                    max_value=60,
                    value=int(current_goals.get(staff, DEFAULT_STAFF_WEEKLY_GOALS.get(staff, 20))),
                    step=1,
                    key=f"goal_{staff}"
                )
    else:
        st.info("Select at least one staff to edit weekly goals.")

    # Save settings
    if st.button("💾 Save Settings"):
        # Keep goals only for selected staff; drop others to keep it clean
        goals_to_save = updated_goals if updated_staff_list else current_goals

        updated_settings = {
            "treshold_hours": int(new_hours),
            "treshold_revenue": int(new_revenue),
            "custom_staff_list": updated_staff_list if updated_staff_list else current_staff_list,
            "staff_weekly_goals": goals_to_save,
        }

        save_threshold_settings(updated_settings)

        # Update session state
        st.session_state["treshold_hours"] = int(new_hours)
        st.session_state["treshold_revenue"] = int(new_revenue)
        st.session_state["custom_staff_list"] = updated_settings["custom_staff_list"]
        st.session_state["staff_weekly_goals"] = goals_to_save

        st.success("✅ Settings saved successfully!")

    # Live preview
    if updated_staff_list:
        st.markdown("### Calculated Thresholds Per Person")
        st.write(f"**Monthly hours per lawyer**: {new_hours / 12:,.2f} hours")
        st.write(f"**Weekly hours per lawyer**: {new_hours / 52:,.2f} hours")
        per_lawyer_rev = (new_revenue / len(updated_staff_list)) if len(updated_staff_list) else 0
        st.write(f"**Revenue per lawyer**: ${per_lawyer_rev:,.2f}")

        # Show a small table with the goals being used
        preview = pd.DataFrame(
            {"Staff": updated_staff_list,
             "WeeklyGoalHours": [updated_goals.get(s, current_goals.get(s, 20)) for s in updated_staff_list]}
        )
        st.dataframe(preview, use_container_width=True)
    else:
        st.warning("⚠️ No staff members defined.")
