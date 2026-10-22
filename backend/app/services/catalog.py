from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models import Category, Product, Warehouse
from app.repositories.catalog import CatalogRepository
from app.schemas.catalog import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    WarehouseCreate,
    WarehouseRead,
    WarehouseUpdate,
)
from app.schemas.common import PaginatedResponse, paginated


class CatalogService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CatalogRepository(db)

    @staticmethod
    def _category_read(category: Category, product_count: int) -> CategoryRead:
        return CategoryRead(
            id=category.id,
            name=category.name,
            description=category.description,
            product_count=product_count,
            created_at=category.created_at,
        )

    @staticmethod
    def _product_read(product: Product, current_stock: int, inventory_value: float) -> ProductRead:
        return ProductRead(
            id=product.id,
            sku=product.sku,
            name=product.name,
            description=product.description,
            category_id=product.category_id,
            category_name=product.category.name,
            cost_price=float(product.cost_price),
            selling_price=float(product.selling_price),
            unit=product.unit,
            safety_stock=product.safety_stock,
            status=product.status,
            current_stock=current_stock,
            inventory_value=inventory_value,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )

    @staticmethod
    def _warehouse_read(
        warehouse: Warehouse,
        sku_count: int,
        total_units: int,
        total_value: float,
    ) -> WarehouseRead:
        utilization = (total_units / warehouse.capacity * 100) if warehouse.capacity else 0
        return WarehouseRead(
            id=warehouse.id,
            code=warehouse.code,
            name=warehouse.name,
            location=warehouse.location,
            manager_name=warehouse.manager_name,
            phone=warehouse.phone,
            capacity=warehouse.capacity,
            status=warehouse.status,
            sku_count=sku_count,
            total_units=total_units,
            total_value=total_value,
            utilization_percent=round(utilization, 1),
            created_at=warehouse.created_at,
        )

    def list_categories(
        self, *, page: int, page_size: int, search: str | None
    ) -> PaginatedResponse[CategoryRead]:
        rows, total = self.repo.list_categories(page=page, page_size=page_size, search=search)
        return paginated(
            [self._category_read(category, count) for category, count in rows],
            total,
            page,
            page_size,
        )

    def create_category(self, payload: CategoryCreate) -> CategoryRead:
        if self.repo.get_category_by_name(payload.name):
            raise ConflictError("分类名称已存在")
        category = Category(name=payload.name, description=payload.description)
        self.repo.add(category)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("分类名称已存在") from exc
        self.db.refresh(category)
        return self._category_read(category, 0)

    def update_category(self, category_id: int, payload: CategoryUpdate) -> CategoryRead:
        category = self.repo.get_category(category_id)
        if not category:
            raise NotFoundError("分类不存在")
        values = payload.model_dump(exclude_unset=True)
        if "name" in values:
            duplicate = self.repo.get_category_by_name(values["name"])
            if duplicate and duplicate.id != category_id:
                raise ConflictError("分类名称已存在")
        for key, value in values.items():
            setattr(category, key, value)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("分类名称已存在") from exc
        self.db.refresh(category)
        return self._category_read(category, self.repo.product_count_for_category(category_id))

    def list_products(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        category_id: int | None,
        status: str | None,
    ) -> PaginatedResponse[ProductRead]:
        rows, total = self.repo.list_products(
            page=page,
            page_size=page_size,
            search=search,
            category_id=category_id,
            status=status,
        )
        return paginated(
            [self._product_read(product, int(stock), float(value)) for product, stock, value in rows],
            total,
            page,
            page_size,
        )

    def get_product(self, product_id: int) -> ProductRead:
        product = self.repo.get_product(product_id)
        if not product:
            raise NotFoundError("商品不存在")
        stock, value = self.repo.product_stock_totals(product_id)
        return self._product_read(product, stock, value)

    def list_product_options(self) -> list[ProductRead]:
        products = self.repo.list_product_options()
        result = []
        for product in products:
            stock, value = self.repo.product_stock_totals(product.id)
            result.append(self._product_read(product, stock, value))
        return result

    def create_product(self, payload: ProductCreate) -> ProductRead:
        if not self.repo.get_category(payload.category_id):
            raise ValidationError("商品分类不存在")
        if self.repo.get_product_by_sku(payload.sku):
            raise ConflictError("SKU 已存在")
        product = Product(
            sku=payload.sku,
            name=payload.name.strip(),
            description=payload.description,
            category_id=payload.category_id,
            cost_price=Decimal(str(payload.cost_price)),
            selling_price=Decimal(str(payload.selling_price)),
            unit=payload.unit,
            safety_stock=payload.safety_stock,
            status=payload.status,
        )
        self.repo.add(product)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("SKU 已存在") from exc
        return self.get_product(product.id)

    def update_product(self, product_id: int, payload: ProductUpdate) -> ProductRead:
        product = self.repo.get_product(product_id)
        if not product:
            raise NotFoundError("商品不存在")
        values = payload.model_dump(exclude_unset=True)
        if "category_id" in values and not self.repo.get_category(values["category_id"]):
            raise ValidationError("商品分类不存在")
        if "sku" in values:
            duplicate = self.repo.get_product_by_sku(values["sku"])
            if duplicate and duplicate.id != product_id:
                raise ConflictError("SKU 已存在")
        for key, value in values.items():
            if key in {"cost_price", "selling_price"}:
                value = Decimal(str(value))
            setattr(product, key, value)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("商品编码或分类数据冲突") from exc
        return self.get_product(product_id)

    def list_warehouses(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        status: str | None,
    ) -> PaginatedResponse[WarehouseRead]:
        rows, total = self.repo.list_warehouses(
            page=page, page_size=page_size, search=search, status=status
        )
        return paginated(
            [
                self._warehouse_read(warehouse, int(sku_count), int(units), float(value))
                for warehouse, sku_count, units, value in rows
            ],
            total,
            page,
            page_size,
        )

    def list_warehouse_options(self) -> list[WarehouseRead]:
        result = []
        for warehouse in self.repo.list_warehouse_options():
            row, _ = self.repo.list_warehouses(page=1, page_size=1000, search=warehouse.code)
            match = next((item for item in row if item[0].id == warehouse.id), None)
            if match:
                _, sku_count, units, value = match
                result.append(self._warehouse_read(warehouse, int(sku_count), int(units), float(value)))
        return result

    def get_warehouse(self, warehouse_id: int) -> WarehouseRead:
        warehouse = self.repo.get_warehouse(warehouse_id)
        if not warehouse:
            raise NotFoundError("仓库不存在")
        rows, _ = self.repo.list_warehouses(page=1, page_size=1000, search=warehouse.code)
        match = next((item for item in rows if item[0].id == warehouse_id), None)
        if not match:
            return self._warehouse_read(warehouse, 0, 0, 0)
        _, sku_count, units, value = match
        return self._warehouse_read(warehouse, int(sku_count), int(units), float(value))

    def create_warehouse(self, payload: WarehouseCreate) -> WarehouseRead:
        if self.repo.get_warehouse_by_code(payload.code):
            raise ConflictError("仓库编码已存在")
        warehouse = Warehouse(
            code=payload.code,
            name=payload.name.strip(),
            location=payload.location.strip(),
            manager_name=payload.manager_name,
            phone=payload.phone,
            capacity=payload.capacity,
            status=payload.status,
        )
        self.repo.add(warehouse)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("仓库编码已存在") from exc
        return self.get_warehouse(warehouse.id)

    def update_warehouse(self, warehouse_id: int, payload: WarehouseUpdate) -> WarehouseRead:
        warehouse = self.repo.get_warehouse(warehouse_id)
        if not warehouse:
            raise NotFoundError("仓库不存在")
        values = payload.model_dump(exclude_unset=True)
        if "code" in values:
            duplicate = self.repo.get_warehouse_by_code(values["code"])
            if duplicate and duplicate.id != warehouse_id:
                raise ConflictError("仓库编码已存在")
        for key, value in values.items():
            setattr(warehouse, key, value)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("仓库编码已存在") from exc
        return self.get_warehouse(warehouse_id)

