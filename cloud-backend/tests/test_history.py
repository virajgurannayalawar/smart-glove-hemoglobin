import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone

@patch("app.api.routes.history.get_database")
def test_get_history(mock_get_db, client):
    # Mock MongoDB cursor logic
    mock_cursor = MagicMock()
    
    # Create a mock asynchronous iterator for the cursor
    async def mock_aiter(*args, **kwargs):
        yield {
            "_id": "60d5ec49c5e31c2d4c8b4567",
            "PatientId": "test-patient-123",
            "TrueTimestamp": datetime.now(timezone.utc),
            "HemoglobinLevel": 14.5,
            "ImageUrl": "http://fake-cloudinary.com/image.jpg",
            "OwnerId": "test-owner",
            "IsPregnant": False,
            "IsAnemic": False,
            "StatusText": "Normal",
            "ReadingId": "reading-123"
        }
        
    mock_cursor.__aiter__ = mock_aiter
    mock_cursor.sort.return_value = mock_cursor
    
    mock_db = MagicMock()
    mock_db.hemoglobin_readings.find.return_value = mock_cursor
    mock_get_db.return_value = mock_db
    
    # Execute request
    response = client.get("/api/v1/history/")
    
    # Assertions
    assert response.status_code == 200
    json_resp = response.json()
    assert isinstance(json_resp, list)
    assert len(json_resp) == 1
    assert json_resp[0]["hemoglobinLevel"] == 14.5
    assert json_resp[0]["imageUrl"] == "http://fake-cloudinary.com/image.jpg"
