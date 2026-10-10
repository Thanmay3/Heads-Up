import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import create_app
from app.models import Base


@pytest.fixture()
def engine():
    """In-memory SQLite shared across connections for the duration of one test."""
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture()
def db_session(engine) -> Session:
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = factory()
    yield session
    session.close()


@pytest.fixture()
def client(engine, db_session) -> TestClient:
    app = create_app()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def isolated_materials_dir(tmp_path, monkeypatch):
    """Keep uploaded material files out of the repo's ./data directory."""
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "materials_dir", str(tmp_path / "materials"))


@pytest.fixture()
def course(client) -> dict:
    response = client.post("/api/v1/courses", json={"name": "Computer Networks"})
    assert response.status_code == 201
    return response.json()
