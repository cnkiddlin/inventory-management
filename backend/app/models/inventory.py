from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.catalog import Product, Warehouse


class Inventory(TimestampMixin, Base):
    __tablename__ = "inventory"
    __table_args__ = (
        UniqueConstraint("product_id", "warehouse_id", name="uq_inventory_product_warehouse"),
        CheckConstraint("quantity >= 0", name="ck_inventory_quantity_nonnegative"),
        CheckConstraint("reserved_quantity >= 0", name="ck_inventory_reserved_nonnegative"),
        CheckConstraint(
            "reserved_quantity <= quantity", name="ck_inventory_reserved_lte_quantity"
        ),
        Index("ix_inventory_warehouse_product", "warehouse_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="inventory_records")
    warehouse: Mapped["Warehouse"] = relationship(back_populates="inventory_records")

    @property
    def available_quantity(self) -> int:
        return self.quantity - self.reserved_quantity


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    __table_args__ = (
        CheckConstraint("quantity_change <> 0", name="ck_transactions_quantity_change_nonzero"),
        CheckConstraint("balance_after >= 0", name="ck_transactions_balance_nonnegative"),
        Index("ix_transactions_product_warehouse_created", "product_id", "warehouse_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    transaction_no: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    quantity_change: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(40), index=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, index=True)
    reference_no: Mapped[str | None] = mapped_column(String(60), index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    product: Mapped["Product"] = relationship()
    warehouse: Mapped["Warehouse"] = relationship()

