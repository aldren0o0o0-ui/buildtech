"""add shipping_barangay notes and cancelled_at to orders

Revision ID: c9d2e3f4a5b6
Revises: b8f1c2d3e4a5
Create Date: 2026-09-11 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = 'b8f1c2d3e4a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('shipping_barangay', sa.String(length=100), nullable=True))
    op.add_column('orders', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('orders', sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('orders', 'cancelled_at')
    op.drop_column('orders', 'notes')
    op.drop_column('orders', 'shipping_barangay')
