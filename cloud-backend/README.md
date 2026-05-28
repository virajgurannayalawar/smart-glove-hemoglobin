## Smart Glove – Cloud Backend (FastAPI)

### Requirements
- Python 3.10+ recommended
- MongoDB (local or Atlas)

### Setup (Windows PowerShell)

Create and activate a venv:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env` from the example:

```bash
copy .env.example .env
```

### Run

```bash
uvicorn app.main:app --reload
```

Open:
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health root: `http://127.0.0.1:8000/`

### Testing

#### Unit Tests
Run pytest for unit tests:

```bash
pytest tests/
```

#### End-to-End Tests
Run the comprehensive end-to-end test suite that validates the complete workflow:

```bash
python test_e2e.py
```

The e2e test covers:
- **Auth**: register, login, profile retrieval
- **Patient CRUD**: create, list, get, delete patients
- **Scan workflow**: session creation, long-poll result retrieval, glove upload simulation
- **Report generation**: create, get, list reports
- **History**: retrieve scan history

**Prerequisites for e2e tests:**
- Backend server running on `http://localhost:8000`
- MongoDB connected and accessible
- Cloudinary configured (for image/PDF storage)
- Model service available (for hemoglobin prediction)

**Note**: The e2e test creates a temporary user and patient for testing, then cleans up by deleting the test patient.

#### Integration Tests
Test MongoDB and Cloudinary connectivity:

```bash
python test_integrations.py
```

### Notes
- The API base path is `API_V1_STR` (default `/api/v1`).
- Mongo indexes are created at startup in `app/services/db.py`.
