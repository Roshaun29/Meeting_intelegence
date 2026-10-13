import streamlit as st
import httpx
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BACKEND_URL
from styles.theme import apply_theme, page_header

def show():
    apply_theme()
    page_header("Meeting Minutes", "View and export meeting summaries", "📋")
    st.write("---")
    headers = {"Authorization": f"Bearer {st.session_state.get('token')}"}
    
    try:
        meetings = httpx.get(f"{BACKEND_URL}/meetings/", headers=headers).json()
        if not meetings:
            st.warning("No meetings found.")
            return
            
        meeting_options = {m["title"]: m["id"] for m in meetings}
        selected_title = st.selectbox("Select Meeting", list(meeting_options.keys()))
        meeting_id = meeting_options[selected_title]
        
        meeting_detail = httpx.get(f"{BACKEND_URL}/meetings/{meeting_id}", headers=headers).json()
        
        st.subheader("Transcript")
        st.text_area("Full Transcript", meeting_detail.get("transcript", "N/A"), height=200)
        
        nlp = meeting_detail.get("nlp_results", {})
        if nlp:
            st.subheader("AI Analysis")
            st.write("**Summary:**", nlp.get("summary"))
            st.write("**Action Items:**", nlp.get("action_items"))
            
            txt_content = f"MEETING MINUTES\n\nTitle: {selected_title}\n\nSUMMARY:\n{nlp.get('summary')}\n\nACTION ITEMS:\n{nlp.get('action_items')}\n\nTRANSCRIPT:\n{meeting_detail.get('transcript')}"
            st.download_button("Download as TXT", txt_content, file_name=f"Minutes_{selected_title}.txt")
            
    except Exception as e:
        st.error(f"Failed to load meeting minutes: {e}")
