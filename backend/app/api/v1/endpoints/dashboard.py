from fastapi import APIRouter, Depends

from app.api.deps import get_dashboard_service
from app.schemas.dashboard import DashboardRead
from app.services.dashboard import DashboardService


router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard", response_model=DashboardRead, summary="库存运营看板")
def get_dashboard(service: DashboardService = Depends(get_dashboard_service)) -> DashboardRead:
    return service.get_dashboard()

