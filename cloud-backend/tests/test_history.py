import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone

@patch("app.api.routes.history.get_database")
@patch("app.api.routes.history.storage_service.generate_signed_url")
def test_get_history(mock_generate_url, mock_get_db, client):
    # Setup mocks
    mock_generate_url.return_value = "http://fake-cloudinary.com/image.jpg"
    
    # Mock MongoDB cursor logic
    mock_cursor = MagicMock()
    
    # Create a mock asynchronous iterator for the cursor
    async def mock_aiter(*args, **kwargs):
        yield {
            "_id": "60d5ec49c5e31c2d4c8b4567",
            "patient_id": "test-patient-123",
            "true_timestamp": datetime.now(timezone.utc),
            "hemoglobin_level": 14.5,
            "s3_image_key": "fake_public_id"
        }
        
    mock_cursor.__aiter__ = mock_aiter
    mock_cursor.sort.return_value = mock_cursor
    
    mock_db = MagicMock()
    mock_db.history.find.return_value = mock_cursor
    mock_get_db.return_value = mock_db
    
    # Execute request
    response = client.get("/api/v1/history/")
    
    # Assertions
    assert response.status_code == 200
    json_resp = response.json()
    assert isinstance(json_resp, list)
    assert len(json_resp) == 1
    assert json_resp[0]["hemoglobin_level"] == 14.5
    assert json_resp[0]["image_url"] == "http://fake-cloudinary.com/image.jpg"
