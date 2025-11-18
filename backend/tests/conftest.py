from pathlib import Path
import os, pytest, sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from alembic.config import Config
from alembic import command
from fastapi.testclient import TestClient

# Add the fastapi-service directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "fastapi-service"))

from app.main import app
from app.db.database import get_db

TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql+psycopg://fitmealor:fitmealor@localhost:5432/fitmealor_test")

@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    # alembic.ini의 절대경로 지정 (pytest 실행 위치가 달라도 안전)
#    ini_path = Path(__file__).parent.parent / "alembic.ini"
#    cfg = Config(str(ini_path))
    # ✅ ini 파일을 아예 안 읽고, 필요한 옵션만 직접 세팅
    cfg = Config()
    cfg.set_main_option("script_location", str(Path(__file__).parent.parent / "alembic"))
    # 테스트 DB로 덮어쓰기
    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)

    # (선택) 디버깅: Alembic이 어떤 URL로 붙는지 눈으로 확인
    print("ALEMBIC URL =", cfg.get_main_option("sqlalchemy.url"))

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

@pytest.fixture()
def client(db_session):
    """
    FastAPI TestClient with database session override
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture()
def test_user_data():
    """
    Test user data for registration and authentication tests
    """
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "Test123456!",
        "full_name": "Test User"
    }

@pytest.fixture()
def test_health_profile_data():
    """
    Test health profile data
    """
    return {
        "age": 30,
        "gender": "male",
        "height_cm": 175,
        "weight_kg": 70,
        "target_weight_kg": 68,
        "activity_level": "moderately_active",
        "health_goal": "weight_loss"
    }

