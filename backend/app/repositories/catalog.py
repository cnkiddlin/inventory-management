from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import Category, Inventory, Product, Warehouse
from app.repositories.base import BaseRepository


class CatalogRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def list_categories(
        self, *, page: int, page_size: int, search: str | None = None
    ) -> tuple[list[tuple[Category, int]], int]:
        filters = []
        if search:
            filters.append(Category.name.ilike(f"%{search.strip()}%"))

        total = self.db.scalar(select(func.count(Category.id)).where(*filters)) or 0
        stmt = (
            select(Category, func.count(Product.id))
            .outerjoin(Product, Product.category_id == Category.id)
            .where(*filters)
            .group_by(Category.id)
            .order_by(Category.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.execute(stmt).all()), total

    def get_category(self, category_id: int) -> Category | None:
        return self.db.get(Category, category_id)

    def get_category_by_name(self, name: str) -> Category | None:
        return self.db.scalar(select(Category).where(func.lower(Category.name) == name.lower()))

    def product_count_for_category(self, category_id: int) -> int:
        return (
            self.db.scalar(select(func.count(Product.id)).where(Product.category_id == category_id))
            or 0
        )

    def list_products(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        category_id: int | None = None,
        status: str | None = None,
    ) -> tuple[list[tuple[Product, int, float]], int]:
        inventory_agg = (
            select(
                Inventory.product_id.label("product_id"),
                func.coalesce(func.sum(Inventory.quantity), 0).label("quantity"),
                func.coalesce(func.sum(Inventory.quantity * Product.cost_price), 0).label("value"),
            )
            .join(Product, Product.id == Inventory.product_id)
            .group_by(Inventory.product_id)
            .subquery()
        )

        filters = []
        if search:
            term = f"%{search.strip()}%"
            filters.append(
                or_(
                    Product.sku.ilike(term),
                    Product.name.ilike(term),
                    Product.model.ilike(term),
                )
            )
        if category_id:
            filters.append(Product.category_id == category_id)
        if status:
            filters.append(Product.status == status)

        total = self.db.scalar(select(func.count(Product.id)).where(*filters)) or 0
        stmt = (
            select(
                Product,
                func.coalesce(inventory_agg.c.quantity, 0),
                func.coalesce(inventory_agg.c.value, 0),
            )
            .outerjoin(inventory_agg, inventory_agg.c.product_id == Product.id)
            .options(joinedload(Product.category))
            .where(*filters)
            .order_by(Product.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.execute(stmt).all()), total

    def get_product(self, product_id: int) -> Product | None:
        return self.db.scalar(
            select(Product).options(joinedload(Product.category)).where(Product.id == product_id)
        )

    def get_product_by_sku(self, sku: str) -> Product | None:
        return self.db.scalar(select(Product).where(func.upper(Product.sku) == sku.upper()))

    def get_products_by_ids(self, product_ids: list[int]) -> list[Product]:
        if not product_ids:
            return []
        return list(self.db.scalars(select(Product).where(Product.id.in_(product_ids))).all())

    def product_stock_totals(self, product_id: int) -> tuple[int, float]:
        row = self.db.execute(
            select(
                func.coalesce(func.sum(Inventory.quantity), 0),
                func.coalesce(func.sum(Inventory.quantity * Product.cost_price), 0),
            )
            .select_from(Inventory)
            .join(Product, Product.id == Inventory.product_id)
            .where(Inventory.product_id == product_id)
        ).one()
        return int(row[0]), float(row[1])

    def list_product_options(self) -> list[Product]:
        return list(
            self.db.scalars(
                select(Product)
                .where(Product.status == "ACTIVE")
                .options(joinedload(Product.category))
                .order_by(Product.sku)
            ).all()
        )

    def list_warehouses(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        status: str | None = None,
    ) -> tuple[list[tuple[Warehouse, int, int, float]], int]:
        inventory_agg = (
            select(
                Inventory.warehouse_id.label("warehouse_id"),
                func.count(Inventory.product_id).label("sku_count"),
                func.coalesce(func.sum(Inventory.quantity), 0).label("units"),
                func.coalesce(func.sum(Inventory.quantity * Product.cost_price), 0).label("value"),
            )
            .join(Product, Product.id == Inventory.product_id)
            .group_by(Inventory.warehouse_id)
            .subquery()
        )

        filters = []
        if search:
            term = f"%{search.strip()}%"
            filters.append(
                or_(Warehouse.code.ilike(term), Warehouse.name.ilike(term), Warehouse.location.ilike(term))
            )
        if status:
            filters.append(Warehouse.status == status)

        total = self.db.scalar(select(func.count(Warehouse.id)).where(*filters)) or 0
        stmt = (
            select(
                Warehouse,
                func.coalesce(inventory_agg.c.sku_count, 0),
                func.coalesce(inventory_agg.c.units, 0),
                func.coalesce(inventory_agg.c.value, 0),
            )
            .outerjoin(inventory_agg, inventory_agg.c.warehouse_id == Warehouse.id)
            .where(*filters)
            .order_by(Warehouse.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.execute(stmt).all()), total

    def get_warehouse(self, warehouse_id: int) -> Warehouse | None:
        return self.db.get(Warehouse, warehouse_id)

    def get_warehouse_by_code(self, code: str) -> Warehouse | None:
        return self.db.scalar(select(Warehouse).where(func.upper(Warehouse.code) == code.upper()))

    def list_warehouse_options(self) -> list[Warehouse]:
        return list(
            self.db.scalars(
                select(Warehouse)
                .where(Warehouse.status == "ACTIVE")
                .order_by(Warehouse.code)
            ).all()
        )
