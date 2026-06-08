# Smart Glove Edge Firmware

Production-ready Raspberry Pi firmware for the Smart Glove hemoglobin detection system.

## Overview

This firmware runs on Raspberry Pi 3 (and other models) to:
- Capture finger images using the camera sensor
- Encrypt images using AES-256-CBC
- Upload encrypted images to the backend for processing
- Handle offline scenarios with local caching
- Accept trigger requests from the mobile app via HTTP

**Key Design Principle:** No AI model runs on the Raspberry Pi. All image processing and hemoglobin prediction happens on the backend/cloud.

## Hardware

- **Target Device:** Raspberry Pi 3 Model B1.2 (2015) or newer
- **Camera Sensor:** IMX219-200 (or compatible Pi camera)
- **Bluetooth:** Built-in BLE for provisioning
- **Storage:** microSD card with at least 8GB free space

## Installation

### 1. Set up Raspberry Pi OS

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Enable camera
sudo raspi-config
# Navigate to Interface Options -> Camera -> Enable

# Install Python 3.10+ (if not already installed)
sudo apt install python3 python3-pip python3-venv -y
```

### 2. Clone Repository

```bash
cd /opt
sudo git clone <repository-url> smart-glove-hemoglobin
cd smart-glove-hemoglobin/edge-firmware
```

### 3. Create Virtual Environment

```bash
sudo python3 -m venv venv
sudo venv/bin/pip install -r edge_firmware/requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
nano .env
# Fill in your OWNER_ID and GLOVE_API_KEY
```

### 5. Run Firmware

```bash
# Development mode (run directly)
sudo venv/bin/python -m edge_firmware.main

# Production mode (with systemd - see deploy/ directory)
sudo systemctl start smart_glove.service
```

## Configuration

All hardware variations are handled via the `.env` file:

- **Camera:** `CAMERA_INDEX`, `CAMERA_RESOLUTION`, `CAMERA_FORMAT`
- **Network:** `SERVER_HOST`, `SERVER_PORT`, `MDNS_HOSTNAME`
- **GPIO:** `ENABLE_GPIO_POWER_CONTROL`, `GPIO_CAMERA_POWER_PIN`, `GPIO_LED_POWER_PIN`
- **Cache:** `CACHE_DIR`, `MAX_CACHE_SIZE_MB`, `RETRY_MAX_ATTEMPTS`

See `.env.example` for all available options.

## API Endpoints

### POST /trigger

Triggers a scan session. Called by the mobile app.

**Request Body:**
```json
{
  "scan_id": "uuid-string",
  "owner_id": "owner-uuid",
  "patient_id": "patient-uuid",
  "is_pregnant": false,
  "capture_timestamp": 1716825600,
  "sync_timestamp": 1716825605
}
```

**Response:** `202 Accepted` if capture started successfully.

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "owner_id": "owner-uuid",
  "last_upload": "2024-06-08T12:00:00Z",
  "queue_depth": 0
}
```

## Workflow

1. Mobile app creates scan session via backend API
2. Mobile app sends POST /trigger to Raspberry Pi
3. Raspberry Pi validates owner_id and starts capture
4. Camera captures finger image
5. Image is encrypted with AES-256-CBC
6. Encrypted image + metadata uploaded to backend
7. Backend decrypts, processes, and runs AI model
8. Mobile app polls backend for result
9. Raspberry Pi powers off camera after successful upload

## Offline Support

If network is unavailable during upload:
- Encrypted image and metadata are saved to `CACHE_DIR`
- Background retry worker attempts upload with exponential backoff
- Queue is processed when network becomes available

## Testing

```bash
# Run unit tests
sudo venv/bin/pytest tests/

# Test camera capture
sudo venv/bin/python -m edge_firmware.capture

# Test encryption
sudo venv/bin/python tests/test_crypto.py
```

## Troubleshooting

### Camera not detected
```bash
# Check camera is enabled
vcgencmd get_camera

# List video devices
ls -l /dev/video*

# Try different CAMERA_INDEX in .env
```

### Upload failures
```bash
# Check backend connectivity
curl -I https://api.smartglovecloud.com/health

# Check logs
journalctl -u smart_glove.service -f
```

### Permission errors
```bash
# Ensure user has camera and GPIO permissions
sudo usermod -a -G video $USER
sudo usermod -a -G gpio $USER
```

## Development

To develop on a non-Pi machine (e.g., laptop):

```bash
# Install dependencies
pip install -r edge_firmware/requirements.txt

# Set ENABLE_MOCK_CAMERA=true in .env to simulate camera
# This allows testing without actual hardware
```

## License

Proprietary - Smart Glove Project

## Support

For issues or questions, contact the Edge Firmware Engineer.
