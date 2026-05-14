# Smart Glove Cloud Backend - Walkthrough

The backend infrastructure for the Smart Glove Hemoglobin project is now fully constructed! All execution phases are complete. Here is a summary of the systems we built.

## 1. Database & Strict Compliance
- **Motor (Async MongoDB)**: High-performance async database integration.
- **Isolated PII**: The `users` collection exclusively handles Names and Emails. The `history` collection is strictly clinical data mapped only by `patient_id`.
- **Strict Indexing**: A compound index was created on `("patient_id", 1), ("true_timestamp", -1)` to ensure lighting-fast chart queries for the mobile app.

## 2. Burst-Tolerant Uploads & Relative Offset Logic
- **Multipart Data**: The Raspberry Pi endpoint (`POST /upload`) flawlessly handles mixed `multipart/form-data` to prevent Base64 string bloat (saving the Pi from out-of-memory crashes).
- **The Offset Algorithm**: The backend calculates the `true_timestamp` dynamically by subtracting the Pi's time-since-capture from the current server time. This completely bypasses the hardware limitation of the Pi resetting its clock to 1970 when offline.
- **Burst Limits**: The `slowapi` rate limiter allows an edge device to burst up to 100 requests per minute to dump offline caches smoothly.

## 3. Storage & Encryption (Cloudinary Migration)
- **Memory Decryption**: The backend intercepts AES-encrypted payloads, decrypting them strictly in memory via the `cryptography` module.
- **Cloudinary Swap**: Replaced AWS S3 with Cloudinary. Raw images are uploaded as "authenticated" (private) assets, completely preventing public access.
- **Signed URLs**: The `GET /history` endpoint generates short-lived, cryptographically signed Cloudinary URLs allowing the mobile app to securely view the images without needing hardcoded keys.

## 4. Testing
- We created robust Pytest suites in the `tests/` directory covering the multipart payload parsing, offset logic, and Cloudinary signed URL mocking logic.

> [!TIP]
> **To run your tests:**
> Make sure your virtual environment is activated, then run:
> ```powershell
> pytest tests/
> ```
> **To start the server:**
> ```powershell
> uvicorn app.main:app --reload
> ```
