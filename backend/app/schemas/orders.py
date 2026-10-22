from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=1_000_000)


class InboundItemCreate(OrderItemCreate):
    unit_cost: float | None = Field(default=None, ge=0)


class OutboundItemCreate(OrderItemCreate):
    unit_price: float | None = Field(default=None, ge=0)


class InboundOrderCreate(BaseModel):
    warehouse_id: int = Field(gt=0)
    supplier: str = Field(min_length=2, max_length=160)
    notes: str | None = Field(default=None, max_length=1000)
    created_by: str = Field(default="web-user", max_length=80)
    items: list[InboundItemCreate] = Field(min_length=1)

    @field_validator("supplier")
    @classmethod
    def clean_supplier(cls, value: str) -> str:
        return value.strip()


class OutboundOrderCreate(BaseModel):
    warehouse_id: int = Field(gt=0)
    customer: str = Field(min_length=2, max_length=160)
    notes: str | None = Field(default=None, max_length=1000)
    created_by: str = Field(default="web-user", max_length=80)
    items: list[OutboundItemCreate] = Field(min_length=1)

    @field_validator("customer")
    @classmethod
    def clean_customer(cls, value: str) -> str:
        return value.strip()


class TransferItemCreate(OrderItemCreate):
    pass


class StockTransferCreate(BaseModel):
    from_warehouse_id: int = Field(gt=0)
    to_warehouse_id: int = Field(gt=0)
    notes: str | None = Field(default=None, max_length=1000)
    created_by: str = Field(default="web-user", max_length=80)
    items: list[TransferItemCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_warehouses(self) -> "StockTransferCreate":
        if self.from_warehouse_id == self.to_warehouse_id:
            raise ValueError("调出仓库和调入仓库不能相同")
        return self


class InboundItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    sku: str
    product_name: str
    unit: str
    quantity: int
    unit_cost: float
    line_total: float


class OutboundItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    sku: str
    product_name: str
    unit: str
    quantity: int
    unit_price: float
    line_total: float


class TransferItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    sku: str
    product_name: str
    unit: str
    quantity: int


class InboundOrderRead(BaseModel):
    id: int
    order_no: str
    warehouse_id: int
    warehouse_name: str
    supplier: str
    status: str
    notes: str | None
    created_by: str
    confirmed_at: datetime | None
    created_at: datetime
    item_count: int
    total_quantity: int
    total_value: float
    items: list[InboundItemRead]


class OutboundOrderRead(BaseModel):
    id: int
    order_no: str
    warehouse_id: int
    warehouse_name: str
    customer: str
    status: str
    notes: str | None
    created_by: str
    confirmed_at: datetime | None
    created_at: datetime
    item_count: int
    total_quantity: int
    total_value: float
    items: list[OutboundItemRead]


class StockTransferRead(BaseModel):
    id: int
    transfer_no: str
    from_warehouse_id: int
    from_warehouse_name: str
    to_warehouse_id: int
    to_warehouse_name: str
    status: str
    notes: str | None
    created_by: str
    completed_at: datetime | None
    created_at: datetime
    item_count: int
    total_quantity: int
    items: list[TransferItemRead]

