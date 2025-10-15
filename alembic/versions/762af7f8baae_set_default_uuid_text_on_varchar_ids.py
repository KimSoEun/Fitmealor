"""set default uuid()::text on varchar ids

Revision ID: 762af7f8baae
Revises: 8c5cecec27e8_add_identity_to_integer_pks
Create Date: 2025-10-15 17:27:38.302725

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '762af7f8baae'
down_revision: Union[str, Sequence[str], None] = '8c5cecec27e8_add_identity_to_integer_pks'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
