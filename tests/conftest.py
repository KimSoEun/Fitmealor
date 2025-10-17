from pathlib import Path
import os, pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command

TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql+psycopg://fitmealor:fitmealor@localhost:5432/fitmealor_test")

@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    # alembic.ini의 절대경로 지정 (pytest 실행 위치가 달라도 안전)
    ini_path = Path(__file__).parent.parent / "alembic.ini"
    cfg = Config(str(ini_path))

    # 테스트 DB로 덮어쓰기
    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)
    command.upgrade(cfg, "head")
    yield
    command.downgrade(cfg, "base")

@pytest.fixture()
def db_session():
    engine = create_engine(TEST_DB_URL, future=True, pool_pre_ping=True)
    conn = engine.connect()
    trans = conn.begin()
    Session = sessionmaker(bind=conn, autoflush=False, autocommit=False, future=True)
    s = Session()
    try:
        yield s
    finally:
        s.close()
        trans.rollback()
        conn.close()
        engine.dispose()

