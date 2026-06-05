import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.dependencies import get_current_active_user
from unittest.mock import AsyncMock, MagicMock

# Mock current user dependency
def override_get_current_active_user():
    return {
        "patient_id": "test-patient-123",
        "email": "test@example.com",
        "name": "Test User",
        "is_active": True
    }

app.dependency_overrides[get_current_active_user] = override_get_current_active_user

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
