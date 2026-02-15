"""Test fixtures and configuration."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add project root to path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.app.main import app
from backend.app.database import get_db
from backend.app.models import Base, User
from backend.app.api.auth import hash_password, create_access_token

# Use in-memory SQLite with StaticPool so same connection is reused
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _override_get_db():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


# Override get_db globally for all tests
app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture
def db_session():
    """Provide a database session for tests."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """Create a test client."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def test_user(db_session):
    """Create a test user and return it."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("testpassword"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Return authorization headers for the test user."""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}
