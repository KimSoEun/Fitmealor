import os, sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# (선택) .env 로드
from dotenv import load_dotenv
load_dotenv()

config = context.config

# ─────────────────────────────────────────────────────────
# ① 프로젝트 루트를 import 경로에 추가 (alembic/에서 import 안정화)
#    env.py가 /<project>/alembic/env.py 라고 가정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ② Base는 직접 경로로 import (순환 import 방지)
from db.core import Base   # ← 실제 경로에 맞게
# ③ 모델 모듈들을 "사이드 임포트" 해서 Base.metadata에 등록
#    (파일명에 맞춰 추가)
#import models.user
#import models.meal
#import models.recommendation
# import models.other_models ...
# ─────────────────────────────────────────────────────────

# ★ 모델 자동 임포트: models 패키지 하위 .py / 서브패키지 전부 로드
import importlib, pkgutil, models
def import_all_models():
    for _, module_name, ispkg in pkgutil.walk_packages(models.__path__, models.__name__ + "."):
        # 필요하다면 특정 모듈 제외 로직 추가 가능
        importlib.import_module(module_name)
import_all_models()

def resolve_url() -> str:
    """우선순위: -x 인자 > 환경변수 > alembic.ini"""
    # 1) `alembic -x "sqlalchemy.url=..."` 로 넘어온 값
    xargs = context.get_x_argument(as_dictionary=True)
    x_url = xargs.get("sqlalchemy.url") or xargs.get("dburl")
    if x_url:
        return x_url

    # 2) 환경변수
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url

    # 3) alembic.ini (fallback)
    return config.get_main_option("sqlalchemy.url")

# logging 설정
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """'offline' 모드"""
#    url = resolve_url()  # ← 반드시 resolve_url() 사용
    url = config.get_main_option("sqlalchemy.url")  # ✅ conftest에서 주입한 URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """'online' 모드"""
    # engine_from_config가 ini에서 url을 읽으므로 먼저 주입!
#    url = resolve_url()
#    config.set_main_option("sqlalchemy.url", url)

    # ✅ ini/config의 sqlalchemy.url을 그대로 사용 (conftest가 덮어쓴 값)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
