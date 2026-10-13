from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json

from backend.database import get_db
from backend.models.nlp_result import NLPResult

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/worker")
async def get_worker_alerts(name: str, db: Session = Depends(get_db)):
    try:
        rows = db.query(NLPResult).all()
        alerts = []
        for row in rows:
            if not row.assignments or not row.deadlines:
                continue
            assignments = json.loads(row.assignments)
            deadlines = json.loads(row.deadlines)
            
            for task in assignments:
                if task.get('assigned_to', '').lower() == name.lower():
                    dl = next((d['deadline'] for d in deadlines if d['task'] == task['task']), "No deadline")
                    if "overdue" in dl.lower() or "passed" in dl.lower():
                        alerts.append({
                            "type": "overdue",
                            "message": f"Task Overdue: {task['task'][:50]}...",
                            "meeting_id": row.meeting_id,
                            "severity": "high"
                        })
        return alerts
    except Exception as e:
        return []

@router.get("/manager")
async def get_manager_alerts(db: Session = Depends(get_db)):
    try:
        rows = db.query(NLPResult).all()
        alerts = []
        for row in rows:
            if not row.risks or not row.assignments or not row.deadlines:
                continue
            risks = json.loads(row.risks)
            assignments = json.loads(row.assignments)
            deadlines = json.loads(row.deadlines)
            
            if len(risks) >= 3:
                alerts.append({
                    "type": "high_risk",
                    "message": f"High risk detected in meeting {row.meeting_id}",
                    "meeting_id": row.meeting_id,
                    "severity": "high"
                })
            
            unassigned = [t for t in assignments if t.get('assigned_to') == "Unassigned"]
            if unassigned:
                alerts.append({
                    "type": "unassigned",
                    "message": f"{len(unassigned)} unassigned tasks in meeting {row.meeting_id}",
                    "meeting_id": row.meeting_id,
                    "severity": "medium"
                })
                
            no_dl = [t for t in deadlines if t.get('deadline') == "No deadline"]
            if no_dl:
                alerts.append({
                    "type": "no_deadline",
                    "message": f"Tasks with no deadlines in meeting {row.meeting_id}",
                    "meeting_id": row.meeting_id,
                    "severity": "low"
                })

        return alerts
    except Exception as e:
        return []
