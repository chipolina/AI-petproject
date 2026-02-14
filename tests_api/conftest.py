import pytest
from fastapi.testclient import TestClient

from app.backend.main import app


@pytest.fixture(scope="session")
def client():
    return TestClient(app)
