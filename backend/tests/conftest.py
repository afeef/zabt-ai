# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
import pytest
from typing import Generator, Dict
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from app.main import app
from app.db.engine import engine
from app.api.deps import get_db, get_current_user
from app.models import User

@pytest.fixture(scope="session", autouse=True)
def db_engine():
    # Use the existing engine
    return engine

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    # Create a new session for each test
    with Session(engine) as session:
        yield session

@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function", autouse=True)
def create_test_user(db: Session):
    from sqlalchemy import text
    from app.models import User
    user = db.get(User, 1)
    if not user:
        user = User(id=1, email="test@example.com", supabase_id="mock_supabase_uuid", full_name="Test User")
        db.add(user)
        db.commit()
    # The user above is inserted with an explicit id=1, which does NOT advance the
    # Postgres identity sequence. Keep the sequence ahead of the max id so tests that
    # create users via autoincrement don't collide on the primary key.
    db.execute(
        text(
            "SELECT setval(pg_get_serial_sequence('\"user\"', 'id'), "
            "(SELECT COALESCE(MAX(id), 1) FROM \"user\"))"
        )
    )
    db.commit()

@pytest.fixture(scope="function")
def normal_user_token_headers(client: TestClient, db: Session) -> Dict[str, str]:
    return {"Authorization": "Bearer mock_token"}

@pytest.fixture(scope="module", autouse=True)
def override_auth_deps():
    from app.api.deps import get_current_user
    from app.models import User

    async def mock_get_current_user() -> User:
        return User(id=1, email="test@example.com", supabase_id="mock_supabase_uuid", full_name="Test User")

    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides = {}
