from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.services.db import connect_to_mongo, close_mongo_connection
from app.api.routes import auth, upload, history
from app.utils.rate_limit import limiter

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
    allow_origins=["*"], # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiter setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(upload.router, prefix=f"{settings.API_V1_STR}/upload", tags=["upload"])
app.include_router(history.router, prefix=f"{settings.API_V1_STR}/history", tags=["history"])

@app.get("/")
def root():
    return {"message": "Welcome to Smart Glove Hemoglobin API"}
