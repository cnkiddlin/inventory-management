from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InventoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    sku: str
    product_name: str
    category_name: str
    warehouse_id: int
    warehouse_code: str
    warehouse_name: str
    unit: str
    quantity: int
    reserved_quantity: int
    available_quantity: int
    safety_stock: int
    status: str
    updated_at: datetime


class InventoryAlertRead(BaseModel):
    product_id: int
    sku: str
    product_name: str
    category_name: str
    unit: str
    current_stock: int
    safety_stock: int
    shortage: int
    suggested_replenishment: int
    status: str
    warehouse_count: int
    warehouse_stock: list[dict[str, int | str]] = Field(default_factory=list)


class InventoryTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_no: str
    product_id: int
    sku: str
    product_name: str
    warehouse_id: int
    warehouse_name: str
    transaction_type: str
    quantity_change: int
    balance_after: int
    reference_type: str | None
    reference_id: int | None
    reference_no: str | None
    notes: str | None
    created_at: datetime

