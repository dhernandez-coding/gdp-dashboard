import streamlit as st
import json
from pathlib import Path
import pandas as pd
import base64
import requests
from datetime import datetime
import time
# ----------------------And---------------------------------------
# 📁 File paths
# -------------------------------------------------------------
SETTINGS_FILE = Path(__file__).parents[1] / "data" / "settings.json"
DATA_PATH = Path(__file__).parents[1] / "data" / "vBillableHoursStaff.csv"
PREBILLS_FILE = Path(__file__).parents[1] / "data" / "prebills.json"
#Change 
# -------------------------------------------------------------
# 📊 Data preparation
# -------------------------------------------------------------
df_time_entries = pd.read_csv(DATA_PATH)
unique_staff_list = sorted(df_time_entries["StaffAbbreviation"].dropna().unique().tolist())

def load_default_staff_goals():
    """Load staff goals dynamically from settings.json"""
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
        return settings.get("staff_weekly_goals", {})
    else:
        st.warning("⚠️ settings.json not found. Using fallback defaults.")
        return {
            "AEZ": 20, "BPL": 20, "CAJ": 20, "JER": 20,
            "JRJ": 20, "RAW": 20, "TGF": 20, "KWD": 20, "JMG": 20,
        }

def push_to_github_serialized(push_func, *args, **kwargs):
    if st.session_state.get("is_committing", False):
        st.warning("⏳ Another GitHub commit is in progress, please wait...")
        return

    st.session_state["is_committing"] = True
    try:
        push_func(*args, **kwargs)
    finally:
        # small buffer to ensure GitHub commit finishes indexing
        time.sleep(2)
        st.session_state["is_committing"] = False

DEFAULT_STAFF_WEEKLY_GOALS = load_default_staff_goals()
# -------------------------------------------------------------
# ⚙️ Load / Save logic
# -------------------------------------------------------------

def save_prebills_to_github(prebills_data: dict):
    """Push prebills.json to GitHub when updated."""
    import base64, requests, json
    from datetime import datetime

    # --- Save locally first
    PREBILLS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PREBILLS_FILE, "w") as f:
        json.dump(prebills_data, f, indent=4)

    # --- GitHub settings from secrets ---
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]
    branch = st.secrets.get("GITHUB_BRANCH", "main")
    path = "data/prebills.json"

    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}

    # --- Get current file SHA ---
    response = requests.get(url, headers=headers, params={"ref": branch})
    sha = response.json().get("sha") if response.status_code == 200 else None

    # --- Prepare content ---
    encoded_content = base64.b64encode(json.dumps(prebills_data, indent=4).encode()).decode()
    data = {
        "message": f"Auto-update prebills.json from Streamlit ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
        "content": encoded_content,
        "branch": branch,
    }
    if sha:
        data["sha"] = sha

    # --- Commit to GitHub ---
    put_response = requests.put(url, headers=headers, data=json.dumps(data))
    if put_response.status_code in (200, 201):
        st.toast("Prebills updated in GitHub", icon="💾")
    else:
        st.error(f"Failed to update prebills.json: {put_response.status_code}")
        st.write(put_response.text)

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

    push_to_github_serialized(save_threshold_settings, updated_settings)
    st.session_state.update(updated_settings)
    st.toast("Auto-saved settings", icon="💾")


def load_threshold_settings():
    """
    Safely load settings.json — never overwrite user data unless truly missing or empty.
    Keeps last valid settings in memory to prevent data loss during reruns.
    """
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    raise ValueError("Empty settings file")
                settings = json.loads(content)

            # ✅ Cache a copy to prevent loss after reloads
            st.session_state["last_valid_settings"] = settings
            return settings

        except Exception as e:
            st.warning(f"Settings file invalid ({e}). Using last known good settings if available.")
            if "last_valid_settings" in st.session_state:
                return st.session_state["last_valid_settings"]
            else:
                # return full valid structure, not just staff goals
                defaults = {
                    "treshold_hours": sum(DEFAULT_STAFF_WEEKLY_GOALS.values()),
                    "treshold_revenue": 2_000_000,
                    "custom_staff_list": list(DEFAULT_STAFF_WEEKLY_GOALS.keys()),
                    "staff_weekly_goals": DEFAULT_STAFF_WEEKLY_GOALS.copy(),
                }
                st.session_state["last_valid_settings"] = defaults
                return defaults

    # 🧱 If no file exists (first run)
    defaults = {
        "treshold_hours": sum(DEFAULT_STAFF_WEEKLY_GOALS.values()),
        "treshold_revenue": 2_000_000,
        "custom_staff_list": list(DEFAULT_STAFF_WEEKLY_GOALS.keys()),
        "staff_weekly_goals": DEFAULT_STAFF_WEEKLY_GOALS.copy(),
    }

    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(defaults, f, indent=4)

    st.session_state["last_valid_settings"] = defaults
    return defaults

def save_threshold_settings(thresholds: dict):
    """
    Save settings.json locally and push to GitHub only if there are real changes.
    """

    # --- Recalculate and enrich metadata ---
    staff_goals = thresholds.get("staff_weekly_goals", {})
    thresholds["treshold_hours"] = sum(staff_goals.values()) if staff_goals else thresholds.get("treshold_hours", 910)
    thresholds["last_updated_at"] = datetime.now().isoformat()

    # --- Always save locally for immediate use ---
    SETTINGS_FILE = Path(__file__).parents[1] / "data" / "settings.json"
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(thresholds, f, indent=4)

    # --- GitHub API setup ---
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]
    path = st.secrets["GITHUB_FILE_PATH"]
    branch = st.secrets.get("GITHUB_BRANCH", "main")

    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}"}

    # --- Fetch current file from GitHub ---
    response = requests.get(url, headers=headers, params={"ref": branch})
    if response.status_code == 200:
        sha = response.json().get("sha")
        current_content = base64.b64decode(response.json()["content"]).decode()
        try:
            current_json = json.loads(current_content)
        except json.JSONDecodeError:
            current_json = {}
    else:
        sha = None
        current_json = {}

    # --- Compare old vs new content ---
    if current_json == thresholds:
        st.toast("No changes detected — skipping GitHub commit")
        return

    # --- Prepare content for GitHub commit ---
    new_content = json.dumps(thresholds, indent=4)
    encoded_content = base64.b64encode(new_content.encode()).decode()

    data = {
        "message": f"Auto-update settings.json from Streamlit ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
        "content": encoded_content,
        "branch": branch,
        "committer": {"name": "Streamlit Bot", "email": "bot@streamlit.app"},
    }
    if sha:
        data["sha"] = sha

    # --- Push to GitHub (with conflict retry) ---
    res = requests.put(url, headers=headers, data=json.dumps(data))

    if res.status_code == 409:
        st.warning("GitHub conflict detected, retrying with latest SHA...")
        latest = requests.get(url, headers=headers, params={"ref": branch})
        if latest.status_code == 200:
            data["sha"] = latest.json().get("sha")
            res = requests.put(url, headers=headers, data=json.dumps(data))

    # --- Final status ---
    if res.status_code in (200, 201):
        st.toast("settings.json updated on GitHub!")
    else:
        st.error(f"Failed to update GitHub file: {res.status_code}")
        st.code(res.text)

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

        st.success(f"Settings saved! Total weekly threshold: {total_weekly_goal} hours")

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
        st.warning("No staff members defined.")

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
            st.warning("The prebills file is corrupted or empty. Initializing fresh data.")

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
            push_to_github_serialized(save_prebills_to_github, updated_data)
            st.success("Prebills matrix saved and synced to GitHub!")
