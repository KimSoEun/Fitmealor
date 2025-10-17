"""seed master tables

Revision ID: a998657863ca
Revises: 762af7f8baae
Create Date: 2025-10-17 14:14:45.506942

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a998657863ca'
down_revision: Union[str, Sequence[str], None] = '762af7f8baae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 안전장치
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # cuisine_tag (code + display_name)
    op.execute(sa.text("""
    INSERT INTO cuisine_tag(code, display_name) VALUES
      ('KR','Korean'),
      ('JP','Japanese'),
      ('US','American'),
      ('IT','Italian')
    ON CONFLICT (code) DO NOTHING;
    """))
    
    # allergen (code + name_en)
    op.execute(sa.text("""
    INSERT INTO allergen(code, name_en) VALUES
      ('EGG','Egg'),
      ('MLK','Milk'),
      ('NUT','Tree Nuts'),
      ('PNT','Peanut'),
      ('SOY','Soy'),
      ('WHT','Wheat'),
      ('FSH','Fish'),
      ('SHF','Shellfish')
    ON CONFLICT (code) DO NOTHING;
    """))

def downgrade() -> None:
    """Downgrade schema."""
    op.execute(sa.text("DELETE FROM cuisine_tag WHERE code IN ('KR','JP','US','IT');"))
    op.execute(sa.text("DELETE FROM allergen WHERE code IN ('EGG','MLK','NUT','PNT','SOY','WHT','FSH','SHF');"))
