import streamlit as st
import httpx
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BACKEND_URL
from styles.theme import apply_theme, page_header

def show():
    apply_theme()
    page_header("Analyse Meeting", "Extract insights and assign tasks", "🔍")
    st.write("---")
    headers = {"Authorization": f"Bearer {st.session_state.get('token')}"}
    
    try:
        meetings = httpx.get(f"{BACKEND_URL}/meetings/", headers=headers).json()
        if not meetings:
            st.warning("No meetings found. Please upload one first.")
            return
            
        meeting_options = {m["title"]: m["id"] for m in meetings}
        selected_title = st.selectbox("Select Meeting", list(meeting_options.keys()))
        meeting_id = meeting_options[selected_title]
        
        if st.button("Analyse Meeting"):
            with st.spinner("Analysing meeting via NLP pipeline..."):
                res = httpx.post(f"{BACKEND_URL}/nlp/analyze/{meeting_id}", headers=headers, timeout=60.0)
                if res.status_code == 200:
                    st.success("Analysis Complete!")
                    st.json(res.json())
                else:
                    st.error(f"Failed: {res.text}")
                    
    except Exception as e:
        st.error(f"Failed to load analysis page: {e}")
