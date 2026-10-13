from fastapi import APIRouter

router = APIRouter(prefix="/escalation", tags=["Escalation"])

@router.get("/")
def get_escalations():
    return {"message": "Escalation module placeholder"}
