# Frontend Implementation Plan — Smart Glove (Mobile)

**Overview**

This document describes a concrete, step-by-step implementation plan for the mobile (Flutter) frontend engineer to fully support the modified workflow (BLE provisioning, multi-patient scan sessions, local trigger + cloud scoring, and long-polling result delivery).

**Assumptions**
- The backend supports the endpoints used in this plan (see `cloud-backend/app/api/routes/scan.py`).
- The Flutter app uses Riverpod for state, `flutter_blue_plus` for BLE, and `dio` for HTTP (see `pubspec.yaml`).
- Raspberry Pi (glove) will accept BLE provisioning and expose a local HTTP endpoint `http://glove-OWNERID.local` reachable on the same Wi‑Fi network.

**Reference files (read first)**
- App entry: [mobile-app/lib/main.dart](mobile-app/lib/main.dart#L1)
- BLE service: [mobile-app/lib/core/services/bluetooth_service.dart](mobile-app/lib/core/services/bluetooth_service.dart#L1)
- Auth provider: [mobile-app/lib/presentation/providers/auth_provider.dart](mobile-app/lib/presentation/providers/auth_provider.dart#L1)
- History provider: [mobile-app/lib/presentation/providers/history_provider.dart](mobile-app/lib/presentation/providers/history_provider.dart#L1)
- Dashboard screen: [mobile-app/lib/presentation/screens/dashboard_screen.dart](mobile-app/lib/presentation/screens/dashboard_screen.dart#L1)
- Backend scan routes: [cloud-backend/app/api/routes/scan.py](cloud-backend/app/api/routes/scan.py#L1)
- Scan session storage & long-poll: [cloud-backend/app/services/scan_sessions.py](cloud-backend/app/services/scan_sessions.py#L1)

**Goals**
- Enable one owner (logged-in user) to scan multiple patients per login.
- Implement BLE provisioning sequence (owner_id, glove API key, Wi‑Fi credentials) in the app UI.
- Implement scan session lifecycle: create session → trigger glove (local) → long-poll result → display + persist locally.
- UX: clear progress states, error messages, retry/backoff, and test hooks for integration.

Implementation details

1) BLE Provisioning & Connect flow
- Add UI: `Connect Glove` flow accessible from `Dashboard` or `Profile` screens.
- Steps (frontend):
  - Fetch the owner id and glove key from backend: call `GET /api/scan/owner-id` and `GET /api/scan/glove-key` (protected via JWT). Use `dio` and token from `auth_provider`.
  - Start BLE scanning using the existing `BluetoothService` (`flutter_blue_plus`) and present a device list if multiple are found.
  - Once the Pi is selected, send a provisioning payload over BLE (characteristic write): JSON {
    - `owner_id`, `glove_api_key`, `wifi_ssid`, `wifi_password`
    }
  - Confirm provisioning success via characteristic response; store a local flag `glove_provisioned: true` (in `flutter_secure_storage` or `hive`).

Notes:
- Use `BluetoothConstants.serviceUuid` and characteristic UUID already used in `BluetoothService` (see [bluetooth_service.dart](mobile-app/lib/core/services/bluetooth_service.dart#L1)).
- Provide an option to re-provision / rotate key (calls backend `POST /api/scan/glove-key/rotate`), and show instructions to re-provision the glove.

2) Patient management (multi-patient support)
- UI: `Add Patient` screen and `Patient List` accessible from `Profile` or a top-right menu.
- Use existing `PatientCreate` shape on backend; create local forms with validation (name, age, gender, contact, email, notes).
- On adding a patient, call backend `POST /api/patients` and refresh `History`/patient list.
- Make `patient_id` available to scan actions.

3) Scan session lifecycle (core)
- Flow (frontend):
  1. User picks a patient and taps `Check`.
  2. App creates a cloud scan session: `POST /api/scan/sessions` with `patient_id` and `is_pregnant`.
  3. Backend returns `scan_id`.
  4. In parallel, app triggers the local glove HTTP endpoint to wake & request the scan: POST `http://glove-<owner_id>.local/trigger` (or `http://<ip>:port/trigger`) with JSON { scan_id, owner_id, patient_id }.
     - If local trigger fails (device not reachable), optionally send a cloud action (if Pi supports polling cloud) or show an actionable error.
  5. Start long-poll: `GET /api/scan/sessions/{scan_id}/result?timeout_seconds=60` and hold the request until result or timeout.
  6. Display progress UI while waiting. On success, show results; on timeout, show `pending` state and button to retry `GET` or re-trigger device.

Implementation notes for long-poll:
- Use `dio` with a dedicated `CancelToken` to manage request lifecycle and allow cancellation if user navigates away.
- Set `connectTimeout` and `receiveTimeout` appropriately, but rely on backend `timeout_seconds` query to control server-side wait.
- Implement exponential backoff for retries (e.g., 2s → 4s → 8s) but cap total wait (e.g., 2 attempts with 60s each).

4) Handling result payload & UI
- The backend returns: `hemoglobin_level`, `is_anemic`, `status_text`, `reading_id`, `true_timestamp`, `image_url`.
- Map into `ScanResult` entity and persist locally in `Hive` for offline history and faster UI.
- Update `ResultCard` (see [result_card.dart](mobile-app/lib/presentation/widgets/result_card.dart#L1)) to show:
  - Hb value with precision
  - `Anemic` / `Normal` badge (color-coded)
  - Timestamp (humanized)
  - Link to open signed image URL or download PDF report via `POST /api/reports` / `GET /api/reports/{id}` (see backend reports route).

5) BLE + Local Trigger details
- When sending provisioning or trigger commands, use write-with-response if available so the Pi can confirm.
- Show strict UX: `Scanning`, `Connecting`, `Provisioning`, `Provisioned`, `Ready`.
- When making the local HTTP trigger, try both the mDNS hostname `http://glove-<OWNERID>.local` and a cached IP address discovered via BLE advertisement (the Pi may advertise its IP in manufacturer data).

6) Security
- All backend API calls require the JWT — keep token in `flutter_secure_storage` and attach via `Authorization: Bearer <token>` header.
- Do not persist `wifi_password` in long term storage (only keep in memory while provisioning).
- For provisioning, only send `glove_api_key` during provisioning step; the Pi should store it and use it for subsequent uploads.

7) Offline & Error handling
- If backend unreachable during session creation, queue the scan creation and retry automatically when network restored.
- If long-poll times out, show a `Retry result` button that re-issues the `GET /sessions/{scan_id}/result`.
- Provide clear messages for: provisioning failure, BLE permission denied, local trigger unreachable, backend 5xx.

8) Tests & QA
- Unit tests for providers: `auth_provider`, `history_provider`, and the new `scan_session_provider`.
- Widget tests for `ResultCard`, `DashboardScreen` and `Connect Glove` modal (existing `test/` files show patterns).
- Create an integration test that:
  1. Mocks the backend session creation.
 2. Mocks long-poll returning a completed result.
  3. Verifies UI transitions from scanning → result.

9) Tasks (recommended order, with estimates)
- Task A (1d): Add `Connect Glove` UI and provisioning flow (BLE write + backend `GET /api/scan/owner-id` + `GET /api/scan/glove-key`).
- Task B (2d): Implement `Patient` management UI and integrate `POST /api/patients` and `GET /api/patients`.
- Task C (2d): Implement scan session lifecycle: `POST /api/scan/sessions`, local trigger HTTP call, and start long-polling `GET /api/scan/sessions/{scan_id}/result` with cancellation/timeout handling.
- Task D (1d): Persist readings locally and update `History` UI.
- Task E (1d): Error handling, retries, and UX polish.
- Task F (1d): Tests & integration tests.

10) Acceptance criteria
- Owner can provision a glove via BLE and see `Ready` state in-app.
- Owner can add/list/delete multiple patients.
- Owner can start a scan for any patient; app creates a session and successfully receives final result within reasonable time in normal network/device conditions.
- Results are persisted locally and displayed in `History` and `Result` views.
- App shows clear errors and retry options for all failure modes.

**Files to update (suggested)**
- Add screens/components: `mobile-app/lib/presentation/screens/connect_glove_screen.dart` (new), `mobile-app/lib/presentation/screens/patients_screen.dart` (new/create), `mobile-app/lib/presentation/screens/patient_form.dart` (new).
- Modify: [mobile-app/lib/presentation/screens/dashboard_screen.dart](mobile-app/lib/presentation/screens/dashboard_screen.dart#L1), [mobile-app/lib/presentation/widgets/result_card.dart](mobile-app/lib/presentation/widgets/result_card.dart#L1), and `history` provider to persist the new readings.
- Add provider: `mobile-app/lib/presentation/providers/scan_session_provider.dart` (new) — short-lived state for active `scan_id` and long-poll management.
- Update services: `mobile-app/lib/core/services/http_service.dart` (if exists) or centralize `dio` client with JWT handling and backoff logic.

**Next steps I can take**
- Generate the skeleton files (providers, screens, and updated `ResultCard`) and a runnable smoke test for the long-poll flow, or
- Implement the `scan_session_provider` and long-polling helper with a small demo in `DashboardScreen`.

---

If you want, I can now scaffold the new provider and screens, and add integration tests and example flows. Which of the next steps should I do first?
