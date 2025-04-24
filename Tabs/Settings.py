import streamlit as st
import json
from pathlib import Path
import pandas as pd
SETTINGS_FILE = Path(__file__).parents[1] / "data" / "settings.json"
DATA_PATH = Path(__file__).parents[1] / "data" / "vTimeEntries.csv"
df_time_entries = pd.read_csv(DATA_PATH)
unique_staff_list = sorted(df_time_entries["Staff"].dropna().unique().tolist())

def load_threshold_settings():
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {
        "treshold_hours": 910,
        "treshold_revenue": 2000000,
        "custom_staff_list": ["AEZ", "BPL", "CAJ", "JER", "JRJ", "RAW", "TGF", "KWD"]
    }

def save_threshold_settings(thresholds: dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(thresholds, f, indent=4)


def run_settings():
    st.title("🔧 Dashboard Settings")

    # Current settings
    current_hours = st.session_state["treshold_hours"]
    current_revenue = st.session_state["treshold_revenue"]
    current_staff_list = st.session_state["custom_staff_list"]

    # Editable staff list
    st.markdown("### Select Staff for the Dashboard")
    updated_staff_list = st.multiselect("Choose the staff to include:",options=unique_staff_list, default=current_staff_list)

    # Thresholds
    new_hours = st.number_input(
        "Team Goal: Total Billable Hours (Annual)",
        min_value=0,
        value=current_hours,
        step=10
    )

    new_revenue = st.number_input(
        "Team Goal: Total Revenue ($)",
        min_value=0,
        value=current_revenue,
        step=10000
    )

    # Save logic
    if st.button("💾 Save Settings"):
        updated_settings = {
            "treshold_hours": new_hours,
            "treshold_revenue": new_revenue,
            "custom_staff_list": updated_staff_list
        }

        # Save to settings.json
        save_threshold_settings(updated_settings)

        # 🧠 Optional: directly update session_state (no need to reload from file)
        st.session_state["treshold_hours"] = new_hours
        st.session_state["treshold_revenue"] = new_revenue
        st.session_state["custom_staff_list"] = updated_staff_list

        # Show success and rerun
        st.success("✅ Settings saved successfully!")



    # Live preview
    if updated_staff_list:
        st.markdown("### Calculated Thresholds Per Person")
        st.write(f"**Monthly hours per lawyer**: {new_hours / 12:,.2f} hours")
        st.write(f"**Weekly hours per lawyer**: {new_hours / 12 / 4:,.2f} hours")
        st.write(f"**Revenue per lawyer**: ${new_revenue / len(updated_staff_list):,.2f}")

        
    else:
        st.warning("⚠️ No staff members defined.")
