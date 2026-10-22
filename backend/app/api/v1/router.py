from fastapi import APIRouter

from app.api.v1.endpoints import catalog, dashboard, health, inventory, orders


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(dashboard.router)
api_router.include_router(catalog.router)
api_router.include_router(inventory.router)
api_router.include_router(orders.router)

