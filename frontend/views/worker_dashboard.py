import streamlit as st
import httpx
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BACKEND_URL
from styles.theme import apply_theme, page_header

def show():
    apply_theme()
    page_header("Worker Dashboard", "Your assigned tasks and progress", "👷")
    st.write("---")
    headers = {"Authorization": f"Bearer {st.session_state.get('token')}"}
    
    try:
        tasks = httpx.get(f"{BACKEND_URL}/tasks/my", headers=headers).json()
        
        st.subheader("My Assigned Tasks")
        if isinstance(tasks, list) and tasks:
            for task in tasks:
                with st.expander(f"{task['description']} (Due: {task.get('deadline', 'N/A')})"):
                    st.write(f"Status: **{task['status']}**")
                    new_status = st.selectbox("Update Status", ["pending", "in_progress", "done"], index=["pending", "in_progress", "done"].index(task['status']), key=f"status_{task['id']}")
                    if st.button("Update", key=f"btn_{task['id']}"):
                        res = httpx.put(f"{BACKEND_URL}/tasks/{task['id']}", headers=headers, json={"status": new_status})
                        if res.status_code == 200:
                            st.success("Updated successfully! Please refresh.")
                        else:
                            st.error("Failed to update task.")
        else:
            st.info("No tasks assigned to you.")
    except Exception as e:
        st.error(f"Failed to load tasks: {e}")
