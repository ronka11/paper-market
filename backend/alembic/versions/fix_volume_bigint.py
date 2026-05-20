"""Fix volume column to BigInteger

Revision ID: fix_volume_bigint
Revises: 94af4d98dbc1
Create Date: 2026-05-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fix_volume_bigint'
down_revision: Union[str, Sequence[str], None] = '94af4d98dbc1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('stock_prices', 'volume',
               existing_type=sa.Integer(),
               type_=sa.BigInteger(),
               existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('stock_prices', 'volume',
               existing_type=sa.BigInteger(),
               type_=sa.Integer(),
               existing_nullable=True)
