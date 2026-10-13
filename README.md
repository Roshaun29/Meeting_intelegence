# AI Meeting Intelligence

This project is a FastAPI + Streamlit meeting intelligence application that lets users upload recordings, transcribe meetings, review extracted action items, assign tasks, and track work on a lightweight internal calendar.

## Architecture

- Backend: FastAPI app in [backend/main.py](backend/main.py)
- Frontend: Streamlit pages in [frontend/app.py](frontend/app.py)
- Database: SQLAlchemy + SQLite by default in [backend/database/__init__.py](backend/database/__init__.py)
- Modeling: Unified ORM layer in [backend/database/models.py](backend/database/models.py)
- Auth: JWT-based authentication with bcrypt hashing in [backend/core/security.py](backend/core/security.py)
- AI/NLP helpers: utilities in [utils](utils)

## Current feature status

Core features that are working in the current codebase:

- User registration and login
- JWT authentication and protected routes
- Meeting upload and transcript generation with a mocked or local Whisper-style pipeline
- Review-first task extraction and assignment flow (task suggestions are not silently assigned)
- Notification creation for assigned work
- Internal role-based access for admin, manager, and employee users
- SQLite-backed persistence
- Persisted internal calendar events (`/calendar/`) with create, edit, list, and delete operations

Important caveats:

- The app uses a local heuristic/ML stack rather than a full external AI provider.
- Some optional features are partially implemented but not fully production-hardened.
- External calendar sync and SMTP email delivery are intentionally optional and require configuration.

## Prerequisites

- Python 3.11+
- pip and virtual environment support
- ffmpeg available on the system for audio processing

## Install

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

If you want spaCy language models for a richer NLP flow:

```bash
python -m spacy download en_core_web_sm
```

## Environment setup

Copy the example file and fill in the values you need:

```bash
copy .env.example .env
```

Required variables:

- DATABASE_URL
- SECRET_KEY
- ALGORITHM
- ACCESS_TOKEN_EXPIRE_MINUTES
- BACKEND_URL

The app falls back to a local SQLite database and development secret values when the environment is not configured, but production deployments should replace them with real secrets.

## Run the app

Backend:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8005 --reload
```

Frontend:

```bash
python -m streamlit run frontend/app.py --server.port 8501
```

Then open:

- Frontend: http://127.0.0.1:8501
- API docs: http://127.0.0.1:8005/docs

## Default seeded users

The application seeds sample users on first startup:

- admin@test.com / admin123
- manager@test.com / manager123
- monish@test.com / monish123

## Typical workflow

1. Sign in.
2. Upload a meeting recording.
3. Transcribe the recording.
4. Review the transcript.
5. Generate or review AI-derived task suggestions.
6. Save tasks and assign them to users.
7. Review notifications and task status.
8. Open the calendar or task lists for follow-up.

## Data and migrations

This project uses SQLite for local development and creates tables from the SQLAlchemy metadata at startup. The database is initialized via [backend/database/__init__.py](backend/database/__init__.py) and the seed logic is in [backend/main.py](backend/main.py).

For production-style upgrades, keep a backup of the current SQLite file before schema changes and apply changes in a migration script or in a dedicated migration tool.

The application also performs a small, non-destructive SQLite compatibility upgrade at startup for older databases: it adds processing diagnostics and task metadata while preserving existing rows. Calendar events are stored in the `calendar_events` table.

## Processing and task review

The upload endpoint accepts WAV, MP3, M4A, and WebM recordings up to 200 MB. Each recording receives a unique server-side filename. A meeting record is created before transcription so failures are retained with an actionable processing status rather than reported as a false success. Local Whisper is loaded lazily; if it is unavailable the API returns a 503 and marks the meeting as failed.

Task extraction is deliberately review-first. Suggested work starts as `pending_approval`; a task is linked to an actual user ID only after a manager/admin selects a registered account. Re-running the save endpoint will not create duplicate task descriptions for the same meeting.

## Testing

Regression tests for the core app workflow live in [tests/test_core_workflow.py](tests/test_core_workflow.py).

Run:

```bash
python -m pytest tests/test_core_workflow.py -q
```

Run the suite in a normal local Python environment:

```bash
python -m pytest -q
```

The included tests use FastAPI's `TestClient`. In the restricted execution host used for this repair, Windows asyncio socket-pair creation stalls before a request can be serviced, so HTTP end-to-end assertions could not be completed here. Syntax compilation and database initialization completed successfully; rerun the above command on the target development machine before deployment.

## Known limitations

- The project uses local heuristics and optional ML utilities rather than a full enterprise AI stack.
- Real-time external integrations such as Google Calendar, Microsoft Graph, and SMTP email delivery are not activated unless credentials are supplied.
- Optional analysis routes may be partial and should be treated as extension points rather than guaranteed production features.
- Audio processing depends on ffmpeg being available locally.
- The internal calendar is complete without external credentials. Google/Outlook sync remains intentionally unconfigured until OAuth credentials and consent scopes are supplied.
- Browser microphone recording and speaker diarization are not implemented in this Streamlit baseline; uploads retain no fabricated speaker identity.

## Troubleshooting

- If the backend cannot start, confirm the virtual environment is activated and dependencies were installed with pip.
- If the frontend cannot reach the backend, ensure the backend is running on port 8005 and the value in [frontend/config.py](frontend/config.py) matches.
- If uploads fail, verify the file extension is one of WAV, MP3, M4A, or WebM and the file is not empty.
- If authentication fails, confirm the password and email are correctly entered and the database has been initialized.
