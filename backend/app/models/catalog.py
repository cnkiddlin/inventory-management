from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.inventory import Inventory
    from app.models.orders import InboundOrderItem, OutboundOrderItem, StockTransferItem


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("cost_price >= 0", name="ck_products_cost_price_nonnegative"),
        CheckConstraint("selling_price >= 0", name="ck_products_selling_price_nonnegative"),
        CheckConstraint("safety_stock >= 0", name="ck_products_safety_stock_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    cost_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="件", nullable=False)
    safety_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False, index=True)

    category: Mapped["Category"] = relationship(back_populates="products")
    inventory_records: Mapped[list["Inventory"]] = relationship(back_populates="product")
    inbound_items: Mapped[list["InboundOrderItem"]] = relationship(back_populates="product")
    outbound_items: Mapped[list["OutboundOrderItem"]] = relationship(back_populates="product")
    transfer_items: Mapped[list["StockTransferItem"]] = relationship(back_populates="product")


class Warehouse(TimestampMixin, Base):
    __tablename__ = "warehouses"
    __table_args__ = (
        CheckConstraint("capacity >= 0", name="ck_warehouses_capacity_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    manager_name: Mapped[str | None] = mapped_column(String(80))
    phone: Mapped[str | None] = mapped_column(String(40))
    capacity: Mapped[int] = mapped_column(Integer, default=10000, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False, index=True)

    inventory_records: Mapped[list["Inventory"]] = relationship(back_populates="warehouse")

