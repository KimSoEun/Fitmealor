"""add identity to integer PKs

Revision ID: 8c5cecec27e8
Revises: 0ab3a5066185
Create Date: 2025-10-15 16:47:31.802139

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c5cecec27e8'
down_revision: Union[str, Sequence[str], None] = '0ab3a5066185'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
