from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_inventory_service
from app.schemas.common import PaginatedResponse
from app.schemas.inventory import (
    InventoryAlertRead,
    InventoryRead,
    InventoryTransactionRead,
)
from app.services.inventory import InventoryService


router = APIRouter(tags=["Inventory"])


@router.get("/inventory", response_model=PaginatedResponse[InventoryRead], summary="库存列表")
def list_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: str | None = Query(None, max_length=160),
    product_id: int | None = Query(None, gt=0),
    warehouse_id: int | None = Query(None, gt=0),
    category_id: int | None = Query(None, gt=0),
    status_filter: Literal["IN_STOCK", "LOW_STOCK", "OUT_OF_STOCK"] | None = Query(
        None, alias="status"
    ),
    service: InventoryService = Depends(get_inventory_service),
) -> PaginatedResponse[InventoryRead]:
    return service.list_inventory(
        page=page,
        page_size=page_size,
        search=search,
        product_id=product_id,
        warehouse_id=warehouse_id,
        category_id=category_id,
        status=status_filter,
    )


@router.get(
    "/inventory/alerts",
    response_model=PaginatedResponse[InventoryAlertRead],
    summary="低库存与缺货预警",
)
def list_inventory_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: str | None = Query(None, max_length=160),
    status_filter: Literal["LOW_STOCK", "OUT_OF_STOCK"] | None = Query(None, alias="status"),
    service: InventoryService = Depends(get_inventory_service),
) -> PaginatedResponse[InventoryAlertRead]:
    return service.list_alerts(
        page=page, page_size=page_size, search=search, status=status_filter
    )


@router.get(
    "/inventory/transactions",
    response_model=PaginatedResponse[InventoryTransactionRead],
    summary="库存流水",
)
def list_inventory_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: str | None = Query(None, max_length=160),
    product_id: int | None = Query(None, gt=0),
    warehouse_id: int | None = Query(None, gt=0),
    transaction_type: Literal[
        "INBOUND", "OUTBOUND", "TRANSFER_IN", "TRANSFER_OUT", "ADJUSTMENT"
    ]
    | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    service: InventoryService = Depends(get_inventory_service),
) -> PaginatedResponse[InventoryTransactionRead]:
    return service.list_transactions(
        page=page,
        page_size=page_size,
        search=search,
        product_id=product_id,
        warehouse_id=warehouse_id,
        transaction_type=transaction_type,
        date_from=date_from,
        date_to=date_to,
    )
