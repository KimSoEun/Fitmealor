# alembic/versions/xxxx_set_default_uuid_text_on_ids.py
from alembic import op

revision = "xxxx_set_default_uuid_text_on_ids"
down_revision = "<init_schema_revision_id>"  # 실제 init 리비전 ID로 교체
branch_labels = None
depends_on = None

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
