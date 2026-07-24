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
from backend.app.database.database import engine
from backend.app.database import models  # Holds your actual database tables
from backend.app.routes.task_routes import router as task_router
from backend.app.routes.note_routes import router as note_router
from backend.app.routes.auth import router as auth_router
from backend.app.routes.chat_routes import router as chat_router


app = FastAPI(title="Personal AI Assistant")

# Register your modular routing blueprints
app.include_router(task_router)
app.include_router(note_router)
app.include_router(auth_router)
app.include_router(chat_router)



@app.on_event("startup")
def startup_event():
    """
    Executes tasks safely on system launch.
    Ensures structural integrity without erasing production data files.
    """
    # 1. Safely create any missing database tables (does not alter or erase existing data)
    models.Base.metadata.create_all(bind=engine)
    print("Database infrastructure synchronized successfully.")