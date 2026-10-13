import io
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_registration_and_login_work():
    email = f"coreflow-{uuid.uuid4().hex[:8]}@example.com"
    password = "secret123"

    register_resp = client.post(
        "/auth/register",
        json={"name": "Core Flow", "email": email, "password": password, "role": "employee"},
    )
    assert register_resp.status_code == 201, register_resp.text

    login_resp = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200, login_resp.text

    token = login_resp.json()["access_token"]
    me_resp = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200, me_resp.text
    assert me_resp.json()["email"] == email


def test_transcription_creates_meeting_and_transcript():
    email = f"transcribe-{uuid.uuid4().hex[:8]}@example.com"
    password = "secret123"
    client.post(
        "/auth/register",
        json={"name": "Transcriber", "email": email, "password": password, "role": "employee"},
    )
    login_resp = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    token = login_resp.json()["access_token"]

    class FakeWhisperModel:
        def transcribe(self, path):
            return {"text": "Hello everyone, thanks for the update."}

    with patch("backend.routes.transcription._get_whisper_model", return_value=FakeWhisperModel()), patch(
        "backend.routes.transcription.extract_voice_tasks", return_value=[]
    ):
        response = client.post(
            "/transcribe/",
            files={"file": ("sample.wav", io.BytesIO(b"fake-audio-data"), "audio/wav")},
            data={"title": "Weekly Standup"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["meeting_id"] > 0
    assert payload["transcript"] == "Hello everyone, thanks for the update."
