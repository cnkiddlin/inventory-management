from typing import Literal

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_order_service
from app.schemas.common import PaginatedResponse
from app.schemas.orders import (
    InboundOrderCreate,
    InboundOrderRead,
    OutboundOrderCreate,
    OutboundOrderRead,
    StockTransferCreate,
    StockTransferRead,
)
from app.services.orders import OrderService


router = APIRouter(tags=["Stock Operations"])


@router.get(
    "/inbound-orders",
    response_model=PaginatedResponse[InboundOrderRead],
    summary="入库单列表",
)
def list_inbound_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: str | None = Query(None, max_length=160),
    status_filter: Literal["DRAFT", "CONFIRMED", "CANCELLED"] | None = Query(
        None, alias="status"
    ),
    warehouse_id: int | None = Query(None, gt=0),
    service: OrderService = Depends(get_order_service),
) -> PaginatedResponse[InboundOrderRead]:
    return service.list_inbound(
        page=page,
        page_size=page_size,
        search=search,
        status=status_filter,
        warehouse_id=warehouse_id,
    )


@router.post(
    "/inbound-orders",
    response_model=InboundOrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建入库单",
)
def create_inbound_order(
    payload: InboundOrderCreate, service: OrderService = Depends(get_order_service)
) -> InboundOrderRead:
    return service.create_inbound(payload)


@router.get(
    "/inbound-orders/{order_id}", response_model=InboundOrderRead, summary="入库单详情"
)
def get_inbound_order(
    order_id: int, service: OrderService = Depends(get_order_service)
) -> InboundOrderRead:
    return service.get_inbound(order_id)


@router.post(
    "/inbound-orders/{order_id}/confirm",
    response_model=InboundOrderRead,
    summary="确认入库",
)
def confirm_inbound_order(
    order_id: int, service: OrderService = Depends(get_order_service)
) -> InboundOrderRead:
    return service.confirm_inbound(order_id)


@router.get(
    "/outbound-orders",
    response_model=PaginatedResponse[OutboundOrderRead],
    summary="出库单列表",
)
def list_outbound_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: str | None = Query(None, max_length=160),
    status_filter: Literal["DRAFT", "CONFIRMED", "CANCELLED"] | None = Query(
        None, alias="status"
    ),
    warehouse_id: int | None = Query(None, gt=0),
    service: OrderService = Depends(get_order_service),
) -> PaginatedResponse[OutboundOrderRead]:
    return service.list_outbound(
        page=page,
        page_size=page_size,
        search=search,
        status=status_filter,
        warehouse_id=warehouse_id,
    )


@router.post(
    "/outbound-orders",
    response_model=OutboundOrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建出库单",
)
def create_outbound_order(
    payload: OutboundOrderCreate, service: OrderService = Depends(get_order_service)
) -> OutboundOrderRead:
    return service.create_outbound(payload)


@router.get(
    "/outbound-orders/{order_id}", response_model=OutboundOrderRead, summary="出库单详情"
)
def get_outbound_order(
    order_id: int, service: OrderService = Depends(get_order_service)
) -> OutboundOrderRead:
    return service.get_outbound(order_id)


@router.post(
    "/outbound-orders/{order_id}/confirm",
    response_model=OutboundOrderRead,
    summary="确认出库",
)
def confirm_outbound_order(
    order_id: int, service: OrderService = Depends(get_order_service)
) -> OutboundOrderRead:
    return service.confirm_outbound(order_id)


@router.get(
    "/stock-transfers",
    response_model=PaginatedResponse[StockTransferRead],
    summary="调拨单列表",
)
def list_stock_transfers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: str | None = Query(None, max_length=160),
    status_filter: Literal["DRAFT", "COMPLETED", "CANCELLED"] | None = Query(
        None, alias="status"
    ),
    warehouse_id: int | None = Query(None, gt=0),
    service: OrderService = Depends(get_order_service),
) -> PaginatedResponse[StockTransferRead]:
    return service.list_transfers(
        page=page,
        page_size=page_size,
        search=search,
        status=status_filter,
        warehouse_id=warehouse_id,
    )


@router.post(
    "/stock-transfers",
    response_model=StockTransferRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建调拨单",
)
def create_stock_transfer(
    payload: StockTransferCreate, service: OrderService = Depends(get_order_service)
) -> StockTransferRead:
    return service.create_transfer(payload)


@router.get(
    "/stock-transfers/{transfer_id}", response_model=StockTransferRead, summary="调拨单详情"
)
def get_stock_transfer(
    transfer_id: int, service: OrderService = Depends(get_order_service)
) -> StockTransferRead:
    return service.get_transfer(transfer_id)


@router.post(
    "/stock-transfers/{transfer_id}/complete",
    response_model=StockTransferRead,
    summary="完成库存调拨",
)
def complete_stock_transfer(
    transfer_id: int, service: OrderService = Depends(get_order_service)
) -> StockTransferRead:
    return service.complete_transfer(transfer_id)

