from typing import Literal

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_catalog_service
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
from app.schemas.common import PaginatedResponse
from app.services.catalog import CatalogService


router = APIRouter(tags=["Catalog"])


@router.get("/categories", response_model=PaginatedResponse[CategoryRead], summary="分类列表")
def list_categories(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: str | None = Query(None, max_length=80),
    service: CatalogService = Depends(get_catalog_service),
) -> PaginatedResponse[CategoryRead]:
    return service.list_categories(page=page, page_size=page_size, search=search)


@router.post(
    "/categories",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="新增分类",
)
def create_category(
    payload: CategoryCreate, service: CatalogService = Depends(get_catalog_service)
) -> CategoryRead:
    return service.create_category(payload)


@router.patch("/categories/{category_id}", response_model=CategoryRead, summary="编辑分类")
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    service: CatalogService = Depends(get_catalog_service),
) -> CategoryRead:
    return service.update_category(category_id, payload)


@router.get("/products", response_model=PaginatedResponse[ProductRead], summary="商品列表")
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: str | None = Query(None, max_length=160),
    category_id: int | None = Query(None, gt=0),
    status_filter: Literal["ACTIVE", "INACTIVE"] | None = Query(None, alias="status"),
    service: CatalogService = Depends(get_catalog_service),
) -> PaginatedResponse[ProductRead]:
    return service.list_products(
        page=page,
        page_size=page_size,
        search=search,
        category_id=category_id,
        status=status_filter,
    )


@router.get("/products/options", response_model=list[ProductRead], summary="商品下拉选项")
def list_product_options(
    service: CatalogService = Depends(get_catalog_service),
) -> list[ProductRead]:
    return service.list_product_options()


@router.get("/products/{product_id}", response_model=ProductRead, summary="商品详情")
def get_product(
    product_id: int, service: CatalogService = Depends(get_catalog_service)
) -> ProductRead:
    return service.get_product(product_id)


@router.post(
    "/products",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="新增商品",
)
def create_product(
    payload: ProductCreate, service: CatalogService = Depends(get_catalog_service)
) -> ProductRead:
    return service.create_product(payload)


@router.patch("/products/{product_id}", response_model=ProductRead, summary="编辑商品")
def update_product(
    product_id: int,
    payload: ProductUpdate,
    service: CatalogService = Depends(get_catalog_service),
) -> ProductRead:
    return service.update_product(product_id, payload)


@router.get("/warehouses", response_model=PaginatedResponse[WarehouseRead], summary="仓库列表")
def list_warehouses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: str | None = Query(None, max_length=120),
    status_filter: Literal["ACTIVE", "INACTIVE"] | None = Query(None, alias="status"),
    service: CatalogService = Depends(get_catalog_service),
) -> PaginatedResponse[WarehouseRead]:
    return service.list_warehouses(
        page=page, page_size=page_size, search=search, status=status_filter
    )


@router.get("/warehouses/options", response_model=list[WarehouseRead], summary="仓库下拉选项")
def list_warehouse_options(
    service: CatalogService = Depends(get_catalog_service),
) -> list[WarehouseRead]:
    return service.list_warehouse_options()


@router.get("/warehouses/{warehouse_id}", response_model=WarehouseRead, summary="仓库详情")
def get_warehouse(
    warehouse_id: int, service: CatalogService = Depends(get_catalog_service)
) -> WarehouseRead:
    return service.get_warehouse(warehouse_id)


@router.post(
    "/warehouses",
    response_model=WarehouseRead,
    status_code=status.HTTP_201_CREATED,
    summary="新增仓库",
)
def create_warehouse(
    payload: WarehouseCreate, service: CatalogService = Depends(get_catalog_service)
) -> WarehouseRead:
    return service.create_warehouse(payload)


@router.patch("/warehouses/{warehouse_id}", response_model=WarehouseRead, summary="编辑仓库")
def update_warehouse(
    warehouse_id: int,
    payload: WarehouseUpdate,
    service: CatalogService = Depends(get_catalog_service),
) -> WarehouseRead:
    return service.update_warehouse(warehouse_id, payload)

