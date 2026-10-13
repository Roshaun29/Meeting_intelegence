from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
import re
import json
from datetime import datetime
from functools import lru_cache


@lru_cache(maxsize=1)
def _load_spacy():
    """Lazy-load spaCy model; returns None if not available."""
    try:
        import spacy as _spacy
        return _spacy.load("en_core_web_sm")
    except Exception:
        return None


# Utils are imported lazily inside the route handler to avoid startup crash
# when transformers / torch aren't yet installed.


from backend.database import get_db
from backend.models.nlp_result import NLPResult
from backend.models.meeting import Meeting
from backend.models.user import User
from backend.models.task import Task, TaskStatus
from backend.models.user import UserRole
from backend.services.auth_service import get_current_user

router = APIRouter(prefix="/nlp/analyze", tags=["NLP Analysis"])

def extract_assignments_and_deadlines(action_items):
    """
    Use spaCy for assignments (NER) and regex for deadlines.
    """
    assignments = []
    deadlines = []
    
    try:
        nlp = _load_spacy()
        if nlp is None:
            return [], []
    except Exception:
        return [], []

    deadline_pattern = r"(by\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|next\s+week))"
    
    for item in action_items:
        doc = nlp(item)
        persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
        
        due_match = re.search(deadline_pattern, item, re.IGNORECASE)
        due_date = due_match.group(1) if due_match else "No deadline"
        
        if persons:
            for p in persons:
                assignments.append({"task": item, "assigned_to": p})
        else:
            assignments.append({"task": item, "assigned_to": "Unassigned"})
            
        if due_match:
            deadlines.append({"task": item, "deadline": due_date})
            
    return assignments, deadlines

@router.post("/{meeting_id}")
async def analyze_meeting(meeting_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Run the full NLP pipeline and save results to SQLite via SQLAlchemy.
    """
    try:
        # 1. Fetch meeting and transcript from DB
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER) and meeting.uploaded_by != current_user.id:
            raise HTTPException(status_code=403, detail="You cannot analyze this meeting")
        
        text = meeting.transcript
        if not text:
            raise HTTPException(status_code=400, detail="No transcript found for this meeting. Please transcribe first.")
            
        # 2. Run NLP Utils (lazy imports so heavy ML deps don't block server startup)
        from utils.summarization import generate_summary
        from utils.action_extraction import extract_action_items
        from utils.decision_detection import detect_decisions
        from utils.risk_detection import detect_risks
        from utils.sentiment_analysis import analyze_sentiment
        from utils.productivity_score import calculate_productivity_score
        from utils.voice_task_extractor import extract_voice_tasks

        summary = generate_summary(text)
        action_items = extract_action_items(text)
        decisions = detect_decisions(text)
        risks = detect_risks(text)
        sentiment = analyze_sentiment(text)
        score, label = calculate_productivity_score(action_items, decisions, risks, sentiment)
        
        # 3. Extract assignments and deadlines from action items
        assignments, deadlines = extract_assignments_and_deadlines(action_items)
        
        # 4. Save to Database
        # Upsert NLP results
        nlp_res = db.query(NLPResult).filter(NLPResult.meeting_id == meeting_id).first()
        if not nlp_res:
            nlp_res = NLPResult(meeting_id=meeting_id)
            db.add(nlp_res)

        nlp_res.summary = summary
        nlp_res.action_items = json.dumps(action_items)
        nlp_res.decisions = json.dumps(decisions)
        nlp_res.risks = json.dumps(risks)
        nlp_res.sentiment = sentiment
        nlp_res.productivity_score = score
        nlp_res.deadlines = json.dumps(deadlines)
        nlp_res.assignments = json.dumps(assignments)

        # 5. Extract Voice Tasks
        registered_users = db.query(User).all()
        # Convert user objects to dicts for the extractor
        users_list = [{"username": u.username, "id": u.id} for u in registered_users]
        
        voice_tasks = extract_voice_tasks(text, users_list)
        
        # 6. Save Voice Tasks as Pending Confirmation
        for vt in voice_tasks:
            # Find the user id if matched
            assignee_id = None
            if vt["assigned_to"] != "Unmatched":
                user = next((u for u in registered_users if u.username == vt["assigned_to"]), None)
                if user:
                    assignee_id = user.id
            
            if db.query(Task).filter(Task.meeting_id == meeting_id, Task.description == vt["task_description"]).first():
                continue
            new_task = Task(
                meeting_id=meeting_id,
                description=vt["task_description"],
                assigned_to=assignee_id,
                assigned_by_voice=vt["assigned_by"],
                deadline=vt["deadline"],
                status=TaskStatus.PENDING_APPROVAL,
                source="voice",
                confirmed=0  # False
            )
            db.add(new_task)
        
        # Update meeting status
        meeting.status = "completed"
        db.commit()

        return {
            "meeting_id": meeting_id,
            "summary": summary,
            "action_items": action_items,
            "decisions": decisions,
            "risks": risks,
            "sentiment": sentiment,
            "productivity_score": {"score": score, "label": label},
            "assignments": assignments,
            "deadlines": deadlines,
            "voice_tasks": voice_tasks,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
