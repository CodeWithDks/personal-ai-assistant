import os
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



from fastapi import FastAPI
from app.database.database import engine, reset_db_development_only
from app.database import models  # Holds your actual database tables
from app.routes.task_routes import router as task_router
from app.routes.note_routes import router as note_router
from app.routes.auth import router as auth_router
from app.routes.chat_routes import router as chat_router
from fastapi.middleware.cors import CORSMiddleware

from fastapi import Request
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.core.rate_limit import limiter


app = FastAPI(title="Personal AI Assistant")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Register your modular routing blueprints
app.include_router(task_router)
app.include_router(note_router)
app.include_router(auth_router)
app.include_router(chat_router)



app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.on_event("startup")
def startup_event():
    """
    Executes tasks safely on system launch.
    Ensures structural integrity without erasing production data files.
    """
    # 1. Safely create any missing database tables (does not alter or erase existing data)
    models.Base.metadata.create_all(bind=engine)
    print("Database infrastructure synchronized successfully.")