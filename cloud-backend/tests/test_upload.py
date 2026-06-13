import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import json

@patch("app.api.routes.upload.preprocess_for_model")
@patch("app.api.routes.upload.decrypt_image_payload")
@patch("app.api.routes.upload.storage_service.upload_file")
@patch("app.api.routes.upload.get_database")
def test_upload_reading(mock_get_db, mock_upload, mock_decrypt, mock_preprocess, client):
    # Setup mocks
    mock_decrypt.return_value = b"decrypted_image_bytes"
    mock_upload.return_value = "fake_cloudinary_id"
    mock_preprocess.return_value = (b"processed_bytes", "png")
    
    mock_db = MagicMock()
    mock_db.patients.find_one = AsyncMock(return_value={
        "PatientId": "test-patient-123",
        "OwnerId": "test-owner-123",
        "Age": 25,
        "Gender": "female"
    })
    mock_db.hemoglobin_readings.insert_one = AsyncMock()
    mock_get_db.return_value = mock_db
    
    # Create valid metadata conforming to UploadMetadata schema
    metadata = {
        "HemoglobinLevel": 14.5,
        "CaptureTimestamp": 10000,
        "SyncTimestamp": 10050,  # 50 second offset
        "PatientId": "test-patient-123",
        "IsPregnant": False
    }
    
    # Send multipart/form-data
    response = client.post(
        "/api/v1/upload/",
        data={"metadata": json.dumps(metadata)},
        files={"image": ("test.jpg", b"encrypted_fake_bytes", "image/jpeg")}
    )
    
    print("RESPONSE STATUS:", response.status_code)
    print("RESPONSE BODY:", response.json())
    
    assert response.status_code == 200
    json_resp = response.json()
    assert "message" in json_resp
    assert json_resp["message"] == "Upload successful"
    assert "true_timestamp" in json_resp
    
    # Verify our mocks were called
    mock_decrypt.assert_called_once()
    mock_upload.assert_called_once()
    mock_preprocess.assert_called_once()
    mock_db.patients.find_one.assert_called_once_with({"PatientId": "test-patient-123"})
    mock_db.hemoglobin_readings.insert_one.assert_called_once()
