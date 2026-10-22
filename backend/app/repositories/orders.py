from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import (
    InboundOrder,
    InboundOrderItem,
    OutboundOrder,
    OutboundOrderItem,
    Product,
    StockTransfer,
    StockTransferItem,
    Warehouse,
)
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    @staticmethod
    def _inbound_loaders():
        return (
            selectinload(InboundOrder.warehouse),
            selectinload(InboundOrder.items).joinedload(InboundOrderItem.product),
        )

    @staticmethod
    def _outbound_loaders():
        return (
            selectinload(OutboundOrder.warehouse),
            selectinload(OutboundOrder.items).joinedload(OutboundOrderItem.product),
        )

    @staticmethod
    def _transfer_loaders():
        return (
            selectinload(StockTransfer.from_warehouse),
            selectinload(StockTransfer.to_warehouse),
            selectinload(StockTransfer.items).joinedload(StockTransferItem.product),
        )

    def list_inbound(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        status: str | None = None,
        warehouse_id: int | None = None,
    ) -> tuple[list[InboundOrder], int]:
        filters = []
        if search:
            term = f"%{search.strip()}%"
            filters.append(
                or_(InboundOrder.order_no.ilike(term), InboundOrder.supplier.ilike(term))
            )
        if status:
            filters.append(InboundOrder.status == status)
        if warehouse_id:
            filters.append(InboundOrder.warehouse_id == warehouse_id)
        total = self.db.scalar(select(func.count(InboundOrder.id)).where(*filters)) or 0
        stmt = (
            select(InboundOrder)
            .options(*self._inbound_loaders())
            .where(*filters)
            .order_by(InboundOrder.created_at.desc(), InboundOrder.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all()), int(total)

    def get_inbound(self, order_id: int, *, for_update: bool = False) -> InboundOrder | None:
        stmt = select(InboundOrder).options(*self._inbound_loaders()).where(InboundOrder.id == order_id)
        if for_update:
            stmt = stmt.with_for_update()
        return self.db.scalar(stmt)

    def list_outbound(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        status: str | None = None,
        warehouse_id: int | None = None,
    ) -> tuple[list[OutboundOrder], int]:
        filters = []
        if search:
            term = f"%{search.strip()}%"
            filters.append(
                or_(OutboundOrder.order_no.ilike(term), OutboundOrder.customer.ilike(term))
            )
        if status:
            filters.append(OutboundOrder.status == status)
        if warehouse_id:
            filters.append(OutboundOrder.warehouse_id == warehouse_id)
        total = self.db.scalar(select(func.count(OutboundOrder.id)).where(*filters)) or 0
        stmt = (
            select(OutboundOrder)
            .options(*self._outbound_loaders())
            .where(*filters)
            .order_by(OutboundOrder.created_at.desc(), OutboundOrder.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all()), int(total)

    def get_outbound(self, order_id: int, *, for_update: bool = False) -> OutboundOrder | None:
        stmt = select(OutboundOrder).options(*self._outbound_loaders()).where(OutboundOrder.id == order_id)
        if for_update:
            stmt = stmt.with_for_update()
        return self.db.scalar(stmt)

    def list_transfers(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        status: str | None = None,
        warehouse_id: int | None = None,
    ) -> tuple[list[StockTransfer], int]:
        filters = []
        if search:
            term = f"%{search.strip()}%"
            filters.append(
                or_(StockTransfer.transfer_no.ilike(term), StockTransfer.notes.ilike(term))
            )
        if status:
            filters.append(StockTransfer.status == status)
        if warehouse_id:
            filters.append(
                or_(
                    StockTransfer.from_warehouse_id == warehouse_id,
                    StockTransfer.to_warehouse_id == warehouse_id,
                )
            )
        total = self.db.scalar(select(func.count(StockTransfer.id)).where(*filters)) or 0
        stmt = (
            select(StockTransfer)
            .options(*self._transfer_loaders())
            .where(*filters)
            .order_by(StockTransfer.created_at.desc(), StockTransfer.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all()), int(total)

    def get_transfer(self, transfer_id: int, *, for_update: bool = False) -> StockTransfer | None:
        stmt = select(StockTransfer).options(*self._transfer_loaders()).where(StockTransfer.id == transfer_id)
        if for_update:
            stmt = stmt.with_for_update()
        return self.db.scalar(stmt)

    def product_for_update(self, product_id: int) -> Product | None:
        return self.db.scalar(select(Product).where(Product.id == product_id).with_for_update())

    def warehouse_exists(self, warehouse_id: int) -> bool:
        return self.db.scalar(select(func.count(Warehouse.id)).where(Warehouse.id == warehouse_id)) == 1
