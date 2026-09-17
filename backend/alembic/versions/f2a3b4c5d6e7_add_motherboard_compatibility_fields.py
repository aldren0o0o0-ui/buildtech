"""add motherboard compatibility fields

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-09-12 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, Sequence[str], None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('motherboard_specifications', sa.Column('max_memory_speed_mhz', sa.Integer(), nullable=True))
    op.add_column('motherboard_specifications', sa.Column('supported_storage_interfaces', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('motherboard_specifications', 'supported_storage_interfaces')
    op.drop_column('motherboard_specifications', 'max_memory_speed_mhz')
