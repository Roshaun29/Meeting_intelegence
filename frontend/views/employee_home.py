import streamlit as st
import httpx
import requests
from datetime import date, datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BACKEND_URL
from styles.theme import apply_theme, page_header

def show_notifications_banner(token, backend_url):
    try:
        response = httpx.get(
            f"{backend_url}/notifications/",
            headers={"Authorization": f"Bearer {token}"}
        )
        notifs = [n for n in response.json() if not n.get('is_read')]
    except:
        notifs = []

    if notifs:
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#1a365d,#2a4a7f);
                    border:1px solid #4299e1; border-radius:10px;
                    padding:12px 18px; margin-bottom:15px;'>
            🔔 <strong style='color:#63b3ed;'>You have {len(notifs)} new notification(s)</strong>
        </div>
        """, unsafe_allow_html=True)
        for notif in notifs[:3]:
            st.markdown(f"""
            <div class='notif-banner'>
                📌 <span style='color:#e2e8f0;'>{notif['message']}</span>
            </div>
            """, unsafe_allow_html=True)

def show_task_bar(tasks):
    total = len(tasks)
    pending = len([t for t in tasks if t['status'] == 'pending'])
    in_progress = len([t for t in tasks if t['status'] == 'in_progress'])
    done = len([t for t in tasks if t['status'] == 'done'])
    overdue = len([t for t in tasks if t.get('deadline') and
                   datetime.strptime(t['deadline'][:10], '%Y-%m-%d').date() < date.today()
                   and t['status'] != 'done'])

    col1, col2, col3, col4, col5 = st.columns(5)
    metrics = [
        (col1, "📋 Total", total, "#63b3ed"),
        (col2, "⏳ Pending", pending, "#f6ad55"),
        (col3, "🔄 In Progress", in_progress, "#76e4f7"),
        (col4, "✅ Done", done, "#68d391"),
        (col5, "🔴 Overdue", overdue, "#fc8181"),
    ]
    for col, label, value, color in metrics:
        with col:
            st.markdown(f"""
            <div class='metric-card'>
                <h2 style='color:{color};'>{value}</h2>
                <p>{label}</p>
            </div>
            """, unsafe_allow_html=True)

def show_task_list(tasks, token, backend_url):
    st.markdown("### 📝 My Tasks")
    if not tasks:
        st.markdown("""
        <div style='text-align:center; padding:40px; color:#4a5568;'>
            <h3>No tasks assigned yet</h3>
            <p>Your manager will assign tasks after a meeting</p>
        </div>
        """, unsafe_allow_html=True)
        return

    for task in tasks:
        deadline_str = task.get('deadline', '')[:10] if task.get('deadline') else 'No deadline'
        if deadline_str != 'No deadline':
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
                days_left = (deadline - date.today()).days
                if days_left < 0:
                    card_class = "overdue"
                    time_label = f"🔴 Overdue by {abs(days_left)} days"
                elif days_left <= 2:
                    card_class = "due-soon"
                    time_label = f"🟡 Due in {days_left} days"
                else:
                    card_class = "on-track"
                    time_label = f"🟢 Due in {days_left} days"
                deadline_display = deadline.strftime('%d %b %Y')
            except:
                card_class = "on-track"
                time_label = deadline_str
                deadline_display = deadline_str
        else:
            card_class = "on-track"
            time_label = "No deadline set"
            deadline_display = "—"

        col1, col2, col3 = st.columns([4, 2, 1])
        with col1:
            st.markdown(f"""
            <div class='task-card {card_class}'>
                <strong style='color:white; font-size:1rem;'>{task['description']}</strong><br>
                <small style='color:#a0aec0;'>
                    📅 {deadline_display} &nbsp;|&nbsp; {time_label}
                </small>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            new_status = st.selectbox(
                "",
                ["pending", "in_progress", "done"],
                index=["pending", "in_progress", "done"].index(task.get('status','pending')),
                key=f"task_status_{task['id']}",
                label_visibility="collapsed"
            )
        with col3:
            st.write("")
            if st.button("💾 Save", key=f"save_{task['id']}"):
                update_task_status(task['id'], new_status, token, backend_url)
                st.rerun()

def update_task_status(task_id, new_status, token, backend_url):
    try:
        response = requests.patch(
            f"{backend_url}/tasks/{task_id}/status",
            json={"status": new_status},
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            st.success("✅")
            st.rerun()
    except Exception as e:
        st.error(f"Failed to update status: {e}")

def show():
    apply_theme()
    page_header("My Tasks", "Your assigned tasks and deadlines", "👷")
    
    token = st.session_state.get('token')
    
    from frontend.config import BACKEND_URL
    show_notifications_banner(token, BACKEND_URL)
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/tasks/",
            headers={"Authorization": f"Bearer {token}"}
        )
        all_tasks = response.json() if response.status_code == 200 else []
        
        # Filter for ONLY tasks assigned to current user
        user_id = st.session_state.get('user_id')
        tasks = [t for t in all_tasks if t.get("assigned_to") == user_id]
        
        show_task_bar(tasks)
        st.write("")
        show_task_list(tasks, token, BACKEND_URL)
    except Exception as e:
        st.error(f"Error loading tasks: {e}")
        tasks = []
        
        show_task_bar(tasks)
        st.write("")
        show_task_list(tasks, token, BACKEND_URL)
