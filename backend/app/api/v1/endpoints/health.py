from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.schemas.health import HealthRead


router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthRead, summary="服务健康检查")
def health_check(db: Session = Depends(get_db)) -> HealthRead:
    db.execute(text("SELECT 1"))
    return HealthRead(
        status="ok",
        database="connected",
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc),
    )

