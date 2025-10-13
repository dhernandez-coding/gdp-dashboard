# auth.py
import streamlit as st
import json
from pathlib import Path

USERS_FILE = Path(__file__).parent / "data" / "users.json"
LOGO_PATH = Path(__file__).parent / "resolution.png"

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def normalize_email(email: str) -> str:
    return email.strip().lower()

def login():
    users = load_users()

    # Centered layout with native columns (no CSS)
    left, center, right = st.columns([1, 2, 1])
    with center:
        # Logo (optional)
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), use_container_width=False, width=160)
        st.markdown("### RLG Dashboard Login")

        # Group inputs + button in a form (prevents half-rerenders)
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="you@ResolutionLegal.com")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Login")

        if submitted:
            normalized = normalize_email(email)
            normalized_users = {k.lower(): v for k, v in users.items()}

            if normalized in normalized_users:
                user_data = normalized_users[normalized]
                if user_data["password"] == password:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = email
                    st.session_state["allowed_tabs"] = user_data["allowed_tabs"]
                    st.rerun()
                else:
                    st.error("Incorrect password.")
            else:
                st.error("Email not found.")

        st.caption("© 2025 Resolution Legal Group")

def logout():
    st.sidebar.divider()
    if st.sidebar.button("Logout"):
        for key in ["authenticated", "username", "allowed_tabs"]:
            st.session_state.pop(key, None)
        st.rerun()
