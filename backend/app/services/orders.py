from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.identifiers import make_reference
from app.models import (
    InboundOrder,
    InboundOrderItem,
    Inventory,
    InventoryTransaction,
    OutboundOrder,
    OutboundOrderItem,
    StockTransfer,
    StockTransferItem,
)
from app.repositories.catalog import CatalogRepository
from app.repositories.inventory import InventoryRepository
from app.repositories.orders import OrderRepository
from app.schemas.common import PaginatedResponse, paginated
from app.schemas.orders import (
    InboundItemRead,
    InboundOrderCreate,
    InboundOrderRead,
    OutboundItemRead,
    OutboundOrderCreate,
    OutboundOrderRead,
    StockTransferCreate,
    StockTransferRead,
    TransferItemRead,
)


def _inbound_read(order: InboundOrder) -> InboundOrderRead:
    items = [
        InboundItemRead(
            id=item.id,
            product_id=item.product_id,
            sku=item.product.sku,
            product_name=item.product.name,
            unit=item.product.unit,
            quantity=item.quantity,
            unit_cost=float(item.unit_cost),
            line_total=float(item.unit_cost) * item.quantity,
        )
        for item in order.items
    ]
    return InboundOrderRead(
        id=order.id,
        order_no=order.order_no,
        warehouse_id=order.warehouse_id,
        warehouse_name=order.warehouse.name,
        supplier=order.supplier,
        status=order.status,
        notes=order.notes,
        created_by=order.created_by,
        confirmed_at=order.confirmed_at,
        created_at=order.created_at,
        item_count=len(items),
        total_quantity=sum(item.quantity for item in items),
        total_value=sum(item.line_total for item in items),
        items=items,
    )


def _outbound_read(order: OutboundOrder) -> OutboundOrderRead:
    items = [
        OutboundItemRead(
            id=item.id,
            product_id=item.product_id,
            sku=item.product.sku,
            product_name=item.product.name,
            unit=item.product.unit,
            quantity=item.quantity,
            unit_price=float(item.unit_price),
            line_total=float(item.unit_price) * item.quantity,
        )
        for item in order.items
    ]
    return OutboundOrderRead(
        id=order.id,
        order_no=order.order_no,
        warehouse_id=order.warehouse_id,
        warehouse_name=order.warehouse.name,
        customer=order.customer,
        status=order.status,
        notes=order.notes,
        created_by=order.created_by,
        confirmed_at=order.confirmed_at,
        created_at=order.created_at,
        item_count=len(items),
        total_quantity=sum(item.quantity for item in items),
        total_value=sum(item.line_total for item in items),
        items=items,
    )


def _transfer_read(transfer: StockTransfer) -> StockTransferRead:
    items = [
        TransferItemRead(
            id=item.id,
            product_id=item.product_id,
            sku=item.product.sku,
            product_name=item.product.name,
            unit=item.product.unit,
            quantity=item.quantity,
        )
        for item in transfer.items
    ]
    return StockTransferRead(
        id=transfer.id,
        transfer_no=transfer.transfer_no,
        from_warehouse_id=transfer.from_warehouse_id,
        from_warehouse_name=transfer.from_warehouse.name,
        to_warehouse_id=transfer.to_warehouse_id,
        to_warehouse_name=transfer.to_warehouse.name,
        status=transfer.status,
        notes=transfer.notes,
        created_by=transfer.created_by,
        completed_at=transfer.completed_at,
        created_at=transfer.created_at,
        item_count=len(items),
        total_quantity=sum(item.quantity for item in items),
        items=items,
    )


class OrderService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.orders = OrderRepository(db)
        self.catalog = CatalogRepository(db)
        self.inventory = InventoryRepository(db)

    def _validate_warehouse(self, warehouse_id: int):
        warehouse = self.catalog.get_warehouse(warehouse_id)
        if not warehouse:
            raise NotFoundError("仓库不存在")
        if warehouse.status != "ACTIVE":
            raise ValidationError("仓库已停用，不能发生库存业务")
        return warehouse

    def _normalize_items(self, items):
        normalized: dict[int, object] = {}
        for item in items:
            if item.product_id in normalized:
                existing = normalized[item.product_id]
                existing.quantity += item.quantity
                if hasattr(item, "unit_cost") and item.unit_cost is not None:
                    existing.unit_cost = item.unit_cost
                if hasattr(item, "unit_price") and item.unit_price is not None:
                    existing.unit_price = item.unit_price
            else:
                normalized[item.product_id] = item.model_copy()
        products = {product.id: product for product in self.catalog.get_products_by_ids(list(normalized))}
        missing = sorted(set(normalized) - set(products))
        if missing:
            raise ValidationError(f"商品不存在: {missing}")
        inactive = [product.sku for product in products.values() if product.status != "ACTIVE"]
        if inactive:
            raise ValidationError(f"停用商品不能参与库存业务: {', '.join(inactive)}")
        return normalized, products

    def list_inbound(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        status: str | None,
        warehouse_id: int | None,
    ) -> PaginatedResponse[InboundOrderRead]:
        rows, total = self.orders.list_inbound(
            page=page,
            page_size=page_size,
            search=search,
            status=status,
            warehouse_id=warehouse_id,
        )
        return paginated([_inbound_read(row) for row in rows], total, page, page_size)

    def get_inbound(self, order_id: int) -> InboundOrderRead:
        order = self.orders.get_inbound(order_id)
        if not order:
            raise NotFoundError("入库单不存在")
        return _inbound_read(order)

    def create_inbound(self, payload: InboundOrderCreate) -> InboundOrderRead:
        self._validate_warehouse(payload.warehouse_id)
        items, products = self._normalize_items(payload.items)
        order = InboundOrder(
            order_no=make_reference("IN"),
            warehouse_id=payload.warehouse_id,
            supplier=payload.supplier,
            notes=payload.notes,
            created_by=payload.created_by,
            status="DRAFT",
        )
        for product_id, item in items.items():
            cost = item.unit_cost if item.unit_cost is not None else float(products[product_id].cost_price)
            order.items.append(
                InboundOrderItem(
                    product_id=product_id,
                    quantity=item.quantity,
                    unit_cost=Decimal(str(cost)),
                )
            )
        self.orders.add(order)
        self.db.commit()
        return self.get_inbound(order.id)

    def confirm_inbound(self, order_id: int) -> InboundOrderRead:
        order = self.orders.get_inbound(order_id, for_update=True)
        if not order:
            raise NotFoundError("入库单不存在")
        if order.status != "DRAFT":
            raise ConflictError("该入库单已处理，不能重复确认")
        self._validate_warehouse(order.warehouse_id)
        try:
            for item in order.items:
                inventory_row = self.inventory.get_inventory_for_update(
                    item.product_id, order.warehouse_id
                )
                if inventory_row is None:
                    inventory_row = Inventory(
                        product_id=item.product_id,
                        warehouse_id=order.warehouse_id,
                        quantity=0,
                        reserved_quantity=0,
                    )
                    self.inventory.add(inventory_row)
                    self.db.flush()
                inventory_row.quantity += item.quantity
                self.db.add(
                    InventoryTransaction(
                        transaction_no=make_reference("TX"),
                        product_id=item.product_id,
                        warehouse_id=order.warehouse_id,
                        transaction_type="INBOUND",
                        quantity_change=item.quantity,
                        balance_after=inventory_row.quantity,
                        reference_type="INBOUND_ORDER",
                        reference_id=order.id,
                        reference_no=order.order_no,
                        notes=f"入库单 {order.order_no} 确认入库",
                    )
                )
            order.status = "CONFIRMED"
            order.confirmed_at = datetime.now(timezone.utc)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return self.get_inbound(order_id)

    def list_outbound(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        status: str | None,
        warehouse_id: int | None,
    ) -> PaginatedResponse[OutboundOrderRead]:
        rows, total = self.orders.list_outbound(
            page=page,
            page_size=page_size,
            search=search,
            status=status,
            warehouse_id=warehouse_id,
        )
        return paginated([_outbound_read(row) for row in rows], total, page, page_size)

    def get_outbound(self, order_id: int) -> OutboundOrderRead:
        order = self.orders.get_outbound(order_id)
        if not order:
            raise NotFoundError("出库单不存在")
        return _outbound_read(order)

    def create_outbound(self, payload: OutboundOrderCreate) -> OutboundOrderRead:
        self._validate_warehouse(payload.warehouse_id)
        items, products = self._normalize_items(payload.items)
        order = OutboundOrder(
            order_no=make_reference("OUT"),
            warehouse_id=payload.warehouse_id,
            customer=payload.customer,
            notes=payload.notes,
            created_by=payload.created_by,
            status="DRAFT",
        )
        for product_id, item in items.items():
            price = item.unit_price if item.unit_price is not None else float(products[product_id].selling_price)
            order.items.append(
                OutboundOrderItem(
                    product_id=product_id,
                    quantity=item.quantity,
                    unit_price=Decimal(str(price)),
                )
            )
        self.orders.add(order)
        self.db.commit()
        return self.get_outbound(order.id)

    def confirm_outbound(self, order_id: int) -> OutboundOrderRead:
        order = self.orders.get_outbound(order_id, for_update=True)
        if not order:
            raise NotFoundError("出库单不存在")
        if order.status != "DRAFT":
            raise ConflictError("该出库单已处理，不能重复确认")
        self._validate_warehouse(order.warehouse_id)

        inventory_rows = {}
        shortages = []
        for item in order.items:
            inventory_row = self.inventory.get_inventory_for_update(
                item.product_id, order.warehouse_id
            )
            if inventory_row is None:
                available = 0
            else:
                available = inventory_row.quantity - inventory_row.reserved_quantity
            if available < item.quantity:
                shortages.append(
                    {
                        "product_id": item.product_id,
                        "sku": item.product.sku,
                        "requested": item.quantity,
                        "available": available,
                    }
                )
            inventory_rows[item.product_id] = inventory_row
        if shortages:
            self.db.rollback()
            raise ConflictError("可用库存不足，出库单未确认", details=shortages)

        try:
            for item in order.items:
                inventory_row = inventory_rows[item.product_id]
                if inventory_row is None:
                    raise ConflictError("库存记录不存在，无法出库")
                inventory_row.quantity -= item.quantity
                self.db.add(
                    InventoryTransaction(
                        transaction_no=make_reference("TX"),
                        product_id=item.product_id,
                        warehouse_id=order.warehouse_id,
                        transaction_type="OUTBOUND",
                        quantity_change=-item.quantity,
                        balance_after=inventory_row.quantity,
                        reference_type="OUTBOUND_ORDER",
                        reference_id=order.id,
                        reference_no=order.order_no,
                        notes=f"出库单 {order.order_no} 确认出库",
                    )
                )
            order.status = "CONFIRMED"
            order.confirmed_at = datetime.now(timezone.utc)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return self.get_outbound(order_id)

    def list_transfers(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        status: str | None,
        warehouse_id: int | None,
    ) -> PaginatedResponse[StockTransferRead]:
        rows, total = self.orders.list_transfers(
            page=page,
            page_size=page_size,
            search=search,
            status=status,
            warehouse_id=warehouse_id,
        )
        return paginated([_transfer_read(row) for row in rows], total, page, page_size)

    def get_transfer(self, transfer_id: int) -> StockTransferRead:
        transfer = self.orders.get_transfer(transfer_id)
        if not transfer:
            raise NotFoundError("调拨单不存在")
        return _transfer_read(transfer)

    def create_transfer(self, payload: StockTransferCreate) -> StockTransferRead:
        self._validate_warehouse(payload.from_warehouse_id)
        self._validate_warehouse(payload.to_warehouse_id)
        items, _ = self._normalize_items(payload.items)
        transfer = StockTransfer(
            transfer_no=make_reference("TR"),
            from_warehouse_id=payload.from_warehouse_id,
            to_warehouse_id=payload.to_warehouse_id,
            notes=payload.notes,
            created_by=payload.created_by,
            status="DRAFT",
        )
        for product_id, item in items.items():
            transfer.items.append(StockTransferItem(product_id=product_id, quantity=item.quantity))
        self.orders.add(transfer)
        self.db.commit()
        return self.get_transfer(transfer.id)

    def complete_transfer(self, transfer_id: int) -> StockTransferRead:
        transfer = self.orders.get_transfer(transfer_id, for_update=True)
        if not transfer:
            raise NotFoundError("调拨单不存在")
        if transfer.status != "DRAFT":
            raise ConflictError("该调拨单已处理，不能重复完成")
        self._validate_warehouse(transfer.from_warehouse_id)
        self._validate_warehouse(transfer.to_warehouse_id)

        source_rows = {}
        destination_rows = {}
        shortages = []
        for item in transfer.items:
            source = self.inventory.get_inventory_for_update(
                item.product_id, transfer.from_warehouse_id
            )
            destination = self.inventory.get_inventory_for_update(
                item.product_id, transfer.to_warehouse_id
            )
            available = source.quantity - source.reserved_quantity if source else 0
            if available < item.quantity:
                shortages.append(
                    {
                        "product_id": item.product_id,
                        "sku": item.product.sku,
                        "requested": item.quantity,
                        "available": available,
                    }
                )
            source_rows[item.product_id] = source
            destination_rows[item.product_id] = destination
        if shortages:
            self.db.rollback()
            raise ConflictError("调出仓库可用库存不足，调拨未完成", details=shortages)

        try:
            for item in transfer.items:
                source = source_rows[item.product_id]
                destination = destination_rows[item.product_id]
                if source is None:
                    raise ConflictError("调出仓库库存记录不存在")
                if destination is None:
                    destination = Inventory(
                        product_id=item.product_id,
                        warehouse_id=transfer.to_warehouse_id,
                        quantity=0,
                        reserved_quantity=0,
                    )
                    self.inventory.add(destination)
                    self.db.flush()
                source.quantity -= item.quantity
                destination.quantity += item.quantity
                self.db.add_all(
                    [
                        InventoryTransaction(
                            transaction_no=make_reference("TX"),
                            product_id=item.product_id,
                            warehouse_id=transfer.from_warehouse_id,
                            transaction_type="TRANSFER_OUT",
                            quantity_change=-item.quantity,
                            balance_after=source.quantity,
                            reference_type="STOCK_TRANSFER",
                            reference_id=transfer.id,
                            reference_no=transfer.transfer_no,
                            notes=f"调拨单 {transfer.transfer_no} 调出",
                        ),
                        InventoryTransaction(
                            transaction_no=make_reference("TX"),
                            product_id=item.product_id,
                            warehouse_id=transfer.to_warehouse_id,
                            transaction_type="TRANSFER_IN",
                            quantity_change=item.quantity,
                            balance_after=destination.quantity,
                            reference_type="STOCK_TRANSFER",
                            reference_id=transfer.id,
                            reference_no=transfer.transfer_no,
                            notes=f"调拨单 {transfer.transfer_no} 调入",
                        ),
                    ]
                )
            transfer.status = "COMPLETED"
            transfer.completed_at = datetime.now(timezone.utc)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return self.get_transfer(transfer_id)
