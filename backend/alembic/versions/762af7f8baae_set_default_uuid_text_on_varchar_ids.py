# alembic/versions/xxxx_set_default_uuid_text_on_ids.py
from alembic import op

from typing import Union, Sequence

revision = "762af7f8baae"
down_revision: Union[str, Sequence[str], None] = "0ab3a5066185" # revision 직렬화
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = [
    "algo_feature_snapshot",
    "image_asset",
    "ingredient",
    "meal",
    "meal_i18n",
    "rating_feedback",
    "recommendation_item",
    "recommendation_session",
    "user_account",
    "user_health_measure",
    "user_interaction",
    "user_preference",
    "user_profile",
]

def upgrade():
    # gen_random_uuid() 쓰려면 pgcrypto 확장 필요
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    for t in TABLES:
        op.execute(
            f"ALTER TABLE {t} ALTER COLUMN id SET DEFAULT gen_random_uuid()::text;"
        )

def downgrade():
    for t in TABLES:
        op.execute(
            f"ALTER TABLE {t} ALTER COLUMN id DROP DEFAULT;"
        )
