from sqlalchemy.orm import Session

from app.models import Inventory, InventoryTransaction
from app.repositories.inventory import InventoryRepository
from app.schemas.common import PaginatedResponse, paginated
from app.schemas.inventory import (
    InventoryAlertRead,
    InventoryRead,
    InventoryTransactionRead,
)


def inventory_status(quantity: int, safety_stock: int) -> str:
    if quantity <= 0:
        return "OUT_OF_STOCK"
    if quantity <= safety_stock:
        return "LOW_STOCK"
    return "IN_STOCK"


def serialize_inventory(record: Inventory) -> InventoryRead:
    product = record.product
    warehouse = record.warehouse
    available = record.quantity - record.reserved_quantity
    return InventoryRead(
        id=record.id,
        product_id=product.id,
        sku=product.sku,
        product_name=product.name,
        model=product.model,
        category_name=product.category.name,
        warehouse_id=warehouse.id,
        warehouse_code=warehouse.code,
        warehouse_name=warehouse.name,
        unit=product.unit,
        quantity=record.quantity,
        reserved_quantity=record.reserved_quantity,
        available_quantity=available,
        safety_stock=product.safety_stock,
        status=inventory_status(record.quantity, product.safety_stock),
        updated_at=record.updated_at,
    )


def serialize_transaction(transaction: InventoryTransaction) -> InventoryTransactionRead:
    return InventoryTransactionRead(
        id=transaction.id,
        transaction_no=transaction.transaction_no,
        product_id=transaction.product_id,
        sku=transaction.product.sku,
        product_name=transaction.product.name,
        model=transaction.product.model,
        warehouse_id=transaction.warehouse_id,
        warehouse_name=transaction.warehouse.name,
        transaction_type=transaction.transaction_type,
        quantity_change=transaction.quantity_change,
        balance_after=transaction.balance_after,
        reference_type=transaction.reference_type,
        reference_id=transaction.reference_id,
        reference_no=transaction.reference_no,
        notes=transaction.notes,
        created_at=transaction.created_at,
    )


class InventoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = InventoryRepository(db)

    def list_inventory(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        product_id: int | None,
        warehouse_id: int | None,
        category_id: int | None,
        status: str | None,
    ) -> PaginatedResponse[InventoryRead]:
        records, total = self.repo.list_inventory(
            page=page,
            page_size=page_size,
            search=search,
            product_id=product_id,
            warehouse_id=warehouse_id,
            category_id=category_id,
            status=status,
        )
        return paginated([serialize_inventory(record) for record in records], total, page, page_size)

    def list_alerts(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        status: str | None,
    ) -> PaginatedResponse[InventoryAlertRead]:
        rows, total = self.repo.alerts(
            page=page, page_size=page_size, search=search, status=status
        )
        product_ids = [product.id for product, _, _ in rows]
        breakdown = self.repo.stock_breakdown(product_ids)
        items = []
        for product, current_stock, warehouse_count in rows:
            current = int(current_stock)
            shortage = max(product.safety_stock - current, 0)
            items.append(
                InventoryAlertRead(
                    product_id=product.id,
                    sku=product.sku,
                    product_name=product.name,
                    model=product.model,
                    category_name=product.category.name,
                    unit=product.unit,
                    current_stock=current,
                    safety_stock=product.safety_stock,
                    shortage=shortage,
                    suggested_replenishment=shortage,
                    status="OUT_OF_STOCK" if current == 0 else "LOW_STOCK",
                    warehouse_count=int(warehouse_count),
                    warehouse_stock=breakdown.get(product.id, []),
                )
            )
        return paginated(items, total, page, page_size)

    def list_transactions(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        product_id: int | None,
        warehouse_id: int | None,
        transaction_type: str | None,
        date_from,
        date_to,
    ) -> PaginatedResponse[InventoryTransactionRead]:
        records, total = self.repo.list_transactions(
            page=page,
            page_size=page_size,
            search=search,
            product_id=product_id,
            warehouse_id=warehouse_id,
            transaction_type=transaction_type,
            date_from=date_from,
            date_to=date_to,
        )
        return paginated(
            [serialize_transaction(record) for record in records], total, page, page_size
        )
