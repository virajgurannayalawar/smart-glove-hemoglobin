import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import json

@patch("app.api.routes.upload.decrypt_image_payload")
@patch("app.api.routes.upload.storage_service.upload_file")
@patch("app.api.routes.upload.get_database")
def test_upload_reading(mock_get_db, mock_upload, mock_decrypt, client):
    # Setup mocks
    mock_decrypt.return_value = b"decrypted_image_bytes"
    mock_upload.return_value = "fake_cloudinary_id"
    
    mock_db = MagicMock()
    mock_db.history.insert_one = AsyncMock()
    mock_get_db.return_value = mock_db
    
    # Create valid metadata
    metadata = {
        "hemoglobin_level": 14.5,
        "capture_timestamp": 10000,
        "sync_timestamp": 10050 # 50 second offset
    }
    
    # Send multipart/form-data
    response = client.post(
        "/api/v1/upload/",
        data={"metadata": json.dumps(metadata)},
        files={"image": ("test.jpg", b"encrypted_fake_bytes", "image/jpeg")}
    )
    
    assert response.status_code == 200
    json_resp = response.json()
    assert "message" in json_resp
    assert json_resp["message"] == "Upload successful"
    assert "true_timestamp" in json_resp
    
    # Verify our mocks were called
    mock_decrypt.assert_called_once()
    mock_upload.assert_called_once()
    mock_db.history.insert_one.assert_called_once()
