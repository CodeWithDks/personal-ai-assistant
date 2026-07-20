from fastapi import FastAPI
from .database.database import engine
from .database import models
from app.routes.task_routes import router as task_router
from app.routes.note_routes import router as note_router

app = FastAPI()

app.include_router(task_router)
app.include_router(note_router)
models.Base.metadata.create_all(bind=engine)

