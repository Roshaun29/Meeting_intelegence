import streamlit as st
import httpx
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from config import BACKEND_URL
from styles.theme import apply_theme, page_header

def show():
    apply_theme()
    page_header("Manager Dashboard", "Team progress and productivity insights", "👔")
    headers = {"Authorization": f"Bearer {st.session_state.get('token')}"}
    
    try:
        meetings_res = httpx.get(f"{BACKEND_URL}/meetings/", headers=headers).json()
        tasks_res = httpx.get(f"{BACKEND_URL}/tasks/", headers=headers).json()
        alerts_res = httpx.get(f"{BACKEND_URL}/alerts/manager", headers=headers).json()
        
        meetings = meetings_res if isinstance(meetings_res, list) else []
        tasks = tasks_res if isinstance(tasks_res, list) else []
        alerts = alerts_res if isinstance(alerts_res, list) else []
        
        # 1. Team Progress Bar
        total_tasks = len(tasks)
        done_tasks = sum(1 for t in tasks if t.get("status") == "done")
        progress = done_tasks / total_tasks if total_tasks > 0 else 0
        
        st.markdown("### 📈 Team Task Progress")
        st.progress(progress)
        st.write(f"**{done_tasks}** of **{total_tasks}** tasks completed ({int(progress*100)}%)")
        
        # 2. Alerts Section
        if alerts or any(t.get("status") == "pending" and not t.get("assigned_to") for t in tasks):
            st.error("⚠️ Action Required")
            unassigned = [t for t in tasks if not t.get("assigned_to")]
            if unassigned:
                st.warning(f"You have **{len(unassigned)}** unassigned tasks!")
            for alert in alerts:
                st.info(f"🚨 {alert.get('message', 'Risk Alert')}")
        
        # 3. Voice Task Summary
        voice_tasks = [t for t in tasks if t.get("source") == "voice"]
        if voice_tasks:
            st.subheader("🎙️ Voice Task Summary")
            rows = [
                {
                    "Task": t["description"],
                    "Assigned To": t.get("assigned_to_name") or f"User ID {t.get('assigned_to')}",
                    "Deadline": t.get("deadline") or "—",
                    "Status": t.get("status")
                }
                for t in voice_tasks
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
        
        # 4. Productivity Chart
        st.divider()
        st.subheader("🚀 Productivity Scores by Meeting")
        scores = {}
        if meetings:
            df_meetings = pd.DataFrame(meetings)
            # Check for productivity scores in NLP results
            if "nlp_results" in df_meetings.columns:
                chart_data = df_meetings[["title", "nlp_results"]].set_index("title")
                # Extract productivity scores
                for title, nlp in chart_data.iterrows():
                    if isinstance(nlp, dict) and "productivity_score" in nlp:
                        scores[title] = nlp["productivity_score"]
            if scores:
                score_series = pd.Series(scores)
                st.bar_chart(score_series)
            else:
                st.info("No productivity scores available yet. Analyse some meetings first!")
        
        # 5. Team Task Table & Export
        st.divider()
        st.subheader("📋 All Team Tasks")
        if tasks:
            df_tasks = pd.DataFrame(tasks)
            st.dataframe(df_tasks, use_container_width=True)
            
            csv = df_tasks.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Export Team Tasks as CSV",
                data=csv,
                file_name='team_tasks.csv',
                mime='text/csv',
                use_container_width=True
            )
        else:
            st.info("No team tasks found.")
            
    except Exception as e:
        st.error(f"Failed to load manager dashboard: {e}")
