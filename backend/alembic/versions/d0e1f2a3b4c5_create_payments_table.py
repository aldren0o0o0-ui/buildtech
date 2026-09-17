"""create payments table

Revision ID: d0e1f2a3b4c5
Revises: c9d2e3f4a5b6
Create Date: 2026-09-12 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0e1f2a3b4c5'
down_revision: Union[str, Sequence[str], None] = 'c9d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('payment_reference', sa.String(length=50), nullable=False),
        sa.Column('method', sa.String(length=50), nullable=False, server_default='CASH_ON_DELIVERY'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='PHP'),
        sa.Column('provider', sa.String(length=50), nullable=False, server_default='COD'),
        sa.Column('provider_payment_id', sa.String(length=100), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('amount >= 0', name='check_payment_amount_non_negative'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id', name='uq_payments_order_id'),
        sa.UniqueConstraint('payment_reference', name='uq_payments_payment_reference')
    )
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)
    op.create_index(op.f('ix_payments_order_id'), 'payments', ['order_id'], unique=True)
    op.create_index(op.f('ix_payments_payment_reference'), 'payments', ['payment_reference'], unique=True)
    op.create_index(op.f('ix_payments_status'), 'payments', ['status'], unique=False)
    op.create_index(op.f('ix_payments_method'), 'payments', ['method'], unique=False)
    op.create_index(op.f('ix_payments_created_at'), 'payments', ['created_at'], unique=False)

    # Backfill payment for any existing orders without a payment record
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO payments (order_id, payment_reference, method, status, amount, currency, provider, created_at, updated_at)
        SELECT 
            o.id,
            CONCAT('PAY-', TO_CHAR(COALESCE(o.created_at, NOW()), 'YYYYMMDD'), '-', LPAD(o.id::text, 6, '0')),
            COALESCE(NULLIF(o.payment_method, ''), 'CASH_ON_DELIVERY'),
            COALESCE(NULLIF(o.payment_status, ''), 'PENDING'),
            o.total_amount,
            'PHP',
            'COD',
            COALESCE(o.created_at, NOW()),
            COALESCE(o.updated_at, NOW())
        FROM orders o
        WHERE NOT EXISTS (
            SELECT 1 FROM payments p WHERE p.order_id = o.id
        )
    """))


def downgrade() -> None:
    op.drop_index(op.f('ix_payments_created_at'), table_name='payments')
    op.drop_index(op.f('ix_payments_method'), table_name='payments')
    op.drop_index(op.f('ix_payments_status'), table_name='payments')
    op.drop_index(op.f('ix_payments_payment_reference'), table_name='payments')
    op.drop_index(op.f('ix_payments_order_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_id'), table_name='payments')
    op.drop_table('payments')
