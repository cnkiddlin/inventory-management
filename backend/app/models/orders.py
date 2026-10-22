from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.catalog import Product, Warehouse


class InboundOrder(TimestampMixin, Base):
    __tablename__ = "inbound_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_no: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    supplier: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(80), default="system", nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    warehouse: Mapped["Warehouse"] = relationship()
    items: Mapped[list["InboundOrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="InboundOrderItem.id"
    )


class InboundOrderItem(Base):
    __tablename__ = "inbound_order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inbound_items_quantity_positive"),
        CheckConstraint("unit_cost >= 0", name="ck_inbound_items_cost_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("inbound_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    order: Mapped["InboundOrder"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


class OutboundOrder(TimestampMixin, Base):
    __tablename__ = "outbound_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_no: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(80), default="system", nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    warehouse: Mapped["Warehouse"] = relationship()
    items: Mapped[list["OutboundOrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="OutboundOrderItem.id"
    )


class OutboundOrderItem(Base):
    __tablename__ = "outbound_order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_outbound_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_outbound_items_price_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("outbound_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    order: Mapped["OutboundOrder"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


class StockTransfer(TimestampMixin, Base):
    __tablename__ = "stock_transfers"
    __table_args__ = (
        CheckConstraint(
            "from_warehouse_id <> to_warehouse_id", name="ck_transfer_distinct_warehouses"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transfer_no: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    from_warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    to_warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(80), default="system", nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    from_warehouse: Mapped["Warehouse"] = relationship(foreign_keys=[from_warehouse_id])
    to_warehouse: Mapped["Warehouse"] = relationship(foreign_keys=[to_warehouse_id])
    items: Mapped[list["StockTransferItem"]] = relationship(
        back_populates="transfer", cascade="all, delete-orphan", order_by="StockTransferItem.id"
    )


class StockTransferItem(Base):
    __tablename__ = "stock_transfer_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_transfer_items_quantity_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transfer_id: Mapped[int] = mapped_column(
        ForeignKey("stock_transfers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    transfer: Mapped["StockTransfer"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()

