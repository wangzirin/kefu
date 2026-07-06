from collections.abc import Generator
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app


_ENV_KEYS_TO_RESTORE = (
    "BAILIAN_API_BASE",
    "BAILIAN_API_KEY",
    "BAILIAN_MODEL",
    "BAILIAN_FAST_MODEL",
    "BAILIAN_STANDARD_MODEL",
    "BAILIAN_PREMIUM_MODEL",
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_MODEL",
    "DEEPSEEK_FALLBACK_MODEL",
    "MODEL_PRICE_BAILIAN_FAST_PER_1K_UNITS",
    "MODEL_PRICE_BAILIAN_STANDARD_PER_1K_UNITS",
    "MODEL_PRICE_BAILIAN_PREMIUM_PER_1K_UNITS",
    "MODEL_BUDGET_SINGLE_CALL_LIMIT_CNY",
    "KNOWLEDGE_EMBEDDING_PROVIDER",
    "KNOWLEDGE_EMBEDDING_API_BASE",
    "KNOWLEDGE_EMBEDDING_API_KEY",
    "KNOWLEDGE_EMBEDDING_MODEL",
    "KNOWLEDGE_VECTOR_STORE",
    "STANDARD_OPS_ENV",
    "STANDARD_OPS_DEV_BOOTSTRAP_ENABLED",
    "OUTBOX_EXTERNAL_WRITE_ENABLED",
    "TRUSTED_INBOUND_WORKER_ENABLED",
)


@pytest.fixture(autouse=True)
def restore_config_environment() -> Generator[None, None, None]:
    snapshot = {key: os.environ.get(key) for key in _ENV_KEYS_TO_RESTORE}
    try:
        yield
    finally:
        for key, value in snapshot.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session: Session):
    app = create_app()

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


from fastapi.testclient import TestClient  # noqa: E402
