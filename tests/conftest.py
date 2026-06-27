# File: tests/conftest.py
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_safetx.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("EMAIL_ALERTS_ENABLED", "false")
os.environ.setdefault("WEBHOOK_ALERTS_ENABLED", "false")

import pytest
from fastapi.testclient import TestClient

from backend.database import Base, engine
from backend.main import app


@pytest.fixture(autouse=True)
def _clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    client.post(
        "/register",
        json={"username": "alice", "email": "alice@example.com", "password": "s3nha-forte"},
    )
    resp = client.post(
        "/token",
        data={"username": "alice", "password": "s3nha-forte"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
