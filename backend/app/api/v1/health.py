from fastapi import APIRouter, Depends
from sqlmodel import Session, text

from app.core.db import get_session

router = APIRouter()


@router.get("/health")
def health_check(session: Session = Depends(get_session)) -> dict:
    try:
        session.exec(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "db": db_status,
    }
