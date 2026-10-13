import streamlit as st
import httpx
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BACKEND_URL
from styles.theme import apply_theme, page_header
from datetime import datetime, date, timedelta

def get_deadline_badge(deadline_str: str) -> str:
    """Returns status badge based on deadline proximity."""
    if not deadline_str:
        return "⚪ No Deadline"
    try:
        # Try to parse date
        deadline = None
        for fmt in ["%Y-%m-%d", "%d %B %Y", "%B %d, %Y", "%d/%m/%Y"]:
            try:
                deadline = datetime.strptime(deadline_str.strip(), fmt).date()
                break
            except ValueError:
                continue
        
        if not deadline:
            # Fallback for ISO format with time
            try:
                deadline = datetime.fromisoformat(deadline_str.split('T')[0]).date()
            except:
                return "📅 " + deadline_str
        
        today = date.today()
        delta = (deadline - today).days
        
        if delta < 0:
            return "🔴 Overdue"
        elif delta <= 2:
            return "🟡 Due Soon"
        else:
            return "🟢 On Track"
    except Exception:
        return "📅 " + deadline_str

def show():
    apply_theme()
    page_header("My Task Calendar", "Weekly view of your assignments and deadlines", "📅")
    
    token = st.session_state.get('token')
    headers = {"Authorization": f"Bearer {token}"}

    # Navigation for weeks
    if 'week_offset' not in st.session_state:
        st.session_state.week_offset = 0

    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
    with col_nav1:
        if st.button("⬅️ Previous Week"):
            st.session_state.week_offset -= 1
            st.rerun()
    with col_nav3:
        if st.button("Next Week ➡️"):
            st.session_state.week_offset += 1
            st.rerun()

    # Calculate current week dates
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=st.session_state.week_offset)
    week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
    week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    try:
        # Fetch tasks (using all tasks and filtering locally for now)
        resp = httpx.get(f"{BACKEND_URL}/tasks/", headers=headers)
        if resp.status_code != 200:
            st.error("Could not load tasks.")
            return
        
        all_tasks = resp.json()
        user_id = st.session_state.get('user_id')
        
        # Filter: My tasks only (remove confirmed filter)
        tasks = [
            t for t in all_tasks
            if t.get("assigned_to") == user_id
        ]

        # 1. Weekly Grid
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        cols = st.columns(7)
        for i, (day, d) in enumerate(zip(week_days, week_dates)):
            with cols[i]:
                st.markdown(f"<div class='cal-day-header'>{day}<br><small>{d.strftime('%d %b')}</small></div>", unsafe_allow_html=True)
                st.markdown("<div class='cal-day-body'>", unsafe_allow_html=True)
                
                # Find tasks for this day
                day_tasks = []
                for t in tasks:
                    t_deadline = t.get("deadline")
                    if t_deadline:
                        try:
                            # Try multiple formats for date extraction
                            t_date = None
                            
                            # Format 1: ISO dates like "2026-04-15"
                            try:
                                t_date = datetime.fromisoformat(t_deadline.split('T')[0]).date()
                            except:
                                pass
                            
                            # Format 2: "5th April 2026" style dates
                            if not t_date:
                                import re
                                # Handle "5th April 2026", "15th April 2026", etc.
                                match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(\w+)\s+(\d{4})', t_deadline, re.IGNORECASE)
                                if match:
                                    day, month_name, year = match.groups()
                                    month_map = {
                                        'january': 1, 'february': 2, 'march': 3, 'april': 4,
                                        'may': 5, 'june': 6, 'july': 7, 'august': 8,
                                        'september': 9, 'october': 10, 'november': 11, 'december': 12
                                    }
                                    month = month_map.get(month_name.lower())
                                    if month:
                                        t_date = date(int(year), month, int(day))
                            
                            # Format 3: Standard numeric dates
                            if not t_date:
                                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
                                    try:
                                        t_date = datetime.strptime(t_deadline.strip()[:10], fmt).date()
                                        break
                                    except:
                                        continue
                            
                            if t_date and t_date == d:
                                day_tasks.append(t)
                        except:
                            continue
                
                for t in day_tasks:
                    badge = get_deadline_badge(t.get("deadline"))
                    cls = "overdue" if "Overdue" in badge else "due-soon" if "Soon" in badge else "on-track"
                    voice_icon = "🎙️ " if t.get("source") == "voice" else ""
                    st.markdown(f"<div class='cal-task-pill {cls}' title='{t['description']}'>{voice_icon}{t['description']}</div>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # 2. Detailed Task List
        st.divider()
        st.subheader("📋 Task Details & Updates")
        if not tasks:
            st.info("No tasks assigned yet.")
        else:
            for t in tasks:
                badge = get_deadline_badge(t.get("deadline"))
                card_cls = "overdue" if "Overdue" in badge else "due-soon" if "Soon" in badge else "on-track"
                voice_badge = "<span class='badge badge-blue'>🎙️ Voice Assigned</span>" if t.get("source") == "voice" else ""
                
                with st.container():
                    st.markdown(f"""
                    <div class='task-card {card_cls}'>
                        <div style='display:flex; justify-content:space-between; align-items:start;'>
                            <div>
                                <strong>{t['description']}</strong><br>
                                <small>📅 Due: {t.get('deadline', 'N/A')} | {badge}</small>
                            </div>
                            {voice_badge}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.caption(f"Current Status: **{t.get('status', 'pending')}**")
                    with c2:
                        new_status = st.selectbox(
                            "Update Status",
                            ["pending", "in_progress", "done"],
                            index=["pending", "in_progress", "done"].index(t.get('status', 'pending')),
                            key=f"cal_status_{t['id']}",
                            label_visibility="collapsed"
                        )
                        if new_status != t.get('status'):
                            httpx.patch(f"{BACKEND_URL}/tasks/{t['id']}/status", json={"status": new_status}, headers=headers)
                            st.rerun()

    except Exception as e:
        st.error(f"Error loading calendar: {e}")
