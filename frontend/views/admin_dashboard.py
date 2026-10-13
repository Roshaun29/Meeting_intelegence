import streamlit as st
import httpx
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BACKEND_URL
from styles.theme import apply_theme, page_header

def show():
    apply_theme()
    page_header("Admin Dashboard", "System overview and system-wide metrics", "🏠")
    
    headers = {"Authorization": f"Bearer {st.session_state.get('token')}"}
    try:
        tasks_res = httpx.get(f"{BACKEND_URL}/tasks/", headers=headers).json()
        tasks_list = tasks_res if isinstance(tasks_res, list) else []
        voice_tasks_count = sum(1 for t in tasks_list if t.get("source") == "voice")
        
        # Add to the existing metrics in render_admin_content
        # (I will modify render_admin_content instead of just adding here)
    except:
        voice_tasks_count = 0
    
    render_admin_content(voice_tasks_count)

def show_users():
    apply_theme()
    page_header("User Management", "Add, edit, or remove system users", "👥")
    render_user_management()

def show_all_meetings():
    apply_theme()
    page_header("All Meetings", "View all meetings and transcripts in the system", "📊")
    render_all_meetings()

def show_voice_tasks():
    apply_theme()
    page_header("Voice Tasks", "Confirm or reject tasks extracted from voice", "🎙️")
    render_voice_tasks_confirmation()

def render_admin_content(voice_tasks_count=0):
    headers = {"Authorization": f"Bearer {st.session_state.get('token')}"}
    try:
        meetings_res = httpx.get(f"{BACKEND_URL}/meetings/", headers=headers).json()
        users_res    = httpx.get(f"{BACKEND_URL}/auth/users",    headers=headers).json()
        tasks_res    = httpx.get(f"{BACKEND_URL}/tasks/",    headers=headers).json()
        
        total_meetings = len(meetings_res) if isinstance(meetings_res, list) else 0
        total_users    = len(users_res)    if isinstance(users_res,    list) else 0
        
        tasks_list   = tasks_res  if isinstance(tasks_res,  list) else []
        tasks_done   = sum(1 for t in tasks_list if t.get("status") == "done")
        tasks_pending = sum(1 for t in tasks_list if t.get("status") in ["pending", "in_progress"])
        
        st.markdown("### 🖥️ System Overview")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("📅 Total Meetings",    total_meetings)
        col2.metric("👥 Total Users",        total_users)
        col3.metric("✅ Tasks Completed",    tasks_done)
        col4.metric("⏳ Tasks Pending",      tasks_pending)
        col5.metric("🎙️ Voice Tasks",       voice_tasks_count)
        
        st.divider()
        st.subheader("📊 Recent System Activity")
        if meetings_res:
            df_meetings = pd.DataFrame(meetings_res)
            st.dataframe(df_meetings[["title", "created_at", "transcript_snippet"]], use_container_width=True)
    except Exception as e:
        st.error(f"Error loading admin overview: {e}")

def render_user_management():
    headers = {"Authorization": f"Bearer {st.session_state.get('token')}"}
    try:
        users_res = httpx.get(f"{BACKEND_URL}/auth/users", headers=headers).json()
        if isinstance(users_res, list):
            st.dataframe(pd.DataFrame(users_res), use_container_width=True)
            
            with st.expander("➕ Add New User"):
                with st.form("add_user_form"):
                    new_username = st.text_input("Username")
                    new_password = st.text_input("Password", type="password")
                    new_role = st.selectbox("Role", ["admin", "manager", "employee"])
                    if st.form_submit_button("Create User"):
                        r = httpx.post(f"{BACKEND_URL}/auth/register", 
                                     json={"username": new_username, "password": new_password, "role": new_role})
                        if r.status_code == 200:
                            st.success("User created!")
                            st.rerun()
                        else:
                            st.error(f"Failed: {r.text}")
    except Exception as e:
        st.error(f"Error loading users: {e}")

def render_all_meetings():
    headers = {"Authorization": f"Bearer {st.session_state.get('token')}"}
    try:
        meetings_res = httpx.get(f"{BACKEND_URL}/meetings/", headers=headers).json()
        if meetings_res:
            for m in meetings_res:
                with st.expander(f"📄 {m['title']} - {m['created_at']}"):
                    st.write(f"**ID:** {m['id']}")
                    st.write(f"**Snippet:** {m['transcript_snippet']}")
                    if st.button("View Full Details", key=f"view_{m['id']}"):
                        st.session_state['view_meeting_id'] = m['id']
                        # You could redirect to a specific meeting view here
    except Exception as e:
        st.error(f"Error loading meetings: {e}")

def render_voice_tasks_confirmation():
    headers = {"Authorization": f"Bearer {st.session_state.get('token')}"}
    try:
        tasks_res = httpx.get(f"{BACKEND_URL}/tasks/", headers=headers).json()
        tasks_list = tasks_res if isinstance(tasks_res, list) else []
        voice_pending = [t for t in tasks_list if t.get("source") == "voice" and not t.get("confirmed")]
        
        if voice_pending:
            for task in voice_pending:
                with st.container():
                    c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
                    c1.markdown(f"**{task['description']}**")
                    c2.markdown(task.get("assigned_to_name") or "⚠️ Unmatched")
                    c3.markdown(task.get("deadline") or "—")
                    c4.markdown(f"by *{task.get('assigned_by_voice') or 'admin'}*")
                    with c5:
                        if st.button("✅", key=f"conf_{task['id']}"):
                            httpx.post(f"{BACKEND_URL}/tasks/{task['id']}/confirm", headers=headers)
                            st.success("Confirmed!")
                            st.rerun()
                        if st.button("❌", key=f"rej_{task['id']}"):
                            httpx.delete(f"{BACKEND_URL}/tasks/{task['id']}", headers=headers)
                            st.success("Rejected and deleted.")
                            st.rerun()
        else:
            st.info("No voice tasks pending confirmation.")
    except Exception as e:
        st.error(f"Error loading voice tasks: {e}")
