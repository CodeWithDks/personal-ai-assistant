# backend/app/main.py

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# 1. Grab the absolute directory path of main.py
current_file_dir = Path(__file__).resolve().parent  # points to backend/app

# 2. Step up ONE level to get into the backend/ folder
backend_dir = current_file_dir.parent  # points to backend/

# 3. Target the .env inside the backend/ folder
env_path = os.path.join(backend_dir, ".env")

# Force-load the file directly from this path location
load_dotenv(dotenv_path=env_path)

# Configure logging so logs show up cleanly in stdout / Render logs
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.app.database.database import engine
from backend.app.database import models  # Holds your actual database tables
from backend.app.core.rate_limit import limiter
from backend.app.routes.auth import router as auth_router
from backend.app.routes.chat_routes import router as chat_router
from backend.app.routes.note_routes import router as note_router
from backend.app.routes.task_routes import router as task_router

app = FastAPI(title="Personal AI Assistant")

# Rate limiter setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


# CORS middleware (Must be below SlowAPIMiddleware so 429 errors carry CORS headers)

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:8080,https://personal-assistant-09.lovable.app"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=os.getenv(
        "CORS_ORIGIN_REGEX",
        r"https://.*\.(lovable\.app|lovableproject\.com)"
    ),
    allow_credentials=False,  # Using Authorization Bearer tokens, not cookies
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Register your modular routing blueprints
app.include_router(task_router)
app.include_router(note_router)
app.include_router(auth_router)
app.include_router(chat_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.on_event("startup")
def startup_event():
    """
    Executes tasks safely on system launch.
    Alembic handles migrations in production (Postgres), so create_all 
    runs only for local SQLite fallback testing.
    """
    if str(engine.url).startswith("sqlite"):
        models.Base.metadata.create_all(bind=engine)
        logger.info("Local SQLite database infrastructure synchronized.")
    else:
        logger.info("Connected to remote production database (Alembic manages migrations).")