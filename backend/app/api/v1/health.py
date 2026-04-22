from fastapi import APIRouter, Depends, Response
from sqlmodel import text
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import get_session

router = APIRouter(prefix="/api/v1")


@router.get("/health")
async def health_check(
    response: Response, session: AsyncSession = Depends(get_session)
) -> dict:
    try:
        await session.exec(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    if db_status == "error":
        response.status_code = 503

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "db": db_status,
    }
