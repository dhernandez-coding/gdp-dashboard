import streamlit as st
import json
from pathlib import Path
import pandas as pd

# -------------------------------------------------------------
# 📁 File paths
# -------------------------------------------------------------
SETTINGS_FILE = Path(__file__).parents[1] / "data" / "settings.json"
DATA_PATH = Path(__file__).parents[1] / "data" / "vBillableHoursStaff.csv"
PREBILLS_FILE = Path(__file__).parents[1] / "data" / "prebills.json"

# -------------------------------------------------------------
# 📊 Data preparation
# -------------------------------------------------------------
df_time_entries = pd.read_csv(DATA_PATH)
unique_staff_list = sorted(df_time_entries["StaffAbbreviation"].dropna().unique().tolist())

DEFAULT_STAFF_WEEKLY_GOALS = {
    "AEZ": 20, "BPL": 20, "CAJ": 20, "JER": 20,
    "JRJ": 20, "RAW": 20, "TGF": 20, "KWD": 20, "JMG": 20,
}

# -------------------------------------------------------------
# ⚙️ Load / Save logic
# -------------------------------------------------------------

def auto_save_settings(updated_staff_list, updated_goals, new_revenue):
    """Automatically save whenever an input value changes."""
    goals_to_save = {
        s: updated_goals.get(s, DEFAULT_STAFF_WEEKLY_GOALS.get(s, 20))
        for s in updated_staff_list
    } if updated_staff_list else DEFAULT_STAFF_WEEKLY_GOALS

    total_weekly_goal = sum(goals_to_save.values())

    updated_settings = {
        "treshold_hours": total_weekly_goal,
        "treshold_revenue": int(st.session_state.get("new_revenue", new_revenue)),
        "custom_staff_list": updated_staff_list,
        "staff_weekly_goals": goals_to_save,
    }

    save_threshold_settings(updated_settings)
    st.session_state.update(updated_settings)
    st.toast("✅ Auto-saved settings", icon="💾")


def load_threshold_settings():
    # ✅ If a local file exists, always use it — do NOT overwrite
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            st.warning("Settings.json is corrupted. Rebuilding from defaults.")
            settings = {}

        # Recalculate total hours
        staff_weekly_goals = settings.get("staff_weekly_goals", {})
        settings["treshold_hours"] = sum(staff_weekly_goals.values()) if staff_weekly_goals else sum(DEFAULT_STAFF_WEEKLY_GOALS.values())

        # Ensure essential keys
        settings.setdefault("treshold_revenue", 2_000_000)
        settings.setdefault("custom_staff_list", list(staff_weekly_goals.keys()) or list(DEFAULT_STAFF_WEEKLY_GOALS.keys()))
        settings.setdefault("staff_weekly_goals", staff_weekly_goals or DEFAULT_STAFF_WEEKLY_GOALS.copy())

        return settings

    # 🧱 If no file exists (first run), build it from defaults
    defaults = {
        "treshold_hours": sum(DEFAULT_STAFF_WEEKLY_GOALS.values()),
        "treshold_revenue": 2_000_000,
        "custom_staff_list": list(DEFAULT_STAFF_WEEKLY_GOALS.keys()),
        "staff_weekly_goals": DEFAULT_STAFF_WEEKLY_GOALS.copy(),
    }

    # ✅ Create the file once — from defaults only
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(defaults, f, indent=4)


def save_threshold_settings(thresholds: dict):
    """Save settings and automatically recalculate treshold_hours."""
    staff_goals = thresholds.get("staff_weekly_goals", {})
    thresholds["treshold_hours"] = sum(staff_goals.values()) if staff_goals else thresholds.get("treshold_hours", 910)

    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(thresholds, f, indent=4)


def _ensure_session_defaults():
    """Always refresh Streamlit session state with the latest settings."""
    saved = load_threshold_settings()
    st.session_state["treshold_hours"] = saved.get("treshold_hours", 910)
    st.session_state["treshold_revenue"] = saved.get("treshold_revenue", 2_000_000)
    st.session_state["custom_staff_list"] = saved.get("custom_staff_list", list(DEFAULT_STAFF_WEEKLY_GOALS.keys()))
    st.session_state["staff_weekly_goals"] = saved.get("staff_weekly_goals", DEFAULT_STAFF_WEEKLY_GOALS.copy())


# -------------------------------------------------------------
# 🧭 UI logic
# -------------------------------------------------------------
def run_settings():
    _ensure_session_defaults()

    st.title("🔧 Dashboard Settings")

    # Current settings from session
    current_hours = st.session_state["treshold_hours"]
    current_revenue = st.session_state["treshold_revenue"]
    current_staff_list = st.session_state["custom_staff_list"]
    current_goals = st.session_state["staff_weekly_goals"]

    # ---------------------------------------------------------
    # Staff selection
    # ---------------------------------------------------------
    st.markdown("### Select Staff for the Dashboard")
    updated_staff_list = st.multiselect(
        "Choose the staff to include:",
        options=unique_staff_list,
        default=current_staff_list
    )

    # ---------------------------------------------------------
    # Team thresholds display (read-only)
    # ---------------------------------------------------------

    new_revenue = st.number_input(
        "Team Goal: Total Revenue ($)",
        min_value=0,
        value=int(current_revenue),
        step=10_000,
        key="new_revenue",
        on_change=lambda: auto_save_settings(
            st.session_state.get("custom_staff_list", []),
            st.session_state.get("staff_weekly_goals", {}),
            st.session_state["new_revenue"]
        )
    )
    # ---------------------------------------------------------
    # Weekly goals per staff
    # ---------------------------------------------------------
    st.markdown("### Weekly Goals per Staff")
    updated_goals = st.session_state.get("staff_weekly_goals", {}).copy()

    if updated_staff_list:
        cols = st.columns(3)
        for i, staff in enumerate(updated_staff_list):
            current_goal_value = updated_goals.get(
                staff,
                current_goals.get(staff, DEFAULT_STAFF_WEEKLY_GOALS.get(staff, 20))
            )
            with cols[i % 3]:
                new_value = st.number_input(
                    f"{staff} weekly goal (hours)",
                    min_value=0,
                    max_value=60,
                    value=int(current_goal_value),
                    step=1,
                    key=f"goal_{staff}",
                    on_change=lambda s=staff: auto_save_settings(updated_staff_list, updated_goals, new_revenue)
                )
                updated_goals[staff] = new_value
    else:
        st.info("Select at least one staff to edit weekly goals.")

    # ---------------------------------------------------------
    # Save settings
    # ---------------------------------------------------------
    if st.button("💾 Save Settings"):
        goals_to_save = {s: updated_goals.get(s, DEFAULT_STAFF_WEEKLY_GOALS.get(s, 20))
                         for s in updated_staff_list} if updated_staff_list else current_goals

        # ✅ Automatically compute total threshold from staff goals
        total_weekly_goal = sum(goals_to_save.values())

        updated_settings = {
            "treshold_hours": total_weekly_goal,
            "treshold_revenue": int(new_revenue),
            "custom_staff_list": updated_staff_list if updated_staff_list else current_staff_list,
            "staff_weekly_goals": goals_to_save,
        }

        save_threshold_settings(updated_settings)

        # Refresh session state
        st.session_state.update(updated_settings)

        st.success(f"✅ Settings saved! Total weekly threshold: {total_weekly_goal} hours")

    # ---------------------------------------------------------
    # Live preview table
    # ---------------------------------------------------------
    if updated_staff_list:
        st.markdown("### Calculated Thresholds Per Person")

        preview = pd.DataFrame(
            {"Staff": updated_staff_list,
             "WeeklyGoalHours": [updated_goals.get(s, current_goals.get(s, 20)) for s in updated_staff_list]}
        )
        st.dataframe(preview, use_container_width=True)
    else:
        st.warning("⚠️ No staff members defined.")

    # ---------------------------------------------------------
    # ✅ Prebills section (unchanged)
    # ---------------------------------------------------------
    st.markdown("""<style>
        .stSelectbox, .stRadio {padding-top:0.4rem!important;padding-bottom:0.4rem!important;}
        .element-container:has(.stSelectbox), .element-container:has(.stRadio) {display:flex;align-items:center;}
        .row-label {display:flex;align-items:center;height:100%;font-weight:500;padding-left:0.5rem;}
    </style>""", unsafe_allow_html=True)

    months = pd.date_range(
        start=pd.Timestamp.today().replace(month=1, day=1),
        periods=12,
        freq="MS"
    ).strftime("%b").tolist()

    prebills_data = {}
    if PREBILLS_FILE.exists():
        try:
            with open(PREBILLS_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    prebills_data = json.loads(content)
        except json.JSONDecodeError:
            st.warning("⚠️ The prebills file is corrupted or empty. Initializing fresh data.")

    for staff in current_staff_list:
        if staff not in prebills_data:
            prebills_data[staff] = {}
        for month in months:
            if month not in prebills_data[staff]:
                prebills_data[staff][month] = "Yes"

    st.subheader("Prebills Back On Time", divider="gray")
    st.write("Update Yes/No per staff and month:")

    with st.form("prebills_form"):
        updated_data = {}
        cols = st.columns(len(months) + 1)
        cols[0].markdown("**Name**")
        for i, month in enumerate(months):
            cols[i + 1].markdown(f"**{month}**")

        for staff in current_staff_list:
            row = st.columns(len(months) + 1)
            row[0].markdown(f"<div class='row-label'>{staff}</div>", unsafe_allow_html=True)
            updated_data[staff] = {}
            for i, month in enumerate(months):
                key = f"{staff}_{month}"
                default_value = prebills_data[staff].get(month, "Yes")
                updated_data[staff][month] = row[i + 1].radio(
                    "Prebills Response",
                    options=["Yes", "No"],
                    index=["Yes", "No"].index(default_value),
                    key=key,
                    horizontal=True,
                    label_visibility="collapsed"
                )

        if st.form_submit_button("Save"):
            with open(PREBILLS_FILE, "w") as f:
                json.dump(updated_data, f, indent=4)
            st.success("✅ Matrix saved successfully!")
