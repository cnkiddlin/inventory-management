"""add product model

Revision ID: c2d4e6f8a901
Revises: a7bc73547c26
Create Date: 2026-10-22 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2d4e6f8a901"
down_revision: Union[str, None] = "a7bc73547c26"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("model", sa.String(length=80), server_default="", nullable=False),
    )
    op.create_index(op.f("ix_products_model"), "products", ["model"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_products_model"), table_name="products")
    op.drop_column("products", "model")
