from datetime import datetime

from pydantic import BaseModel

from app.schemas.inventory import InventoryAlertRead, InventoryTransactionRead


class DashboardSummary(BaseModel):
    total_units: int
    total_sku: int
    inventory_value: float
    low_stock_count: int
    out_of_stock_count: int
    warehouse_count: int


class TrendPoint(BaseModel):
    date: str
    inbound_quantity: int
    outbound_quantity: int
    net_change: int


class CategoryDistribution(BaseModel):
    category_id: int
    category_name: str
    units: int
    value: float
    product_count: int


class DashboardRead(BaseModel):
    generated_at: datetime
    summary: DashboardSummary
    trend: list[TrendPoint]
    category_distribution: list[CategoryDistribution]
    low_stock: list[InventoryAlertRead]
    recent_transactions: list[InventoryTransactionRead]

