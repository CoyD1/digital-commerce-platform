from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/health/ready")
async def check_health_ready(db: AsyncSession = Depends(get_session)):
    query = text("Select 1")
    await db.execute(query)
    return {"status": "ready"}
