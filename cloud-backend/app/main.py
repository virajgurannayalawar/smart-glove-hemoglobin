from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.services.db import connect_to_mongo, close_mongo_connection
from app.api.middleware import request_id_middleware
from app.api.routes import auth, upload, history, profile
from app.api.routes import patients
from app.api.routes import scan
from app.api.routes import devices
from app.api.routes import reports
from app.utils.rate_limit import limiter
import logging
from app.services.db import db as db_state

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=False,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Rate limiter setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Basic logging level
logging.getLogger().setLevel(settings.LOG_LEVEL)

# Request ID middleware
app.middleware("http")(request_id_middleware)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(profile.router, prefix=f"{settings.API_V1_STR}/profile", tags=["profile"])
app.include_router(upload.router, prefix=f"{settings.API_V1_STR}/upload", tags=["upload"])
app.include_router(history.router, prefix=f"{settings.API_V1_STR}/history", tags=["history"])
app.include_router(patients.router, prefix=f"{settings.API_V1_STR}/patients", tags=["patients"])
app.include_router(scan.router, prefix=f"{settings.API_V1_STR}/scan", tags=["scan"])
app.include_router(devices.router, prefix=f"{settings.API_V1_STR}/devices", tags=["devices"])
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["reports"])

@app.get("/")
def root():
    return {"message": "Welcome to Smart Glove Hemoglobin API"}


@app.get("/health")
async def health():
    """

    Basic health endpoint for container orchestration.
    Checks that Mongo is reachable.
    
    """
    try:
        if not db_state.client:
            return {"status": "degraded", "mongo": "disconnected"}
        await db_state.client.admin.command("ping")
        return {"status": "ok", "mongo": "ok"}
    except Exception:
        return {"status": "degraded", "mongo": "error"}
