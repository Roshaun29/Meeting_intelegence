import streamlit as st
import httpx
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BACKEND_URL
from styles.theme import apply_theme, page_header

def show():
    apply_theme()
    page_header("Upload Meeting Recording", "Upload audio, review the transcript, then approve assignments", "📤")

    # How it works section
    st.markdown("""
    <div class='section-card'>
        <h3>⚡ How It Works</h3>
        <div style='display:flex; gap:20px; justify-content:space-between;'>
            <div style='text-align:center; flex:1;'>
                <div style='font-size:2rem;'>🎙️</div>
                <div style='font-weight:700; color:#1a3a8f;'>1. Upload</div>
                <div style='color:#64748b; font-size:0.85rem;'>Upload meeting audio</div>
            </div>
            <div style='text-align:center; flex:1;'>
                <div style='font-size:2rem;'>🤖</div>
                <div style='font-weight:700; color:#1a3a8f;'>2. Transcribe</div>
                <div style='color:#64748b; font-size:0.85rem;'>AI converts to text</div>
            </div>
            <div style='text-align:center; flex:1;'>
                <div style='font-size:2rem;'>🧠</div>
                <div style='font-weight:700; color:#1a3a8f;'>3. Extract</div>
                <div style='color:#64748b; font-size:0.85rem;'>NLP finds tasks</div>
            </div>
            <div style='text-align:center; flex:1;'>
                <div style='font-size:2rem;'>✅</div>
            <div style='font-weight:700; color:#1a3a8f;'>4. Review</div>
                <div style='color:#64748b; font-size:0.85rem;'>Confirm tasks and owners</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        title = st.text_input("📝 Meeting Title", placeholder="e.g. Weekly Team Standup — April 2026")
        audio_file = st.file_uploader(
            "🎵 Upload Audio Recording",
            type=["mp3", "wav", "m4a", "webm"],
            help="Supported: MP3, WAV, M4A, WebM (up to 200 MB)"
        )
        if audio_file:
            st.audio(audio_file)
        upload_btn = st.button("🚀 Upload & Transcribe", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='section-card'>
            <h3>Tips for Best Results</h3>
            <p style='color:#64748b; font-size:0.88rem; line-height:1.7;'>
            ✅ Speak names clearly<br>
            ✅ Say tasks directly:<br>
            &nbsp;&nbsp;<em>"John complete the report by Friday"</em><br>
            ✅ Mention deadlines explicitly<br>
            ✅ Use registered usernames<br><br>
            ⚠️ Make sure team members are registered in the system before uploading
            </p>
        </div>
        """, unsafe_allow_html=True)

    token = st.session_state.get('token')
    
    if upload_btn:
        if not title:
            st.error("⚠️ Please enter a meeting title")
        elif not audio_file:
            st.error("⚠️ Please upload an audio file")
        else:
            with st.spinner("🔄 Processing audio... This may take 1-3 minutes"):
                try:
                    files = {"file": (audio_file.name, audio_file.getvalue(), audio_file.type)}
                    data = {"title": title}
                    headers = {"Authorization": f"Bearer {token}"}
                    response = httpx.post(
                        f"{BACKEND_URL}/transcribe/",
                        files=files,
                        data=data,
                        headers=headers,
                        timeout=300
                    )
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state['meeting_id'] = result['meeting_id']
                        st.session_state['transcript'] = result['transcript']

                        # Success message
                        st.success(f"✅ Meeting processed successfully!")

                        st.info("Transcript is ready. Use Analyse to create reviewable task suggestions; no task is assigned until a manager approves it.")

                        # Show transcript
                        with st.expander("📄 View Full Transcript"):
                            st.text_area("", result['transcript'], height=250)

                        # Analyse button
                        if st.button("🔍 Run Full NLP Analysis →", use_container_width=True):
                            st.session_state['page'] = 'analyse_meeting'
                            st.rerun()
                    else:
                        st.error(f"❌ Error: {response.text}")
                except Exception as e:
                    st.error(f"❌ Connection error: {str(e)}")
