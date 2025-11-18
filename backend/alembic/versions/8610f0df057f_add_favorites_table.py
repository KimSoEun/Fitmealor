"""add_favorites_table

Revision ID: 8610f0df057f
Revises: a998657863ca
Create Date: 2025-11-18 17:24:45.493876

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8610f0df057f'
down_revision: Union[str, Sequence[str], None] = 'a998657863ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'favorites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('meal_code', sa.String(), nullable=False),
        sa.Column('meal_name_ko', sa.String(), nullable=False),
        sa.Column('meal_name_en', sa.String(), nullable=True),
        sa.Column('calories', sa.Integer(), nullable=True),
        sa.Column('carbohydrates', sa.Integer(), nullable=True),
        sa.Column('protein', sa.Integer(), nullable=True),
        sa.Column('fat', sa.Integer(), nullable=True),
        sa.Column('sodium', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'meal_code', name='unique_user_meal_favorite')
    )
    op.create_index(op.f('ix_favorites_id'), 'favorites', ['id'], unique=False)
    op.create_index(op.f('ix_favorites_user_id'), 'favorites', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_favorites_user_id'), table_name='favorites')
    op.drop_index(op.f('ix_favorites_id'), table_name='favorites')
    op.drop_table('favorites')
