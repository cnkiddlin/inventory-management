from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.catalog import CatalogService
from app.services.dashboard import DashboardService
from app.services.inventory import InventoryService
from app.services.orders import OrderService


def get_catalog_service(db: Session = Depends(get_db)) -> CatalogService:
    return CatalogService(db)


def get_inventory_service(db: Session = Depends(get_db)) -> InventoryService:
    return InventoryService(db)


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    return DashboardService(db)


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    return OrderService(db)

