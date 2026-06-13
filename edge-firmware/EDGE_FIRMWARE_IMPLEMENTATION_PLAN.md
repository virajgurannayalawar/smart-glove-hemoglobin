# Edge Firmware Implementation Plan — Production-ready Raspberry Pi 3

**Objective**

Provide a detailed, production-ready implementation plan for the edge firmware (Raspberry Pi 3) aligned with the new backend workflow: backend-driven session activation, AES-256 encrypted image uploads with `X-Glove-Key` authorization, local HTTP trigger from the mobile app, and cloud processing of images. This plan converts the existing dummy code into a hardened, deployable Pi 3 firmware stack.

**Summary of current repo files (read before starting)**
- [edge-firmware/smart-glove-hemoglobin/capture.py](edge-firmware/smart-glove-hemoglobin/capture.py#L1) — simulated capture & caching logic
- [edge-firmware/smart-glove-hemoglobin/cloud_api_client.py](edge-firmware/smart-glove-hemoglobin/cloud_api_client.py#L1) — simulated secure upload
- [edge-firmware/smart-glove-hemoglobin/bluetooth_gatt_server.py](edge-firmware/smart-glove-hemoglobin/bluetooth_gatt_server.py#L1) — simulated BLE GATT server
- [edge-firmware/smart-glove-hemoglobin/operated.py](edge-firmware/smart-glove-hemoglobin/operated.py#L1) — capture + analysis simulation
- [edge-firmware/CURRENT_STATUS_and_implementation.md](edge-firmware/CURRENT_STATUS_and_implementation.md#L1)

High-level goals
- Conform the Pi firmware to the new backend contract:
  - Provision via BLE: app writes `owner_id` + `glove_api_key` and optional config.
  - Pi exposes a local HTTP endpoint (mDNS/hostname) that the mobile app can POST a `trigger` request to for a given `scan_id` and `owner_id`.
  - Pi captures an image, AES-256 encrypts the payload (IV + ciphertext), and uploads to backend `POST /api/scan/sessions/{scan_id}/upload` with header `X-Glove-Key: <glove_api_key>` and `metadata` form field.
  - After upload confirm 200 OK to app, then power-cycle camera and LEDs until next trigger.
  - Provide robust offline handling: local caching to disk with secure metadata, retries, and telemetry.

Assumptions
- Backend APIs follow `cloud-backend` implementation and contract (see `scan.py`): session creation, `upload` endpoint expects encrypted image and `GloveUploadMetadata` JSON form field.
- Mobile app will provision the Pi over BLE and will trigger the Pi using the mDNS hostname `glove-<OWNERID>.local` or IP.
- Raspberry Pi 3 runs Raspberry Pi OS with Python 3.10+ available (adjust if older).

Component breakdown
- Provisioning (BLE): accept owner_id, glove_api_key, wifi credentials.
- Device Network Manager: connect to local Wi‑Fi (wpa_supplicant) and enable mDNS (avahi) advertising of `glove-OWNERID.local`.
- Local HTTP trigger: lightweight Flask/FastAPI server bound to localhost and 0.0.0.0 (for LAN access) with a small trigger route.
- Capture module: Picamera2 (preferred on modern Pi OS) with fallback to simulated capture if missing.
- Encrypt & upload: AES-256-CBC encryption using the same padding scheme expected by backend and HTTPS POST to backend with form multipart including `metadata` and file.
- Cache & retry: atomic disk writes to `microSD` with metadata and background uploader.
- Power & safety: GPIO control to switch camera/LED power off after upload and on for capture.
- Observability: structured logs, local status API, health check endpoint, and optional Prometheus metrics exporter.

Detailed implementation plan (step-by-step)

1) Project layout & packaging
- Create a Python package `edge_firmware` with modules:
  - `provisioning.py` — BLE provisioning handlers (write/confirm) and local storage of credentials.
  - `network.py` — Wi‑Fi connection manager (use `nmcli` or edit `wpa_supplicant.conf`) + mDNS registration (Avahi/pydbus).
  - `server.py` — minimal FastAPI server with endpoints: `/health`, `/trigger` (POST) and `/status`.
  - `capture.py` — camera capture, image format control, EXIF remove/strip, and file temporary storage.
  - `crypto.py` — AES-256-CBC encrypt/decrypt helpers compatible with backend `decrypt_image_payload`.
  - `uploader.py` — upload logic: builds `GloveUploadMetadata` payload, multipart upload, `X-Glove-Key` header, handles responses and returns status.
  - `cache.py` — disk-based queue and retry worker.
  - `power.py` — optional GPIO wrapper to control camera/LED power.
  - `main.py` — supervisor process: starts server, cache worker, and monitors health.
- Add `requirements.txt` with pinned deps: `fastapi`, `uvicorn[standard]`, `requests`, `cryptography`, `picamera2` (if supported), `pyjwt` (if needed), `python-dotenv`, and optionally `dbus-next`/`pydbus` & `bluezero`/`bleak` for provisioning.

2) Provisioning over BLE (production-ready)
- Choose BLE stack that supports peripheral write from mobile: for Pi, use BlueZ + a Python wrapper capable of GATT server (e.g., `dbus`-based server) or `bluezero`. If BLE GATT server proves brittle, provide temporary AP provisioning fallback (mobile creates hotspot, Pi connects, app posts provisioning payload).
- Implement `provisioning.py` to accept a JSON payload with: `{owner_id, glove_api_key, wifi_ssid, wifi_password, optional: backend_base_url}`.
- Persist credentials to disk in `/etc/smart_glove/config.json` with restrictive permissions (600). Rotate keys: support re-provisioning endpoint or BLE re-write.

3) Network & mDNS setup
- After provisioning, `network.py` should bring up Wi‑Fi using NetworkManager (`nmcli`) or `wpa_cli` for reliability. Wait for IP, then ensure Avahi is running and publish `glove-<OWNERID>.local` (service type `_http._tcp` on port used by server).
- Provide fallback: if Wi‑Fi fails, maintain AP mode for local provisioning/debugging.

4) Local HTTP trigger and handshake
- Implement `POST /trigger` payload: `{ "scan_id": "...", "owner_id": "...", "patient_id": "...", "is_pregnant": bool, "capture_timestamp": unix_ms, "sync_timestamp": unix_ms }`.
- Validate `owner_id` equals provisioned owner; otherwise respond 403.
- On trigger: start capture flow in a short-lived worker and respond quickly 202 Accepted if capture started, or 503 if busy.
- Provide an option for synchronous mode where the mobile app waits for confirmation of receipt and starts long-poll in cloud; prefer async start and cloud long-poll for the result.

5) Capture flow
- Sequence:
  1. Power on camera & required LEDs via `power.py` (GPIO) or enable camera device.
  2. Warm-up camera (100-300ms as needed), set deterministic camera settings (ISO, exposure, white balance locked), capture a high-resolution image (but keep size reasonable for bandwidth, e.g., 1024x1024), and store to temp path.
  3. Run minimal local validation (file size / basic histogram) but DO NOT run ML model on Pi in new workflow — all heavy processing occurs in backend.
  4. AES-256-CBC encrypt image bytes (prepend IV) using `crypto.py` and metadata (capture_timestamp, sync_timestamp). Build `GloveUploadMetadata` JSON following backend schema.
  5. Call `uploader.upload(scan_id, metadata, encrypted_image_bytes)`.
  6. On successful upload (HTTP 200), mark local scan as completed and signal mobile app via BLE notify or return success in subsequent local HTTP polling.
  7. Immediately power off camera & LEDs to save power.

Implementation notes for camera capture
- Use Picamera2 if available. For Pi 3 older setups, fallback to `raspistill` subprocess call.
- Ensure deterministic capture by setting explicit exposure/gain/whitebalance values and disabling auto-adjust.

6) Encryption & upload specifics
- Implement AES-256-CBC with PKCS7 padding exactly like backend `decrypt_image_payload` expects: IV (16 bytes) + ciphertext. Use `cryptography.hazmat.primitives.ciphers`.
- Build `GloveUploadMetadata` JSON fields required by backend (owner_id, patient_id, capture_timestamp, sync_timestamp, is_pregnant, etc.) and send as `metadata` form field. Follow `GloveUploadMetadata` schema in backend `app/schemas/scan.py`.
- Include header `X-Glove-Key: <glove_api_key>` and set `Content-Type` multipart/form-data with `image` file field.
- On failure (network/5xx), persist encrypted file and metadata to cache with retry/backoff worker.

7) Caching & retry worker
- Implement `cache.py` to hold a queue directory `/var/lib/smart_glove/queue/` with atomic write using temporary filenames and fsync. Each queue item includes `metadata.json` and `image.enc`.
- Background worker attempts upload with exponential backoff and jitter; on success remove queue item.
- If multiple items queued, upload oldest-first; throttle to avoid saturating limited uplink.

8) Power management
- Control camera/LEDs using a hardware-controlled MOSFET or Pi GPIO pins.
- Ensure camera power pins are toggled only when needed. After upload, fully disable camera and high-draw LEDs to preserve battery.

9) Security
- Store `glove_api_key` and `owner_id` in `/etc/smart_glove/config.json` with owner `root`, mode `600`.
- Use TLS for backend endpoint (verify server cert). Use certificate pinning if feasible.
- Ensure AES key used to encrypt images is stored securely on Pi (prefer deriving from `glove_api_key` + device secret using HKDF) instead of storing raw AES key.
- Rotate `glove_api_key` support: backend provides `rotate` endpoint; mobile app must reprovision the Pi with new key.

10) Observability & telemetry
- Structured logs (JSON) on stdout for `journalctl` ingestion.
- Expose `/health` and `/status` endpoints. Provide a `last_upload` timestamp and queue depth.
- Optionally integrate lightweight metrics exporter (Prometheus node exporter or custom `/metrics`).

11) Testing
- Unit tests for encryption (`crypto.py`) to ensure compatibility with backend decrypt function.
- Integration test on a test Pi: simulate `POST /trigger`, verify encrypted upload arrives at backend and session completes through long-poll.
- Hardware tests for power toggling to validate camera/LED power sequence.

12) Deployment & Ops
- Packaging: create a `wheel` or installable system package, or a simple `install.sh` that:
  - Creates system user `smartglove`.
  - Writes config to `/etc/smart_glove`.
  - Installs Python deps into a virtualenv (`/opt/smart_glove/venv`).
  - Installs service unit `/etc/systemd/system/smart_glove.service` that runs `/opt/smart_glove/venv/bin/python -m edge_firmware.main`.
- Systemd unit sample (template):

  [Unit]
  Description=Smart Glove Edge Firmware
  After=network-online.target
  Wants=network-online.target

  [Service]
  User=smartglove
  Group=smartglove
  WorkingDirectory=/opt/smart_glove
  Environment=PYTHONPATH=/opt/smart_glove
  ExecStart=/opt/smart_glove/venv/bin/python -m edge_firmware.main
  Restart=on-failure
  RestartSec=5

  [Install]
  WantedBy=multi-user.target

- Provide an `upgrade.sh` script to update code, run database migrations (if any), and restart service.

13) CI / Release
- Build pipeline (GitHub Actions): run lint, unit tests, build wheel, and produce an artifact.
- Integration pipeline: provision a test Pi image, deploy artifact, run an end-to-end test that calls `POST /trigger` and asserts backend receives upload.

14) Backward compatibility & fallback
- Keep an option for legacy behavior where a small model runs on Pi if network/cloud processing is unavailable — but disable by default and controlled by a config flag.
- Provide an offline AP mode for provisioning and debugging.

15) Timeline & estimates (rough)
- Phase 1 (3 days): Packaging, `server.py`, `capture.py`, `crypto.py`, and uploader happy-path (no BLE). Validate encryption + upload to backend dev/staging.
- Phase 2 (3 days): Caching, retry worker, power control, and mDNS advertising.
- Phase 3 (2 days): BLE provisioning implementation and secure storage of credentials.
- Phase 4 (2 days): Tests, systemd packaging, docs, and production smoke tests.

Files to create/update (suggested)
- Add: `edge-firmware/edge_firmware/__init__.py`
- Add: `edge-firmware/edge_firmware/main.py`
- Add: `edge-firmware/edge_firmware/server.py`
- Add: `edge-firmware/edge_firmware/capture.py` (productionized)
- Add: `edge-firmware/edge_firmware/crypto.py`
- Add: `edge-firmware/edge_firmware/uploader.py`
- Add: `edge-firmware/edge_firmware/cache.py`
- Add: `edge-firmware/edge_firmware/power.py`
- Add: `edge-firmware/edge_firmware/provisioning.py`
- Update or remove: existing scripts in `edge-firmware/smart-glove-hemoglobin/*` (keep as simulators/tests)

Quick start commands (developer Pi)

```bash
# On Pi: create user and venv
sudo useradd --system --create-home --shell /bin/bash smartglove
sudo mkdir -p /opt/smart_glove
sudo chown smartglove:smartglove /opt/smart_glove
sudo -u smartglove python3 -m venv /opt/smart_glove/venv
sudo -u smartglove /opt/smart_glove/venv/bin/pip install -r /opt/smart_glove/requirements.txt

# Enable service
sudo cp deploy/smart_glove.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now smart_glove.service
```

Acceptance criteria
- Pi can be provisioned via mobile app and advertises `glove-<OWNERID>.local`.
- Mobile app can POST `/trigger` to Pi and receive immediate acknowledgement.
- Pi captures an image, encrypts it in AES-256-CBC IV+ct format, and uploads to backend with `X-Glove-Key` and `metadata` as required.
- Backend completes session and returns result to mobile app long-poll; Pi powers off camera after upload.

Questions & decisions for the team
- BLE provisioning library choice for Pi 3 (BlueZ/dbus vs alternative). If BLE GATT server is brittle, fallback to temporary AP provisioning or QR-code scan of Wi‑Fi credentials.
- Hardware wiring for camera/LED power control and safe GPIO levels.
- Whether the AES key is derived from `glove_api_key` or supplied separately.

If you'd like, I can now scaffold the `edge_firmware` package (create the module files and a systemd unit template) and implement the `crypto.py` + `server.py` upload happy-path for testing against your backend staging instance. Which step should I implement first?
