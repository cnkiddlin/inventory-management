from datetime import date, datetime, timedelta, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import Category, Inventory, InventoryTransaction, Product, Warehouse
from app.repositories.base import BaseRepository


class InventoryRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    @staticmethod
    def _inventory_status_filter(status: str):
        if status == "OUT_OF_STOCK":
            return Inventory.quantity == 0
        if status == "LOW_STOCK":
            return and_(Inventory.quantity > 0, Inventory.quantity <= Product.safety_stock)
        if status == "IN_STOCK":
            return Inventory.quantity > Product.safety_stock
        return None

    def list_inventory(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        product_id: int | None = None,
        warehouse_id: int | None = None,
        category_id: int | None = None,
        status: str | None = None,
    ) -> tuple[list[Inventory], int]:
        filters = []
        if search:
            term = f"%{search.strip()}%"
            filters.append(or_(Product.sku.ilike(term), Product.name.ilike(term)))
        if product_id:
            filters.append(Inventory.product_id == product_id)
        if warehouse_id:
            filters.append(Inventory.warehouse_id == warehouse_id)
        if category_id:
            filters.append(Product.category_id == category_id)
        if status and (status_filter := self._inventory_status_filter(status)) is not None:
            filters.append(status_filter)

        base = (
            select(Inventory)
            .join(Product, Product.id == Inventory.product_id)
            .join(Warehouse, Warehouse.id == Inventory.warehouse_id)
            .join(Category, Category.id == Product.category_id)
            .where(*filters)
        )
        total = self.db.scalar(select(func.count()).select_from(base.order_by(None).subquery())) or 0
        stmt = (
            base.options(
                joinedload(Inventory.product).joinedload(Product.category),
                joinedload(Inventory.warehouse),
            )
            .order_by(Inventory.updated_at.desc(), Inventory.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all()), total

    def get_inventory(self, product_id: int, warehouse_id: int) -> Inventory | None:
        return self.db.scalar(
            select(Inventory).where(
                Inventory.product_id == product_id,
                Inventory.warehouse_id == warehouse_id,
            )
        )

    def get_inventory_for_update(self, product_id: int, warehouse_id: int) -> Inventory | None:
        return self.db.scalar(
            select(Inventory)
            .where(
                Inventory.product_id == product_id,
                Inventory.warehouse_id == warehouse_id,
            )
            .with_for_update()
        )

    def alerts(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        status: str | None = None,
    ) -> tuple[list[tuple[Product, int, int]], int]:
        stock_agg = (
            select(
                Inventory.product_id.label("product_id"),
                func.coalesce(func.sum(Inventory.quantity), 0).label("current_stock"),
                func.count(Inventory.id).label("warehouse_count"),
            )
            .group_by(Inventory.product_id)
            .subquery()
        )
        current_stock = func.coalesce(stock_agg.c.current_stock, 0)

        filters = [Product.status == "ACTIVE", current_stock <= Product.safety_stock]
        if search:
            term = f"%{search.strip()}%"
            filters.append(or_(Product.sku.ilike(term), Product.name.ilike(term)))
        if status == "OUT_OF_STOCK":
            filters.append(current_stock == 0)
        elif status == "LOW_STOCK":
            filters.append(current_stock > 0)

        base = (
            select(
                Product,
                current_stock.label("current_stock"),
                func.coalesce(stock_agg.c.warehouse_count, 0).label("warehouse_count"),
            )
            .outerjoin(stock_agg, stock_agg.c.product_id == Product.id)
            .options(joinedload(Product.category))
            .where(*filters)
        )
        total = self.db.scalar(select(func.count()).select_from(base.order_by(None).subquery())) or 0
        stmt = (
            base.order_by(current_stock.asc(), Product.safety_stock.desc(), Product.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.execute(stmt).all()), total

    def alert_counts(self) -> tuple[int, int]:
        stock_agg = (
            select(
                Inventory.product_id.label("product_id"),
                func.coalesce(func.sum(Inventory.quantity), 0).label("current_stock"),
            )
            .group_by(Inventory.product_id)
            .subquery()
        )
        current_stock = func.coalesce(stock_agg.c.current_stock, 0)
        low_or_out = self.db.scalar(
            select(func.count(Product.id))
            .outerjoin(stock_agg, stock_agg.c.product_id == Product.id)
            .where(Product.status == "ACTIVE", current_stock <= Product.safety_stock)
        ) or 0
        out = self.db.scalar(
            select(func.count(Product.id))
            .outerjoin(stock_agg, stock_agg.c.product_id == Product.id)
            .where(Product.status == "ACTIVE", current_stock == 0)
        ) or 0
        return int(low_or_out - out), int(out)

    def stock_breakdown(self, product_ids: list[int]) -> dict[int, list[dict[str, int | str]]]:
        if not product_ids:
            return {}
        rows = self.db.execute(
            select(Inventory.product_id, Warehouse.id, Warehouse.code, Warehouse.name, Inventory.quantity)
            .join(Warehouse, Warehouse.id == Inventory.warehouse_id)
            .where(Inventory.product_id.in_(product_ids))
            .order_by(Warehouse.id)
        ).all()
        result: dict[int, list[dict[str, int | str]]] = {}
        for product_id, warehouse_id, code, name, quantity in rows:
            result.setdefault(product_id, []).append(
                {
                    "warehouse_id": warehouse_id,
                    "warehouse_code": code,
                    "warehouse_name": name,
                    "quantity": int(quantity),
                }
            )
        return result

    def list_transactions(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        product_id: int | None = None,
        warehouse_id: int | None = None,
        transaction_type: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list[InventoryTransaction], int]:
        filters = []
        if search:
            term = f"%{search.strip()}%"
            filters.append(
                or_(
                    InventoryTransaction.transaction_no.ilike(term),
                    InventoryTransaction.reference_no.ilike(term),
                    Product.sku.ilike(term),
                    Product.name.ilike(term),
                )
            )
        if product_id:
            filters.append(InventoryTransaction.product_id == product_id)
        if warehouse_id:
            filters.append(InventoryTransaction.warehouse_id == warehouse_id)
        if transaction_type:
            filters.append(InventoryTransaction.transaction_type == transaction_type)
        if date_from:
            filters.append(InventoryTransaction.created_at >= datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc))
        if date_to:
            next_day = datetime.combine(date_to + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
            filters.append(InventoryTransaction.created_at < next_day)

        base = (
            select(InventoryTransaction)
            .join(Product, Product.id == InventoryTransaction.product_id)
            .join(Warehouse, Warehouse.id == InventoryTransaction.warehouse_id)
            .where(*filters)
        )
        total = self.db.scalar(select(func.count()).select_from(base.order_by(None).subquery())) or 0
        stmt = (
            base.options(
                joinedload(InventoryTransaction.product),
                joinedload(InventoryTransaction.warehouse),
            )
            .order_by(InventoryTransaction.created_at.desc(), InventoryTransaction.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all()), total

    def recent_transactions(self, limit: int = 8) -> list[InventoryTransaction]:
        return list(
            self.db.scalars(
                select(InventoryTransaction)
                .options(
                    joinedload(InventoryTransaction.product),
                    joinedload(InventoryTransaction.warehouse),
                )
                .order_by(InventoryTransaction.created_at.desc(), InventoryTransaction.id.desc())
                .limit(limit)
            ).all()
        )

    def inventory_summary(self) -> tuple[int, float]:
        row = self.db.execute(
            select(
                func.coalesce(func.sum(Inventory.quantity), 0),
                func.coalesce(func.sum(Inventory.quantity * Product.cost_price), 0),
            )
            .select_from(Inventory)
            .join(Product, Product.id == Inventory.product_id)
        ).one()
        return int(row[0]), float(row[1])

    def active_product_count(self) -> int:
        return self.db.scalar(select(func.count(Product.id)).where(Product.status == "ACTIVE")) or 0

    def active_warehouse_count(self) -> int:
        return (
            self.db.scalar(select(func.count(Warehouse.id)).where(Warehouse.status == "ACTIVE"))
            or 0
        )

    def trend(self, days: int = 14) -> list[tuple[date, str, int]]:
        end_day = datetime.now(timezone.utc).date()
        start_day = end_day - timedelta(days=days - 1)
        start_dt = datetime.combine(start_day, datetime.min.time(), tzinfo=timezone.utc)
        rows = self.db.execute(
            select(
                func.date(InventoryTransaction.created_at).label("day"),
                InventoryTransaction.transaction_type,
                func.sum(func.abs(InventoryTransaction.quantity_change)).label("quantity"),
            )
            .where(
                InventoryTransaction.created_at >= start_dt,
                InventoryTransaction.transaction_type.in_(["INBOUND", "OUTBOUND"]),
            )
            .group_by(func.date(InventoryTransaction.created_at), InventoryTransaction.transaction_type)
            .order_by(func.date(InventoryTransaction.created_at))
        ).all()
        return [(row[0], row[1], int(row[2])) for row in rows]

    def category_distribution(self) -> list[tuple[int, str, int, float, int]]:
        rows = self.db.execute(
            select(
                Category.id,
                Category.name,
                func.coalesce(func.sum(Inventory.quantity), 0),
                func.coalesce(func.sum(Inventory.quantity * Product.cost_price), 0),
                func.count(func.distinct(Product.id)),
            )
            .select_from(Category)
            .outerjoin(Product, Product.category_id == Category.id)
            .outerjoin(Inventory, Inventory.product_id == Product.id)
            .group_by(Category.id, Category.name)
            .order_by(Category.id)
        ).all()
        return [(row[0], row[1], int(row[2]), float(row[3]), int(row[4])) for row in rows]
