import streamlit as st
import httpx
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import BACKEND_URL
from styles.theme import apply_theme, page_header

st.set_page_config(page_title="AI Meeting Intelligence", page_icon="📝", layout="wide")

# Initialize Session State
if "token" not in st.session_state:
    st.session_state["token"] = None
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "role" not in st.session_state:
    st.session_state["role"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "login"
if "auth_notice" not in st.session_state:
    st.session_state["auth_notice"] = None

def set_auth_mode(mode):
    st.session_state["auth_mode"] = mode
    st.rerun()


def login():
    apply_theme()
    with st.container(key="auth-shell"):
        left_col, right_col = st.columns([0.95, 1.05], gap="medium")

        with left_col:
            with st.container(key="auth-brand"):
                st.markdown(
                    """
                    <div class='brand-badge'>AI</div>
                    <h1>MeetingAI</h1>
                    <p>Turn conversations into decisions, actions, and accountability.</p>
                    <ul class='feature-list'>
                        <li>📝 Meeting summaries</li>
                        <li>✅ Action tracking</li>
                        <li>📊 Role-based dashboards</li>
                    </ul>
                    """,
                    unsafe_allow_html=True,
                )

        with right_col:
            with st.container(key="auth-card"):
                if st.session_state.get("auth_notice"):
                    st.success(st.session_state.pop("auth_notice"))
                st.markdown(
                    "<div class='auth-heading'><span>WELCOME BACK</span><h1>Sign in</h1><p>Access your meetings, tasks, and team insights.</p></div>",
                    unsafe_allow_html=True,
                )
                with st.form("login_form"):
                    username = st.text_input("Username or Email", placeholder="you@company.com")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    submit = st.form_submit_button("Sign in", use_container_width=True)

                    if submit:
                        try:
                            if not username.strip() or not password.strip():
                                st.error("Please enter both your username/email and password.")
                            else:
                                payload = {"username": username.strip(), "password": password}
                                res = httpx.post(f"{BACKEND_URL}/auth/login", json=payload, timeout=20)
                                if res.status_code == 200:
                                    data = res.json()
                                    user_data = data.get("user", {})
                                    display_name = user_data.get("name") or user_data.get("email") or username.strip()
                                    st.session_state["token"] = data.get("access_token")
                                    st.session_state["user_id"] = user_data.get("id")
                                    st.session_state["role"] = (user_data.get("role") or "employee").lower()
                                    st.session_state["username"] = display_name
                                    st.rerun()
                                else:
                                    st.error("Invalid username/email or password")
                        except Exception:
                            st.error("Could not connect to the sign-in service. Please try again.")

                with st.container(key="auth-switch"):
                    st.markdown("<div class='auth-divider'></div><div class='auth-footer-label'>New to MeetingAI?</div>", unsafe_allow_html=True)
                    if st.button("Create an account", key="go_register_button", use_container_width=True):
                        set_auth_mode("register")


def register():
    apply_theme()
    with st.container(key="auth-shell"):
        left_col, right_col = st.columns([0.95, 1.05], gap="medium")

        with left_col:
            with st.container(key="auth-brand"):
                st.markdown(
                    """
                    <div class='brand-badge'>AI</div>
                    <h1>MeetingAI</h1>
                    <p>Bring your team together and turn every meeting into clear next steps.</p>
                    <ul class='feature-list'>
                        <li>👥 Simple team onboarding</li>
                        <li>📅 Meetings and shared context</li>
                        <li>✅ Clear action accountability</li>
                    </ul>
                    """,
                    unsafe_allow_html=True,
                )

        with right_col:
            with st.container(key="auth-card"):
                st.markdown(
                    "<div class='auth-heading'><span>GET STARTED</span><h1>Create account</h1><p>Set up your profile to start organizing team meetings.</p></div>",
                    unsafe_allow_html=True,
                )
                with st.form("register_form"):
                    name = st.text_input("Full name", placeholder="Jane Doe")
                    email = st.text_input("Email address", placeholder="jane@company.com")
                    password = st.text_input("Password", type="password", placeholder="At least 6 characters")
                    confirm_password = st.text_input("Confirm password", type="password", placeholder="Repeat your password")
                    role = st.selectbox("Role", ["employee", "manager", "admin"], index=0)
                    submit = st.form_submit_button("Create account", use_container_width=True)

                    if submit:
                        if not name.strip() or not email.strip() or not password or not confirm_password:
                            st.error("Please complete all fields before creating your account.")
                        elif password != confirm_password:
                            st.error("Passwords do not match. Please re-enter them.")
                        else:
                            try:
                                payload = {"name": name.strip(), "email": email.strip(), "password": password, "role": role}
                                res = httpx.post(f"{BACKEND_URL}/auth/register", json=payload, timeout=20)
                                if res.status_code in (200, 201):
                                    st.session_state["auth_notice"] = "Account created successfully. Please sign in."
                                    st.session_state["auth_mode"] = "login"
                                    st.rerun()
                                else:
                                    error_text = res.text
                                    try:
                                        detail = res.json()
                                        if isinstance(detail, dict):
                                            error_text = detail.get("detail") or detail.get("message") or res.text
                                    except Exception:
                                        pass
                                    st.error(f"Unable to create account: {error_text}")
                            except Exception:
                                st.error("Could not connect to the registration service. Please try again.")

                with st.container(key="auth-switch"):
                    st.markdown("<div class='auth-divider'></div><div class='auth-footer-label'>Already have an account?</div>", unsafe_allow_html=True)
                    if st.button("Back to sign in", key="back_to_login_button", use_container_width=True):
                        set_auth_mode("login")

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

if not st.session_state.get("token"):
    if st.session_state.get("auth_mode") == "register":
        register()
    else:
        login()
else:
    # Professional sidebar
    st.markdown("""
    <div style='text-align:center; padding: 20px 0;'>
        <h2 style='color:#63b3ed; margin:0;'>🧠 MeetingAI</h2>
        <p style='color:#a0aec0; font-size:0.8rem;'>Intelligence Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    username = st.session_state.get("username", "User")
    role = st.session_state.get("role", "employee").upper()
    st.markdown(f"""
    <div class='metric-card' style='margin:10px 0;'>
        <p>👤 {username}</p>
        <p style='color:#68d391;'>● {role}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("Logout"):
        logout()
    
    st.sidebar.divider()
    
    # Navigation items with icons based on role
    role = st.session_state["role"]
    nav_options = []
    
    if role == "admin":
        nav_options = ["🏠 Dashboard", "👥 Users", "📊 All Meetings", "📤 Upload Meeting", "🎤 Voice Tasks", "📅 Calendar"]
    elif role == "manager":
        nav_options = ["🏠 Dashboard", "📤 Upload Meeting", "🔍 Analyse", "📋 Minutes", "📅 Calendar"]
    elif role == "employee":
        nav_options = ["🏠 My Tasks", "📅 Calendar", "🔔 Notifications"]
    else:
        nav_options = []
    
    page = st.sidebar.radio("Navigation", nav_options)
    
    st.sidebar.divider()
    st.sidebar.info("Running on Local Whisper Model (Base)")

    try:
        if page == "🏠 Dashboard":
            if role == "admin":
                import frontend.views.admin_dashboard as p_admin
                p_admin.show()
            elif role == "manager":
                import frontend.views.manager_dashboard as p_manager
                p_manager.show()
        elif page == "🏠 My Tasks":
            import frontend.views.employee_home as p_employee
            p_employee.show()
        elif page == "👥 Users":
            import frontend.views.admin_dashboard as p_admin
            p_admin.show_users() # Assuming show_users exists or will be added
        elif page == "📊 All Meetings":
            import frontend.views.admin_dashboard as p_admin
            p_admin.show_all_meetings()
        elif page == "🎤 Voice Tasks":
            import frontend.views.admin_dashboard as p_admin
            p_admin.show_voice_tasks()
        elif page == "📤 Upload Meeting":
            import frontend.views.upload_meeting as p_upload
            p_upload.show()
        elif page == "🔍 Analyse":
            import frontend.views.analyse_meeting as p_analyse
            p_analyse.show()
        elif page == "📋 Minutes":
            import frontend.views.meeting_minutes as p_minutes
            p_minutes.show()
        elif page == "📅 Calendar":
            import frontend.views.calendar_view as p_calendar
            p_calendar.show()
        elif page == "🔔 Notifications":
            import frontend.views.employee_home as p_employee
            p_employee.show()
    except Exception as e:
        st.error(f"Error loading page: {e}")
