from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.task_schema import TaskCreate, TaskResponse, TaskUpdate
from app.services.task_service import create_task, get_tasks, update_task, delete_task

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
)


@router.post("/", response_model=TaskResponse)
def add_task(task: TaskCreate, db: Session = Depends(get_db)):
    return create_task(db, task)


@router.get("/", response_model=list[TaskResponse])
def show_tasks(db: Session = Depends(get_db)):
    return get_tasks(db)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task_route(
    task_id: int,
    task: TaskUpdate,
    db: Session = Depends(get_db)
):
    return update_task(db, task_id, task)

@router.delete('/{task_id}')
def delete_task_route(task_id: int, db: Session = Depends(get_db)):
    
    return delete_task(db, task_id)