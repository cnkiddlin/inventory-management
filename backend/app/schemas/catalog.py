from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return value.strip()


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=1000)


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    product_count: int = 0
    created_at: datetime


class ProductBase(BaseModel):
    sku: str = Field(min_length=2, max_length=60)
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    category_id: int = Field(gt=0)
    cost_price: float = Field(ge=0)
    selling_price: float = Field(ge=0)
    unit: str = Field(default="件", min_length=1, max_length=20)
    safety_stock: int = Field(default=0, ge=0)
    status: str = Field(default="ACTIVE", pattern="^(ACTIVE|INACTIVE)$")

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, value: str) -> str:
        return value.strip().upper()


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=2, max_length=60)
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    category_id: int | None = Field(default=None, gt=0)
    cost_price: float | None = Field(default=None, ge=0)
    selling_price: float | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    safety_stock: int | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, pattern="^(ACTIVE|INACTIVE)$")

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else value


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    description: str | None
    category_id: int
    category_name: str
    cost_price: float
    selling_price: float
    unit: str
    safety_stock: int
    status: str
    current_stock: int = 0
    inventory_value: float = 0
    created_at: datetime
    updated_at: datetime


class WarehouseCreate(BaseModel):
    code: str = Field(min_length=2, max_length=30)
    name: str = Field(min_length=2, max_length=120)
    location: str = Field(min_length=2, max_length=200)
    manager_name: str | None = Field(default=None, max_length=80)
    phone: str | None = Field(default=None, max_length=40)
    capacity: int = Field(default=10000, ge=0)
    status: str = Field(default="ACTIVE", pattern="^(ACTIVE|INACTIVE)$")

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()


class WarehouseUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=2, max_length=30)
    name: str | None = Field(default=None, min_length=2, max_length=120)
    location: str | None = Field(default=None, min_length=2, max_length=200)
    manager_name: str | None = Field(default=None, max_length=80)
    phone: str | None = Field(default=None, max_length=40)
    capacity: int | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, pattern="^(ACTIVE|INACTIVE)$")


class WarehouseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    location: str
    manager_name: str | None
    phone: str | None
    capacity: int
    status: str
    sku_count: int = 0
    total_units: int = 0
    total_value: float = 0
    utilization_percent: float = 0
    created_at: datetime

