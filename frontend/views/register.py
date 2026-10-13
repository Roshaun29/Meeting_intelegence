import streamlit as st
import httpx
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BACKEND_URL
from styles.theme import apply_theme, page_header


def show():
    apply_theme()
    page_header("Create your account", "Join the AI Meeting Intelligence platform", "✨")

    with st.form("register_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full name")
        with col2:
            role = st.selectbox("Role", ["employee", "manager", "admin"], index=0)

        email = st.text_input("Email address")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm password", type="password")

        submitted = st.form_submit_button("Create account")

        if submitted:
            if not name.strip() or not email.strip() or not password or not confirm_password:
                st.error("Please complete all fields before creating your account.")
            elif password != confirm_password:
                st.error("Passwords do not match. Please re-enter them.")
            else:
                try:
                    payload = {
                        "name": name.strip(),
                        "email": email.strip(),
                        "password": password,
                        "role": role,
                    }
                    resp = httpx.post(f"{BACKEND_URL}/auth/register", json=payload, timeout=20)
                    if resp.status_code in (200, 201):
                        st.success("Account created successfully. You can now log in.")
                        if st.button("Go to login"):
                            st.session_state["auth_mode"] = "login"
                            st.rerun()
                    else:
                        details = resp.text
                        try:
                            payload_error = resp.json()
                            if isinstance(payload_error, dict):
                                details = payload_error.get("detail") or payload_error.get("message") or details
                        except Exception:
                            pass
                        st.error(f"Unable to create account: {details}")
                except Exception as exc:
                    st.error(f"Registration failed: {exc}")

    st.markdown("<div class='auth-link-row'>", unsafe_allow_html=True)
    st.markdown("<span>Already have an account?</span>", unsafe_allow_html=True)
    if st.button("Back to login"):
        st.session_state["auth_mode"] = "login"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
